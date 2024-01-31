import sqlite3
import json

class Database:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

    def create_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY,
                img BLOB NOT NULL,
                title TEXT NOT NULL,
                about TEXT NOT NULL,
                price INTEGER NOT NULL,
                quantity INTEGER DEFAULT 0  
            )
        """)
        self.conn.commit()

    def create_buyers_items_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS buyers_items (
                id INTEGER PRIMARY KEY,
                user_id TEXT NOT NULL,
                item_id TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def insert_item(self, img, title, about, price, isActive, category, type):
        self.cursor.execute("""
            INSERT INTO items (img, title, about, price, isActive, category, type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (img, title, about, price, isActive, category, type))
        self.conn.commit()

    def get_all_items(self):
        self.cursor.execute("SELECT * FROM items")
        items = self.cursor.fetchall()
        return items
    
    def get_all_buyers(self):
        self.cursor.execute("SELECT * FROM buyers")
        buyers = self.cursor.fetchall()
        return buyers


    def get_item_by_id(self, id):
        self.cursor.execute("SELECT * FROM items WHERE id=?", (id,))
        item = self.cursor.fetchone()
        return item

    def update_item(self, id, img, title, about, price):
        self.cursor.execute("""
            UPDATE items
            SET img=?, title=?, about=?, price=?
            WHERE id=?
        """, (img, title, about, price, id))
        self.conn.commit()

    def delete_item(self, id):
        self.cursor.execute("DELETE FROM items WHERE id=?", (id,))
        self.conn.commit()

    def delete_buyers(self, id):
        self.cursor.execute("DELETE FROM buyers WHERE user_id=?", (id,))
        self.conn.commit()

    def delete_item_buyers(self, id):
        self.cursor.execute("DELETE FROM buyers_items WHERE item_id=?", (id,))
        self.conn.commit()

    def close(self):
        self.conn.close()

    def delete_table(self, table_name):
        self.cursor.execute("DROP TABLE IF EXISTS {}".format(table_name))  # Corrected query
        self.conn.commit()

    def create_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                surname TEXT NOT NULL,
                email TEXT NOT NULL,
                password TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def insert_user(self, name, surname, email, password, users_level):
        self.cursor.execute("""
            INSERT INTO users (name, surname, email, password, users_level)
            VALUES (?, ?, ?, ?, ?)
        """, (name, surname, email, password, users_level))
        self.conn.commit()

    def get_items_by_title_like(self, query):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM items WHERE title LIKE ?", ['%' + query + '%'])
        items = cursor.fetchall()
        return items

    def check_email(self, email):
        sql = """
        SELECT COUNT(*)
        FROM users
        WHERE email = ?
        """
        self.cursor.execute(sql, (email,))
        count = self.cursor.fetchone()[0]
        return count > 0
    
    def check_user_credentials(self, email, password):
        sql = """
            SELECT *
            FROM users
            WHERE email = ? AND password = ?
        """
        self.cursor.execute(sql, (email, password))
        user = self.cursor.fetchone()
        return user

    def get_cart_items(self, user_id):
        self.cursor.execute("""
            SELECT items.id, items.img, items.title, items.about, items.price, carts.items_count, carts.id, items.isActive
            FROM carts
            JOIN items ON carts.item_id = items.id
            WHERE carts.user_id = ?
        """, (user_id,))
        return self.cursor.fetchall()
    
    def get_buyers_items(self, user_id):
        self.cursor.execute("""
            SELECT items.img, buyers_items.status
            FROM buyers_items
            JOIN items ON buyers_items.item_id = items.id
            WHERE buyers_items.user_id = ?
        """, (user_id,))
        return self.cursor.fetchall()
    
    def get_buyers_all_items(self):
        self.cursor.execute("""
            SELECT items.img, buyers_items.user_id, buyers_items.item_id, buyers_items.status 
            FROM buyers_items
            JOIN items ON buyers_items.item_id = items.id
        """)
        buyers_all = self.cursor.fetchall()
        return buyers_all
    
    def add_item_category(self):
        self.cursor.execute("""
            ALTER TABLE buyers_items ADD status integer DEFAULT 1;
        """)  
        self.conn.commit()

    def update_carts_count(self, id, item_count):
        self.cursor.execute("""
            UPDATE carts
            SET items_count = ?
            WHERE id = ?; 
        """, (item_count, id))
        self.conn.commit()

    def execute_query(self, query, params):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def get_items_by_category_and_type(self, category, type, order_by=None):
        query = """
            SELECT * FROM items
            WHERE category = ? AND type = ?
        """
        if order_by:
            query += f" ORDER BY {order_by}"  
        params = (category, type)

        return self.execute_query(query, params)

    def get_items_by_type(self, type, order_by=None):
        query = """
            SELECT * FROM items
            WHERE type = ?
        """
        if order_by:
            query += f" ORDER BY {order_by}"  
        params = (type,)

        cursor = self.conn.cursor()
        cursor.execute(query, params)
        items = cursor.fetchall()
        return items

    def insert_buyer(self, name, phone, email, comment, total_price, user_id):
        cursor = self.conn.cursor()
        sql = """INSERT INTO buyers (name, phone, email, comment, total_price, user_id)
                VALUES (?, ?, ?, ?, ?, ?)"""
        cursor.execute(sql, (name, phone, email, comment, total_price, user_id))
        self.conn.commit()
        return cursor.lastrowid 
    
    def insert_buyer_items(self, user_id, item_id):
        cursor = self.conn.cursor()
        sql = """INSERT INTO buyers_items (user_id, item_id)
                VALUES (?, ?)"""
        cursor.execute(sql, (user_id, item_id))
        self.conn.commit()
        return cursor.lastrowid

    def remove_from_cart(self, user_id):
        cursor = self.conn.cursor()
        sql = """DELETE FROM carts WHERE user_id = ?"""
        cursor.execute(sql, (user_id,))
        self.conn.commit()

    def get_cart_items_for_user(self, user_id):
        self.cursor.execute("""
            SELECT item_id
            FROM buyers_items
            WHERE buyers_items.user_id = ?
        """, (user_id,))
        return self.cursor.fetchall()
    
    def delete_cart_items_column(self):
        self.cursor.execute("""
            ALTER TABLE buyers
            DROP COLUMN order_id;
        """)

    def get_all_items_id_cart(self, user_id):
        self.cursor.execute("""
            SELECT item_id
            FROM carts
            WHERE user_id = ?
        """, (user_id,))
        return tuple(item_id[0] for item_id in self.cursor.fetchall())
    




db = Database("shop.db")



#img = open("4DRC.png", "rb").read()
#db.insert_item(img, title, about, prise)