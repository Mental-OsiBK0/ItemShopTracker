import os
import sys
import psycopg
from dotenv import load_dotenv

load_dotenv()

RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
GRAY = "\033[90m"
RESET = "\033[0m"

def connect():
    try:
        return psycopg.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            autocommit=True,
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

    expires_at = f"{expires_date} 03:00+03:00"

    try:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO products (name, price, expires_at) VALUES (%s, %s, %s) RETURNING id;",
                    (name, price, expires_at),
                )
                new_id = cur.fetchone()[0]
        print(f"Product added with id {new_id}")
    except psycopg.DataError as e:
        print(f"Invalid value: {e}")


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
    conn = connect()

    print("Enter products as: Name, Price, YYYY-MM-DD")
    print("Commands: ListProducts, DeleteProduct <id>, Exit")

    with conn:
        while True:
            user_input = input("> ").strip()

            if user_input.lower() == "exit":
                break
            elif user_input.lower() == "listproducts":
                list_products(conn)
            elif user_input == "":
                continue
            elif user_input.lower().startswith("deleteproduct"):
                try:
                    product_id = int(user_input.split()[1])           
                except ValueError:
                    print("Please provide a valid product ID.")
                    continue
                except IndexError:
                    print("Please provide a product ID to delete.")
                    continue
                print(f"The product you want to delete: {product_id}")
            else:
                add_product(conn, user_input)

if __name__ == "__main__":
    main()