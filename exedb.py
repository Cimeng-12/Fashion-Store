import sqlite3

def add_products_to_db(db_name):
    # Koneksi ke database
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Data produk
    products = [
        ("Topi Baseball", "Topi stylish untuk melindungi dari sinar matahari.", 30000, "static/images/topi_baseball.jpg"),
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

    # Menambahkan produk ke dalam tabel
    cursor.executemany("INSERT INTO products (name, description, price, image_url) VALUES (?, ?, ?, ?)", products)

    # Menyimpan perubahan
    conn.commit()

    # Menutup koneksi
    conn.close()


def create_tabel():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    # Membuat tabel 'products'
    c.execute('''CREATE TABLE IF NOT EXISTS products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        description TEXT,
                        price REAL NOT NULL,
                        image_url TEXT,
                        status TEXT DEFAULT 'pending',
                        user_id INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')

    # Membuat tabel 'orders'
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER,
                            name TEXT NOT NULL,
                            address TEXT NOT NULL,
                            phone TEXT NOT NULL,
                            total_price REAL NOT NULL,
                            payment_method TEXT NOT NULL,
                            status TEXT DEFAULT 'Pending',  -- Kolom status pesanan
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES users (id)
                            )''')

    # Membuat tabel 'order_items'
    c.execute('''CREATE TABLE IF NOT EXISTS order_items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        order_id INTEGER,
                        product_id INTEGER,
                        quantity INTEGER,
                        price REAL,
                        FOREIGN KEY (order_id) REFERENCES orders(id),
                        FOREIGN KEY (product_id) REFERENCES products(id)
    )''')
    conn.commit()
    conn.close()

    print("succes")

def delete_tabel():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''DROP TABLE IF EXISTS products;''')
    c.execute('''DROP TABLE IF EXISTS orders;''')
    c.execute('''DROP TABLE IF EXISTS order_items;''')
    conn.commit()
    conn.close()
    print("SUCCES")

def make_user_admin(user_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()# Koneksi ke database
    try:
        c.execute('UPDATE users SET is_admin = 1 WHERE id = ?', (user_id,))
        conn.commit()  # Simpan perubahan
        print(f"User dengan ID {user_id} telah diubah menjadi admin.")
    except Exception as e:
        print(f"Terjadi kesalahan: {e}")
    finally:
        conn.close()

# Panggil fungsi untuk menjadikan user dengan id 3 sebagai admin
# make_user_admin(3)

def insert_products():
    # Produk yang akan dimasukkan
    products = [
        ("Topi Baseball", "Topi stylish untuk melindungi dari sinar matahari.", 30000,
         "static/images/topi_baseball.jpg"),
        ("Hoodie Oversized", "Hoodie nyaman dengan desain oversized.", 75000, "static/images/hoodie_oversized.jpg"),
        ("Jaket Denim", "Jaket denim klasik untuk gaya casual.", 120000, "static/images/jaket_denim.jpg"),
        ("Kaos Polos", "Kaos polo elegan untuk tampilan semi-formal.", 65000, "static/images/kaos_polo.png"),
        ("Sepatu Boots", "Sepatu boots kulit untuk tampilan maskulin.", 250000, "static/images/sepatu_boots.jpeg"),
        ("Sling Bag Kulit", "Tas selempang kulit dengan desain minimalis.", 135000, "static/images/sling_bag.jpg"),
        ("Kacamata Retro", "Kacamata dengan desain retro yang unik.", 55000, "static/images/kacamata_retro.jpg"),
        ("Dompet Kulit", "Dompet kulit premium dengan banyak slot kartu.", 90000, "static/images/dompet_kulit.jpg"),
        ("Gelang Stainless", "Gelang stainless dengan desain elegan.", 45000, "static/images/gelang_stainless.jpg"),
        ("Scarf Wool", "Scarf berbahan wool untuk musim dingin.", 85000, "static/images/scarf_wool.jpg")
    ]

    # Koneksi ke database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Loop untuk memasukkan data produk
    for product in products:
        cursor.execute('''
            INSERT INTO products (name, description, price, image_url, status, user_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (product[0], product[1], product[2], product[3], 'Approved', 3))  # 3 adalah user_id admin

    # Simpan perubahan ke database
    conn.commit()
    conn.close()

def delete_orders():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''DROP TABLE IF EXISTS orders;''')
    conn.commit()
    conn.close()
    print("SUCCES")

create_tabel()