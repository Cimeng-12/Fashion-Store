from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Pastikan ada secret_key agar session berfungsi
app.secret_key = "supersecretkey"  # Untuk pesan flash
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    """Fungsi untuk memeriksa apakah file yang di-upload memiliki ekstensi yang valid."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Buat folder penyimpanan jika belum ada
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def is_admin(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return user and user['is_admin'] == 1  # Cek apakah is_admin = 1

def init_db():
    conn = get_db_connection()  # Membuat koneksi ke database
    # Cek apakah kolom 'status' sudah ada sebelum menambahkannya
    cursor = conn.execute("PRAGMA table_info(orders)")
    columns = [column[1] for column in cursor.fetchall()]
    if "status" not in columns:
        conn.execute('ALTER TABLE orders ADD COLUMN status TEXT DEFAULT "Pending"')
    conn.commit()

    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS returns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                order_id TEXT NOT NULL,
                product_name TEXT NOT NULL,
                reason TEXT NOT NULL,
                details TEXT NOT NULL,
                image_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    # Pastikan Anda melakukan sesuatu dengan 'conn' di sini, seperti menjalankan query atau commit
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
                           id INTEGER PRIMARY KEY AUTOINCREMENT,
                           username TEXT UNIQUE NOT NULL,
                           email TEXT UNIQUE NOT NULL,
                           password TEXT NOT NULL,
                           is_admin INTEGER DEFAULT 0
       )''')

    conn.execute('''CREATE TABLE IF NOT EXISTS products (
                           id INTEGER PRIMARY KEY AUTOINCREMENT,
                           name TEXT NOT NULL,
                           description TEXT,
                           price REAL NOT NULL,
                           image_url TEXT
       )''')

    conn.execute('''CREATE TABLE IF NOT EXISTS orders (
                           id INTEGER PRIMARY KEY AUTOINCREMENT,
                           user_id INTEGER,
                           name TEXT NOT NULL,
                           address TEXT NOT NULL,
                           phone TEXT NOT NULL,
                           total_price REAL NOT NULL,
                           created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                           FOREIGN KEY (user_id) REFERENCES users (id)
       )''')

    conn.execute('''CREATE TABLE IF NOT EXISTS order_items (
                           id INTEGER PRIMARY KEY AUTOINCREMENT,
                           order_id INTEGER,
                           product_id INTEGER,
                           quantity INTEGER,
                           price REAL,
                           FOREIGN KEY (order_id) REFERENCES orders (id),
                           FOREIGN KEY (product_id) REFERENCES products (id)
       )''')


def add_admin_column():
    conn = get_db_connection()
    try:
        conn.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Kolom sudah ada

    # Tambahkan admin jika belum ada
    existing_admin = conn.execute("SELECT * FROM users WHERE username = 'admin'").fetchone()
    if not existing_admin:
        admin_password = generate_password_hash('admin123')
        conn.execute("INSERT INTO users (username, email, password, is_admin) VALUES (?, ?, ?, ?)",
                     ('admin', 'admin@example.com', admin_password, 1))
        conn.commit()
    conn.close()

    if conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
        products = [
            ("Topi Baseball", "Topi stylish untuk melindungi dari sinar matahari.", 30000,
             "static/images/topi_baseball.jpg"),
            ("Hoodie Oversized", "Hoodie nyaman dengan desain oversized.", 75000, "static/images/hoodie_oversized.jpg"),
            ("Jaket Denim", "Jaket denim klasik untuk gaya casual.", 120000, "static/images/jaket_denim.jpg"),
            ("Kaos Polo", "Kaos polo elegan untuk tampilan semi-formal.", 65000, "static/images/kaos_polo.png"),
            ("Sepatu Boots", "Sepatu boots kulit untuk tampilan maskulin.", 250000, "static/images/sepatu_boots.jpeg"),
            ("Sling Bag Kulit", "Tas selempang kulit dengan desain minimalis.", 135000, "static/images/sling_bag.jpg"),
            ("Kacamata Retro", "Kacamata dengan desain retro yang unik.", 55000, "static/images/kacamata_retro.jpg"),
            ("Dompet Kulit", "Dompet kulit premium dengan banyak slot kartu.", 90000, "static/images/dompet_kulit.jpg"),
            ("Gelang Stainless", "Gelang stainless dengan desain elegan.", 45000, "static/images/gelang_stainless.jpg"),
            ("Scarf Wool", "Scarf berbahan wool untuk musim dingin.", 85000, "static/images/scarf_wool.jpg")
        ]
        conn.executemany("INSERT INTO products (name, description, price, image_url) VALUES (?, ?, ?, ?)", products)
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html', bg_color="#121212", text_color="#ffffff")


@app.route('/catalog')
def catalog():
    conn = get_db_connection()
    # Ambil produk yang statusnya tidak 'Pending'
    products = conn.execute('SELECT * FROM products WHERE status != "Pending"').fetchall()
    conn.close()

    return render_template('catalog.html', products=products, bg_color="#1e1e1e", text_color="#ffffff")

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    conn.close()
    if product is None:
        return 'Produk tidak ditemukan!', 404
    return render_template('product_detail.html', product=product, bg_color="#2c2c2c", text_color="#ffffff")

@app.route('/cart')
def cart():
    # Ambil produk yang ada di dalam sesi
    cart_items = session.get('cart', [])

    # Dapatkan detail produk berdasarkan ID yang ada di cart
    conn = get_db_connection()
    products_in_cart = []
    for item in cart_items:
        product = conn.execute('SELECT * FROM products WHERE id = ?', (item,)).fetchone()
        if product:
            products_in_cart.append(product)
    conn.close()

    return render_template('cart.html', products=products_in_cart, bg_color="#181818", text_color="#ffffff")


@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    cart_items = session.get('cart', {})

    if isinstance(cart_items, list):  # Konversi list ke dict jika perlu
        cart_items = {pid: 1 for pid in cart_items}

    if product_id in cart_items:
        cart_items[product_id] += 1  # Tambah jumlah produk
    else:
        cart_items[product_id] = 1

    session['cart'] = cart_items
    session.modified = True

    flash("Produk ditambahkan ke keranjang!", "success")
    return redirect(url_for('catalog'))


@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    if 'user_id' not in session:
        flash("Anda harus login untuk menghapus produk.", "warning")
        return redirect(url_for('contact'))

    conn = get_db_connection()
    product = conn.execute('SELECT user_id FROM products WHERE id = ?', (product_id,)).fetchone()

    if not product:
        conn.close()
        flash("Produk tidak ditemukan!", "danger")
        return redirect(url_for('catalog'))

    if session['user_id'] != product['user_id'] and not is_admin(session['user_id']):
        conn.close()
        flash("Anda tidak memiliki izin untuk menghapus produk ini!", "danger")
        return redirect(url_for('catalog'))

    conn.execute('DELETE FROM products WHERE id = ?', (product_id,))
    conn.commit()
    conn.close()
    flash("Produk berhasil dihapus.", "success")
    return redirect(url_for('catalog'))

@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    cart_items = session.get('cart', [])

    # Pastikan semua item dalam cart adalah tipe int untuk menghindari perbedaan tipe
    cart_items = [int(item) for item in cart_items]

    if product_id in cart_items:
        cart_items.remove(product_id)

    session['cart'] = cart_items
    session.modified = True  # Penting agar perubahan di session disimpan!

    flash("Produk berhasil dihapus dari keranjang!", "success")
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    user_id = session.get('user_id')
    if not user_id:
        flash("Silakan login sebelum melakukan checkout!", "warning")
        return redirect(url_for('contact'))

    cart_items = session.get('cart', {})
    if isinstance(cart_items, list):
        cart_items = {product_id: 1 for product_id in cart_items}

    conn = get_db_connection()
    products_in_cart = []
    total_price = 0

    for product_id, quantity in cart_items.items():
        product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
        if product:
            products_in_cart.append({
                'id': product['id'],
                'name': product['name'],
                'price': product['price'],
                'quantity': quantity,
                'subtotal': product['price'] * quantity
            })
            total_price += product['price'] * quantity
    conn.close()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        address = request.form.get('address', '').strip()
        phone = request.form.get('phone', '').strip()
        payment_method = request.form.get('payment_method', '').strip()  # Ambil metode pembayaran

        print(f"Checkout Data: user_id={user_id}, name={name}, address={address}, phone={phone}, total_price={total_price}, payment_method={payment_method}")

        if not name or not address or not phone or not payment_method:
            flash("Harap isi semua informasi pengiriman dan pilih metode pembayaran!", "danger")
            return redirect(url_for('checkout'))
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Simpan pesanan dengan metode pembayaran
            cursor.execute('''INSERT INTO orders (user_id, name, address, phone, total_price, payment_method) 
                              VALUES (?, ?, ?, ?, ?, ?)''',
                           (user_id, name, address, phone, total_price, payment_method))
            order_id = cursor.lastrowid

            print(f"Order ID yang dibuat: {order_id}")

            for item in products_in_cart:
                cursor.execute('''INSERT INTO order_items (order_id, product_id, quantity, price) 
                                  VALUES (?, ?, ?, ?)''',
                               (order_id, item['id'], item['quantity'], item['price']))

            conn.commit()
            print("pesanan berhasil disimpan!")
            flash(f"Pemesanan berhasil dengan metode pembayaran: {payment_method}", "success")

            session.pop('cart', None)

            return redirect(url_for('orders'))

        except sqlite3.Error as e:
            conn.rollback()
            print(f"Error saat menyimpan pesanan: {str(e)}")
            flash(f"Terjadi kesalahan saat menyimpan pesanan: {str(e)}", "danger")

        finally:
            conn.close()

    return render_template('checkout.html', products=products_in_cart, total_price=total_price, bg_color="#181818", text_color="#ffffff")


@app.route('/orders')
def orders():
    if 'user_id' not in session:
        flash("Silakan login untuk melihat pesanan Anda!", "warning")
        return redirect(url_for('login'))  # Redirect ke halaman login

    user_id = session['user_id']
    print(f"User ID yang sedang login: {user_id}")

    conn = get_db_connection()
    # Ambil semua pesanan untuk user yang sedang login
    orders = conn.execute('SELECT * FROM orders WHERE user_id = ?', (session['user_id'],)).fetchall()
    conn.close()

    print(f"pesanan yang ditemukan: {orders}")

    # Menampilkan daftar pesanan
    return render_template('orders.html', orders=orders, bg_color="#181818", text_color="#ffffff")


@app.route('/upload_product', methods=['GET', 'POST'])
def upload_product():
    if 'user_id' not in session:
        flash("Anda harus login untuk mengupload produk.", "warning")
        return redirect(url_for('contact'))

    if request.method == 'POST':
        user_id = session['user_id']
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        image = request.files['image']

        # Cek apakah file gambar valid
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image_path = os.path.join(UPLOAD_FOLDER, filename)
            image.save(image_path)

            image_url = image_path.replace(os.sep, '/')




            # Simpan produk ke database
            conn = get_db_connection()
            conn.execute('''
                INSERT INTO products (name, description, price, image_url, status, user_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, description, price, image_url, 'Pending', user_id))
            conn.commit()
            conn.close()

            flash("Produk berhasil di-upload dan sedang menunggu persetujuan.", "success")
            return redirect(url_for('catalog'))  # Redirect ke halaman katalog

        else:
            flash("Format gambar tidak valid atau tidak ada gambar yang diunggah.", "danger")
            return redirect(url_for('upload_product'))

    return render_template('upload_product.html')

@app.route('/approve_products')
def approve_products():
    # Pastikan user adalah admin
    if 'user_id' not in session or not is_admin(session['user_id']):
        flash("Anda harus login sebagai admin untuk mengakses halaman ini.", "warning")
        return redirect(url_for('contact'))  # Redirect ke halaman login jika bukan admin

    # Ambil produk yang statusnya 'Pending'
    conn = get_db_connection()
    products_pending = conn.execute('SELECT * FROM products WHERE status = "Pending"').fetchall()
    conn.close()

    return render_template('approve_products.html', products=products_pending, bg_color="#1e1e1e", text_color="#ffffff")

@app.route('/approve_product/<int:product_id>')
def approve_product(product_id):
    # Pastikan user adalah admin
    if 'user_id' not in session or not is_admin(session['user_id']):
        flash("Anda harus login sebagai admin untuk mengakses halaman ini.", "warning")
        return redirect(url_for('contact'))  # Redirect ke halaman login jika bukan admin

    # Update status produk menjadi 'Approved'
    conn = get_db_connection()
    conn.execute('UPDATE products SET status = "Approved" WHERE id = ?', (product_id,))
    conn.commit()
    conn.close()

    flash("Produk berhasil disetujui.", "success")
    return redirect(url_for('approve_products'))  # Kembali ke halaman approve products

@app.route('/reject_product/<int:product_id>')
def reject_product(product_id):
    # Pastikan user adalah admin
    if 'user_id' not in session or not is_admin(session['user_id']):
        flash("Anda harus login sebagai admin untuk mengakses halaman ini.", "warning")
        return redirect(url_for('contact'))  # Redirect ke halaman login jika bukan admin

    # Hapus produk dari database
    conn = get_db_connection()
    conn.execute('DELETE FROM products WHERE id = ?', (product_id,))
    conn.commit()
    conn.close()

    flash("Produk berhasil ditolak dan dihapus dari daftar.", "danger")
    return redirect(url_for('approve_products'))  # Kembali ke halaman approve products

@app.route('/process_order/<int:order_id>')
def process_order(order_id):
    if 'user_id' not in session:
        flash("Silakan login untuk memproses pesanan!", "warning")
        return redirect(url_for('contact'))

    conn = get_db_connection()
    order = conn.execute('SELECT * FROM orders WHERE id = ? AND user_id = ?', (order_id, session['user_id'])).fetchone()

    if not order:
        flash("Pesanan tidak ditemukan atau bukan milik Anda!", "danger")
    elif order['status'] != 'Pending':
        flash("Pesanan ini sudah diproses!", "info")
    else:
        conn.execute('UPDATE orders SET status = "Processing" WHERE id = ?', (order_id,))
        conn.commit()
        flash("Pesanan sedang diproses!", "success")

    conn.close()
    return redirect(url_for('orders'))


@app.route('/confirm_order/<int:order_id>')
def confirm_order(order_id):
    if 'user_id' not in session:
        flash("Silakan login untuk mengonfirmasi pesanan!", "warning")
        return redirect(url_for('contact'))

    conn = get_db_connection()
    order = conn.execute('SELECT * FROM orders WHERE id = ? AND user_id = ?', (order_id, session['user_id'])).fetchone()

    if not order:
        flash("Pesanan tidak ditemukan atau bukan milik Anda!", "danger")
    elif order['status'] == 'Completed':
        flash("Pesanan ini sudah selesai!", "info")
    else:
        conn.execute('UPDATE orders SET status = "Completed" WHERE id = ?', (order_id,))
        conn.commit()
        flash("Pesanan berhasil dikonfirmasi sebagai selesai!", "success")

    conn.close()
    return redirect(url_for('orders'))


@app.route('/daftar', methods=['GET', 'POST'])
def daftar():
        if request.method == 'POST':
            username = request.form['username']
            email = request.form['email']
            password = generate_password_hash(request.form['password'])

            if len(password) < 6:
                flash("Password harus lebih dari 6 karakter!", "danger")
                return redirect(url_for('daftar'))

            hashed_password = generate_password_hash(password)

            conn = get_db_connection()
            existing_user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            existing_email = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

            if existing_user:
                flash("Username sudah digunakan!", "danger")
                conn.close()
                return redirect(url_for('daftar'))

            if existing_email:
                flash("Email sudah terdaftar!", "danger")
                conn.close()
                return redirect(url_for('daftar'))

            conn.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', (username, email, password))
            conn.commit()
            conn.close()

            flash("Pendaftaran berhasil! Silakan login.", "success")
            return redirect(url_for('contact'))

        return render_template('daftar.html', bg_color="#252525", text_color="#ffffff")


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['email'] = user['email']

            # Pastikan 'is_admin' ada sebelum mengaksesnya
            session['is_admin'] = user['is_admin'] if 'is_admin' in user.keys() else 0
            print(f"User ID setelah login: {session.get('user_id')}")  # Debugging

            flash("Login berhasil!", "success")
            return redirect(url_for('profile'))
        else:
            flash("Login gagal, periksa kembali username dan password!", "danger")

    return render_template('contact.html', bg_color="#222222", text_color="#ffffff")

@app.route('/logout')
def logout():
    print(f"Session sebelum logout: {session}")  # Debugging
    session.pop('user_id', None)  # Hapus session user_id
    session.clear()  # Hapus semua session
    session.modified = True  # Pastikan perubahan tersimpan
    print(f"Session setelah logout: {session}")  # Debugging
    flash("Anda telah logout!", "info")
    return redirect(url_for('index'))  # Redirect ke halaman utama

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash("Silakan login terlebih dahulu", "warning")
        return redirect(url_for('contact'))  # ✅ Redirect ke login jika belum login

    # ✅ Pastikan semua data dikirim ke template
    return render_template(
        'profile.html',
        username=session.get('username', 'Guest'),
        email=session.get('email', 'Email tidak tersedia'),
        is_admin=session.get('is_admin', 0),
        bg_color="#f8f9fa",
        text_color="#343a40"
    )


@app.route('/update_address/<int:order_id>', methods=['GET', 'POST'])
def update_address(order_id):
    if 'user_id' not in session:
        flash("Silakan login untuk mengubah alamat!", "warning")
        return redirect(url_for('contact'))

    conn = get_db_connection()
    order = conn.execute('SELECT * FROM orders WHERE id = ? AND user_id = ?', (order_id, session['user_id'])).fetchone()

    if not order:
        flash("Pesanan tidak ditemukan atau bukan milik Anda!", "danger")
        conn.close()
        return redirect(url_for('orders'))

    if order['is_address_updated']:
        flash("Alamat sudah diubah sebelumnya dan tidak dapat diubah lagi!", "danger")
        conn.close()
        return redirect(url_for('orders'))

    if request.method == 'POST':
        new_address = request.form.get('new_address', '').strip()
        if not new_address:
            flash("Alamat baru tidak boleh kosong!", "danger")
        else:
            conn.execute('UPDATE orders SET address = ?, is_address_updated = 1 WHERE id = ?', (new_address, order_id))
            conn.commit()
            flash("Alamat berhasil diperbarui!", "success")
        conn.close()
        return redirect(url_for('orders'))

    conn.close()
    return render_template('update_address.html', order=order)



# Halaman Admin untuk melihat kritik & saran
@app.route("/admin_feedbacks")
def admin_feedbacks():
    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, message, created_at FROM feedback ORDER BY created_at DESC")
        feedbacks = cursor.fetchall()

    return render_template("admin_feedbacks.html", feedbacks=feedbacks)


# Route untuk menampilkan form pengajuan pengembalian
@app.route("/return_form", methods=["GET"])
def return_form():
    return render_template("return_form.html")


# Route untuk menangani pengajuan pengembalian
@app.route("/return_product", methods=["POST"])
def return_product():
    if request.method == "POST":
        name = request.form["name"]
        order_id = request.form["order_id"]
        product_name = request.form["product_name"]
        reason = request.form["reason"]
        details = request.form["details"]

        # Mengelola file gambar jika diunggah
        image_url = None
        if "return_image" in request.files:
            file = request.files["return_image"]
            if file.filename != "":
                filename = secure_filename(file.filename)
                image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(image_path)
                image_url = f"static/uploads/{filename}"

        # Simpan data ke database
        with sqlite3.connect("database.db") as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO returns (name, order_id, product_name, reason, details, image_url)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, order_id, product_name, reason, details, image_url))
            conn.commit()

        flash("Pengajuan pengembalian berhasil dikirim!", "success")
        return redirect(url_for("return_form"))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0')