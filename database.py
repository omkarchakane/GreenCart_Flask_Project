import sqlite3 as sq

#! Function to connect database
def connect_db():
    con = sq.connect("greencart.db")
    con.row_factory = sq.Row               #? read rows like dictionary
    return con

#! Function to create tables
def create_tables():
    con = connect_db()
    cur = con.cursor()

    #todo Users Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT,
            role TEXT,
            location TEXT,
            status TEXT DEFAULT 'pending'
        );
    """)

    #todo Wallet Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS wallet(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            balance INTEGER DEFAULT 0
        );
    """)

    #todo Products Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_id INTEGER,
            name TEXT,
            qty INTEGER,
            price INTEGER,
            expiry_date TEXT,
            image TEXT,
            status TEXT DEFAULT 'pending'
        );
    """)

    #todo Orders Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            buyer_id INTEGER,
            product_id INTEGER,
            qty INTEGER,
            amount INTEGER,
            date TEXT,
            item_name TEXT
        );
    """)


    con.commit()
    con.close()
