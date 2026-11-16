-- ItemShopTracker database schema (PostgreSQL 18)
-- Mirrors the live database: table, constraints and least-privilege grants.

CREATE TABLE products (
    id         integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name       text NOT NULL CHECK (name <> ''),
    price      numeric(10,2) NOT NULL CHECK (price >= 0),
    expires_at timestamptz NOT NULL
);

-- Each user has their own login role. Passwords are NOT stored in this file:
-- create the roles with CREATE ROLE ... LOGIN; then set the password in psql
-- with \password <role_name> so it never appears in a file or in the shell history.
--
--   CREATE ROLE itemshop_app LOGIN;
--   CREATE ROLE itemshop_brother LOGIN;

-- Least privilege: SELECT, INSERT and DELETE only. No UPDATE, no TRUNCATE.
-- Dropping or altering the table is only possible for its owner.
GRANT SELECT, INSERT, DELETE ON products TO itemshop_app;
GRANT SELECT, INSERT, DELETE ON products TO itemshop_brother;
