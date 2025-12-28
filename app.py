from flask import *
import os
from werkzeug.utils import secure_filename
from datetime import datetime,date
from database import create_tables,connect_db  #? use module concepts
app=Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join("static", "uploads")#? Path to save files

app.secret_key = "my_secret_omkar_123" 
create_tables() 

#? Deployement
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/')  #? connect URL with function
def home():
    return render_template("index.html")

@app.route('/register',methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']  #? Take value enter by user
        email = request.form['email']
        password = request.form['password']
        location = request.form['location']
        role = request.form['role']

        con = connect_db()
        cur = con.cursor()

        #! Insert user into DB
        cur.execute("INSERT INTO users(name,email,password,role,location) VALUES(?,?,?,?,?)",(name,email,password,role,location))
        con.commit()

        #! Create wallet
        cur.execute("INSERT INTO wallet(user_id,balance) VALUES ((SELECT id FROM users WHERE email=?),0)",(email,))
        con.commit()
        con.close()

        return redirect(url_for("login"))
    return render_template("register.html")

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        con = connect_db()
        cur = con.cursor()
        cur.execute("SELECT * FROM users WHERE email=? and password=?",(email,password))
        user = cur.fetchone()    #! Reads one row from DB
        con.close()

        if user:
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['location'] = user['location']

            if user['role'] =="buyer":
                return redirect('/buyer-dashboard')
            elif user['role'] =="seller":
                return redirect('/seller-dashboard')
            else:
                return redirect('/admin-dashboard')
        else:
            return "Invalid Email or Password"
    return render_template("login.html") 

@app.route('/buyer-dashboard')   
def buyer_page():
    return render_template("buyer_dashboard.html") 

@app.route('/admin-dashboard')
def admin_page():
    return render_template("admin_dashboard.html")   

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/upload-product',methods=['GET','POST'])
def upload_product():
    if request.method =='POST':
        name = request.form['name']
        qty = request.form['qty']
        price = request.form['price']
        expiry = request.form['expiry']
        image = request.files['image']

        filename = secure_filename(image.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'],filename)
        image.save(filepath)

        seller_id = session.get('user_id')

        con = connect_db()
        cur = con.cursor()
        cur.execute("INSERT INTO products(seller_id,name,qty,price,expiry_date,image) VALUES(?,?,?,?,?,?)",(seller_id,name,qty,price,expiry,filename))
        con.commit()
        con.close()

        return redirect('/seller-dashboard')
    return render_template ("seller_upload.html")

@app.route('/seller-dashboard')
def seller_page():
    seller_id = session.get('user_id')
    con = connect_db()
    cur = con.cursor()
    cur.execute("SELECT * FROM products WHERE seller_id=?",(seller_id,))  #! why this (seller_id,) = Because SQLite execute() expects parameters in a tuple. (seller_id) is not a tuple, (seller_id,) is a tuple.
    item = cur.fetchall()
    con.close()
    current_date = date.today().isoformat() 
    return render_template("seller_dashboard.html",products=item,current_date=current_date)   #! products variable in frontend and in backend item

@app.route('/products')
def show_products():
    buyer_location = session.get('location')
    con = connect_db()
    cur = con.cursor()
    cur.execute("""
        SELECT p.* FROM products p 
        JOIN users u ON p.seller_id = u.id
        WHERE u.location = ? 
        AND DATE(p.expiry_date)>=DATE('now')""",(buyer_location,))
    items = cur.fetchall()
    con.close()
    today = datetime.now().date().isoformat()
    return render_template("buyer_products.html",products=items,current_date=today)

@app.route('/wallet',methods=['GET','POST'])
def wallet():
    user_id = session.get('user_id')
    con = connect_db()
    cur = con.cursor()

    if request.method == "POST":
        amt = int(request.form['amount'])
        cur.execute("UPDATE wallet SET balance = balance + ? WHERE user_id=?",(amt,user_id))
        con.commit()
    cur.execute("SELECT balance FROM wallet WHERE user_id=?",(user_id,))
    bal = cur.fetchone()['balance']
    con.close()
    return render_template("wallet.html",balance=bal)    


@app.route('/buy/<int:pid>')  #? pid= Product id 
def buy(pid):
    user_id = session.get('user_id')

    con = connect_db()
    cur = con.cursor() 

    #! get product details  
    cur.execute("SELECT * FROM products WHERE id=?",(pid,))
    item = cur.fetchone()

    #! get buyer balance
    cur.execute("SELECT balance FROM wallet WHERE user_id=?",(user_id,))
    bal = cur.fetchone()['balance']
    price = item['price']

    if bal<price:
        con.close()
        return redirect('/wallet?error=low_balance')
    
    #! deduct balance
    cur.execute("UPDATE wallet SET balance = balance - ? WHERE user_id=?",(price,user_id))

    #! credit seller
    cur.execute("UPDATE wallet SET balance = balance + ? WHERE user_id=?", (item['seller_id'],price))

    new_qty = item['qty'] - 1
    if new_qty <=0:
        cur.execute("DELETE FROM products WHERE id=?",(pid,))
    else:
        cur.execute("UPDATE products SET qty=? WHERE id=?",(new_qty,pid))  

    #! add order record (Save Order to Orders Table)
    cur.execute("INSERT INTO orders(buyer_id, product_id, qty, amount, date,item_name) VALUES(?,?,?,?,DATE('now'),?)",(user_id,pid,1,price,item['name'])) #? 1 = assuming customer buy item only one 

    con.commit()
    con.close()
    
    return redirect('/products?success=1')

@app.route('/admin-sellers')
def admin_sellers():
    con=connect_db()
    cur=con.cursor()
    cur.execute("SELECT * FROM users WHERE role='seller'")
    rows = cur.fetchall()
    con.close()
    return render_template("admin_sellers.html",sellers=rows)


@app.route('/approve/<int:uid>')
def approve(uid):
    con = connect_db()
    cur = con.cursor()
    cur.execute("UPDATE users SET status='approved' WHERE id=?",(uid,))
    con.commit()
    con.close()
    return redirect('/admin-sellers')

@app.route('/reject/<int:uid>')
def reject(uid):
    con = connect_db()
    cur= con.cursor()
    cur.execute("DELETE FROM users WHERE id = ?",(uid,))
    con.commit()
    con.close()
    return redirect('/admin-sellers')


@app.route('/buyer-orders')
def buyer_orders():
    buyer_id = session.get('user_id')
    con = connect_db()
    cur = con.cursor()
    cur.execute(""" 
        SELECT item_name, amount, qty, date
        FROM orders 
        WHERE buyer_id=?
        ORDER BY id DESC
        """,(buyer_id,))
    data = cur.fetchall()
    con.close()
    return render_template("buyer_orders.html",orders=data)


@app.route('/seller-orders')
def seller_orders():
    seller_id = session.get('user_id')
    con= connect_db()
    cur = con.cursor()
    cur.execute("""
        SELECT buyer_id,item_name, amount, qty, date
        FROM orders 
        WHERE product_id IN (SELECT id FROM products WHERE seller_id=?)
        ORDER BY id DESC
        """,(seller_id,))
    rows = cur.fetchall()
    con.close()
    return render_template("seller_orders.html", orders=rows)

#!--------------------------------------------------------------------------------------------
@app.route('/admin-products')
def admin_products():
    con = connect_db()
    cur = con.cursor()
    cur.execute("SELECT * FROM products ORDER BY id DESC")
    rows = cur.fetchall()
    con.close()
    return render_template("admin_products.html", products=rows)
@app.route('/admin-delete/<int:pid>')
def admin_delete(pid):
    con = connect_db()
    cur = con.cursor()
    cur.execute("DELETE FROM products WHERE id=?", (pid,))
    con.commit()
    con.close()
    return redirect('/admin-products')




if __name__=='__main__':
    app.run(debug=True)