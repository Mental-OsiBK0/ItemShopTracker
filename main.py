import os
import sys
from decimal import Decimal, InvalidOperation

import psycopg
from dotenv import load_dotenv

load_dotenv()

RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
GRAY = "\033[90m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

MAX_ID = 2_147_483_647
TIMEZONE = "Europe/Istanbul"
SHOP_RESET_TIME = "03:00+03:00"
REQUIRED_ENV_VARS = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]


def print_help():
    print(f"""
{BOLD}{CYAN}╔══════════════════════════════════════════════╗
║               ItemShopTracker                ║
╚══════════════════════════════════════════════╝{RESET}

{BOLD}Add a product:{RESET}
  Name, Price, YYYY-MM-DD
  {GRAY}e.g. Black Knight, 200, 2026-11-05{RESET}

{BOLD}Commands:{RESET}
  {CYAN}ListProducts{RESET}         Show all products
  {CYAN}DeleteProduct <id>{RESET}   Delete a product by id
  {CYAN}Help{RESET}                 Show this screen
  {CYAN}Exit{RESET}                 Quit the program

{BOLD}Colors:{RESET}
  {RED}■{RESET} Less than 1 day    {YELLOW}■{RESET} Less than 2 days
  {GREEN}■{RESET} More than 2 days   {GRAY}■{RESET} Expired
""")


def check_env():
    missing = [name for name in REQUIRED_ENV_VARS if not os.getenv(name)]
    if missing:
        print(f"Missing settings in .env: {', '.join(missing)}")
        sys.exit(1)


def connect():
    try:
        return psycopg.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            autocommit=True,
            sslmode=os.getenv("DB_SSLMODE", "require"),
            options=f"-c timezone={TIMEZONE}",
        )
    except psycopg.OperationalError as e:
        print(f"Could not connect to the database: {e}")
        sys.exit(1)


def add_product(conn, user_input):
    try:
        name, price, expires_date = [part.strip() for part in user_input.split(",")]
    except ValueError:
        print("Please enter exactly 3 values separated by commas.")
        return

    if not name:
        print("Product name cannot be empty.")
        return

    try:
        price_value = Decimal(price)
    except InvalidOperation:
        print("Price must be a number.")
        return

    if not price_value.is_finite() or price_value < 0:
        print("Price must be a positive number.")
        return

    expires_at = f"{expires_date} {SHOP_RESET_TIME}"

    try:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO products (name, price, expires_at) VALUES (%s, %s, %s) RETURNING id;",
                    (name, price_value, expires_at),
                )
                new_id = cur.fetchone()[0]
        print(f"Product added with id {new_id}")
    except psycopg.DataError as e:
        print(f"Invalid value: {e}")


def delete_product(conn, user_input):
    parts = user_input.split()

    if len(parts) != 2:
        print("Usage: DeleteProduct <id>")
        return

    try:
        product_id = int(parts[1])
    except ValueError:
        print("Please provide a valid product ID.")
        return

    if product_id < 1 or product_id > MAX_ID:
        print("Please provide a valid product ID.")
        return

    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM products WHERE id = %s;",
                (product_id,),
            )
            deleted_count = cur.rowcount

    if deleted_count == 0:
        print(f"No product found with id {product_id}.")
    else:
        print(f"Product {product_id} deleted.")


def list_products(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, name, price, expires_at, expires_at - now() AS remaining
            FROM products
            ORDER BY expires_at;
            """
        )
        products = cur.fetchall()

    if not products:
        print("No products.")
        return

    for product_id, name, price, expires_at, remaining in products:
        seconds_left = remaining.total_seconds()

        if seconds_left <= 0:
            ago = -remaining
            print(f"{GRAY}[{product_id}] {name} | {price} TL | expired {ago.days}d {ago.seconds // 3600}h ago | {expires_at:%Y-%m-%d %H:%M}{RESET}")
            continue

        days_left = seconds_left / 86400

        if days_left <= 1:
            color = RED
        elif days_left <= 2:
            color = YELLOW
        else:
            color = GREEN

        print(f"{color}[{product_id}] {name} | {price} TL | {remaining.days}d {remaining.seconds // 3600}h left | {expires_at:%Y-%m-%d %H:%M}{RESET}")


def main():
    check_env()
    conn =  connect()
    print("Type 'Help' to see commands.")

    try:
        while True:
            user_input = input("> ").strip()

            if not user_input:
                continue

            command = user_input.split()[0].lower()

            if command == "exit":
                break
            elif command == "listproducts":
                list_products(conn)
            elif command == "help":
                print_help()
            elif command == "deleteproduct":
                delete_product(conn, user_input)
            else:
                add_product(conn, user_input)
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye!")
    except psycopg.OperationalError:
        print("Lost connection to the database. Please restart the program.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()