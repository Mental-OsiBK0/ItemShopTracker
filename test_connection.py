import getpass
import psycopg

password = getpass.getpass("PostgreSQL Password:  ")
print("Connecting to PostgreSQL...")