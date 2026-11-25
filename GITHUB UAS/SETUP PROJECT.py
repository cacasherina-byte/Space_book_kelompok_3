#1.	Setup Project
import datetime
import sqlite3
JAM_BUKA = 8
JAM_TUTUP = 22
ADMIN_ACCOUNTS = {
    "sherina": ("Sherina", "12346"),
    "richard": ("Richard", "123456"),
    "ridwan": ("Ridwan", "123456"),
}
DEFAULT_FAS = [
    ("Lapangan Futsal A", "Olahraga", 150000),
    ("Lapangan Badminton B", "Olahraga", 75000),
    ("Ruang Meeting Alpha", "Coworking", 60000),
    ("Ruang Meeting Beta", "Coworking", 60000),
]


def get_conn():
    conn = sqlite3.connect("space_book.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL,
            no_hp TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user'
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS fasilitas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_fasilitas TEXT NOT NULL,
            jenis TEXT NOT NULL,
            harga_per_jam INTEGER NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS booking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kode_booking TEXT UNIQUE NOT NULL,
            id_fasilitas INTEGER NOT NULL,
            id_user INTEGER NOT NULL,
            nama_penyewa TEXT NOT NULL,
            no_hp TEXT NOT NULL,
            catatan TEXT,
            tanggal TEXT NOT NULL,
            jam_mulai TEXT NOT NULL,
            jam_selesai TEXT NOT NULL,
            total_harga INTEGER NOT NULL,
            status_booking TEXT NOT NULL,
            status_bayar TEXT NOT NULL,
            FOREIGN KEY (id_fasilitas) REFERENCES fasilitas(id),
            FOREIGN KEY (id_user) REFERENCES user(id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pembayaran (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_booking INTEGER NOT NULL,
            metode TEXT NOT NULL,
            referensi TEXT NOT NULL,
            tanggal_bayar TEXT NOT NULL,
            FOREIGN KEY (id_booking) REFERENCES booking(id)
        )
    """)

    for uname, (nama, pwd) in ADMIN_ACCOUNTS.items():
        cur.execute("SELECT id FROM user WHERE LOWER(username) = LOWER(?)", (uname,))
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO user (nama, no_hp, username, password, role) VALUES (?, ?, ?, ?, 'admin')",
                (nama, "0800000000", uname, pwd),
            )

    cur.execute("SELECT COUNT(*) AS cnt FROM fasilitas")
    if cur.fetchone()["cnt"] == 0:
        cur.executemany(
            "INSERT INTO fasilitas (nama_fasilitas, jenis, harga_per_jam) VALUES (?, ?, ?)",
            DEFAULT_FAS,
        )

    conn.commit()
    conn.close()


def jam_to_menit(jam_str):
    try:
        parts = jam_str.strip().split(":")
        if len(parts) != 2:
            return None
        h, m = int(parts[0]), int(parts[1])
        if not (0 <= h <= 23 and 0 <= m <= 59):
            return None
        return h * 60 + m
    except ValueError:
        return None


def validasi_tanggal(tgl_str):
    try:
        datetime.datetime.strptime(tgl_str.strip(), "%d-%m-%Y")
        return True
    except ValueError:
        return False


def registrasi_user():
    print("\n--- REGISTRASI USER ---")
    nama = input("Nama Lengkap : ").strip()
    no_hp = input("Nomor HP     : ").strip()
    username = input("Username     : ").strip()
    password = input("Password     : ").strip()

    if not nama or not username:
        print("Nama dan username wajib diisi.")
        return
    if not (no_hp.isdigit() and len(no_hp) >= 10):
        print("Nomor HP minimal 10 digit angka.")
        return
    if len(password) < 6:
        print("Password minimal 6 karakter.")
        return

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM user WHERE LOWER(username) = LOWER(?)", (username,))
    if cur.fetchone():
        print("Username sudah digunakan.")
        conn.close()
        return

    cur.execute(
        "INSERT INTO user (nama, no_hp, username, password, role) VALUES (?, ?, ?, ?, 'user')",
        (nama, no_hp, username, password),
    )
    conn.commit()
    conn.close()
    print("Registrasi berhasil! Silakan login.")

