from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'nakul'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '2005'
app.config['MYSQL_DB'] = 'ecommerce_db'
mysql = MySQL(app)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        
        cur = mysql.connection.cursor()
        # Check if email already exists
        cur.execute("SELECT * FROM users WHERE email = %s", [email])
        existing_user = cur.fetchone()
        
        if existing_user:
            flash('Email is already taken. Please choose a different one.', 'error')
        else:
            cur.execute("INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)", 
                        (username, email, password, 'user'))
            mysql.connection.commit()
            flash('Registration successful, please login.', 'success')
            return redirect(url_for('login'))
        cur.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", [email])
        user = cur.fetchone()
        cur.close()
        
        if user and user[3] and check_password_hash(user[3], password):
            session['loggedin'] = True
            session['id'] = user[0]
            session['username'] = user[1]
            session['role'] = user[4]
            return redirect(url_for('dashboard') if user[4] == 'user' else url_for('admin'))
        
        flash('Incorrect email or password. Please try again.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'loggedin' in session and session['role'] == 'user':
        cur = mysql.connection.cursor()
        search_query = request.form.get('search') if request.method == 'POST' else ''
        
        if search_query:
            cur.execute("SELECT * FROM products WHERE name LIKE %s", ('%' + search_query + '%',))
        else:
            cur.execute("SELECT * FROM products")
        
        products = cur.fetchall()
        cur.close()
        
        return render_template('dashboard.html', username=session['username'], products=products, search_query=search_query)
    return redirect(url_for('login'))

@app.route('/admin')
def admin():
    if 'loggedin' in session and session['role'] == 'admin':
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM products")
        products = cur.fetchall()
        cur.close()
        return render_template('admin.html', products=products)
    return redirect(url_for('login'))

@app.route('/admin/product/new', methods=['GET', 'POST'])
def create_product():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        stock = request.form['stock']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO products (name, description, price, stock) VALUES (%s, %s, %s, %s)", (name, description, price, stock))
        mysql.connection.commit()
        cur.close()
        flash('Product added successfully.', 'success')
        return redirect(url_for('admin'))
    return render_template('product_form.html')

@app.route('/admin/product/edit/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM products WHERE id = %s", [id])
    product = cur.fetchone()
    cur.close()
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        stock = request.form['stock']
        cur = mysql.connection.cursor()
        cur.execute("UPDATE products SET name = %s, description = %s, price = %s, stock = %s WHERE id = %s", (name, description, price, stock, id))
        mysql.connection.commit()
        cur.close()
        flash('Product updated successfully.', 'success')
        return redirect(url_for('admin'))
    return render_template('product_form.html', product=product)

@app.route('/admin/product/delete/<int:id>', methods=['POST'])
def delete_product(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM products WHERE id = %s", [id])
    mysql.connection.commit()
    cur.close()
    flash('Product deleted successfully.', 'success')
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)
