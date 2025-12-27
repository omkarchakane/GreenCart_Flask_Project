import sqlite3

con = sqlite3.connect("greencart.db")  
cur = con.cursor()

#! Insert admin user
cur.execute("INSERT INTO users(name,email,password,role,location) VALUES(?,?,?,?,?)",
            ("admin", "admin@gmail.com", "admin@123", "admin", "Pune"))
con.commit()

# Create wallet entry for admin
cur.execute("INSERT INTO wallet(user_id,balance) VALUES((SELECT id FROM users WHERE email=?),0)",
            ("admin@gmail.com",))
con.commit()

con.close()


