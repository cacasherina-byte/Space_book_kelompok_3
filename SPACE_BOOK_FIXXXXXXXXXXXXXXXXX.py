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


def login_akun():
    print("\n--- LOGIN SPACE-BOOK ---")
    username = input("Username : ").strip()
    password = input("Password : ").strip()

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM user WHERE LOWER(username) = LOWER(?) AND password = ?",
        (username, password),
    )
    akun = cur.fetchone()
    conn.close()

    if akun:
        print(f"Login Berhasil. Selamat datang, {akun['nama']} ({akun['role']}).")
        return dict(akun)
    print("Username atau Password Salah")
    return None


def lihat_fasilitas():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM fasilitas ORDER BY id")
    rows = cur.fetchall()
    conn.close()

    print("\nID | Nama Fasilitas          | Jenis     | Harga/Jam")
    print("-" * 58)
    for r in rows:
        print(f"{r['id']:<2} | {r['nama_fasilitas']:<23} | {r['jenis']:<9} | Rp {r['harga_per_jam']:,}")


def cari_bentrok(id_fasilitas, tanggal, mulai_m, selesai_m):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT * FROM booking
        WHERE id_fasilitas = ? AND tanggal = ?
          AND status_booking NOT IN ('DIBATALKAN', 'DITOLAK')
        """,
        (id_fasilitas, tanggal),
    )
    rows = cur.fetchall()
    conn.close()

    bentrok = []
    for r in rows:
        m_lama = jam_to_menit(r["jam_mulai"])
        s_lama = jam_to_menit(r["jam_selesai"])
        if m_lama is not None and s_lama is not None:
            if mulai_m < s_lama and selesai_m > m_lama:
                bentrok.append(dict(r))
    return bentrok


def rekomendasi_slot(id_fasilitas, tanggal, durasi_jam):
    durasi_menit = int(durasi_jam * 60)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT jam_mulai, jam_selesai FROM booking
        WHERE id_fasilitas = ? AND tanggal = ?
          AND status_booking NOT IN ('DIBATALKAN', 'DITOLAK')
        """,
        (id_fasilitas, tanggal),
    )
    terpakai = []
    for r in cur.fetchall():
        m1, m2 = jam_to_menit(r["jam_mulai"]), jam_to_menit(r["jam_selesai"])
        if m1 is not None and m2 is not None:
            terpakai.append((m1, m2))
    conn.close()

    rekom = []
    step = 60
    start_bound = JAM_BUKA * 60
    end_bound = JAM_TUTUP * 60
    cur_m = start_bound
    while cur_m + durasi_menit <= end_bound:
        cand_end = cur_m + durasi_menit
        tabrakan = any(cur_m < b and cand_end > a for a, b in terpakai)
        if not tabrakan:
            h1, m1 = divmod(cur_m, 60)
            h2, m2 = divmod(cand_end, 60)
            rekom.append(f"{h1:02d}:{m1:02d} - {h2:02d}:{m2:02d}")
        cur_m += step
    return rekom


def cek_ketersediaan():
    lihat_fasilitas()
    try:
        id_fas = int(input("\nID Fasilitas : ").strip())
    except ValueError:
        print("ID Fasilitas harus berupa angka.")
        return

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM fasilitas WHERE id = ?", (id_fas,))
    fas = cur.fetchone()
    conn.close()
    if not fas:
        print("Fasilitas tidak ditemukan.")
        return

    tanggal = input("Tanggal (DD-MM-YYYY) : ").strip()
    jam_mulai = input("Jam Mulai (HH:MM)    : ").strip()
    jam_selesai = input("Jam Selesai (HH:MM)  : ").strip()

    if not validasi_tanggal(tanggal):
        print("Format tanggal tidak valid. Gunakan DD-MM-YYYY.")
        return

    m_mulai = jam_to_menit(jam_mulai)
    m_selesai = jam_to_menit(jam_selesai)
    if m_mulai is None or m_selesai is None:
        print("Format jam tidak valid. Gunakan HH:MM.")
        return
    if m_mulai < JAM_BUKA * 60 or m_selesai > JAM_TUTUP * 60 or m_selesai <= m_mulai:
        print(f"Jam operasional {JAM_BUKA:02d}:00 - {JAM_TUTUP:02d}:00 dan jam selesai harus lebih besar dari jam mulai.")
        return
    if (m_selesai - m_mulai) < 60:
        print("Durasi booking minimal 1 jam.")
        return

    bentrok = cari_bentrok(id_fas, tanggal, m_mulai, m_selesai)
    durasi_jam = (m_selesai - m_mulai) / 60
    if bentrok:
        print("\nERROR")
        print("Jadwal sudah digunakan.")
        print("Silakan pilih jam lain.")
        saran = rekomendasi_slot(id_fas, tanggal, durasi_jam)
        if saran:
            print("Rekomendasi slot kosong:")
            for slot in saran:
                print(f"- {slot}")
        else:
            print("Tidak ada slot kosong dengan durasi tersebut pada tanggal ini.")
    else:
        estimasi = int(durasi_jam * fas["harga_per_jam"])
        print("\nJadwal Tersedia!")
        print(f"Fasilitas : {fas['nama_fasilitas']}")
        print(f"Durasi    : {durasi_jam:g} jam")
        print(f"Total Biaya: Rp {estimasi:,}")


def generate_kode_booking(cur):
    cur.execute("SELECT id FROM booking ORDER BY id DESC LIMIT 1")
    last = cur.fetchone()
    next_num = (last["id"] + 1) if last else 1
    return f"BK{next_num:04d}"


def buat_booking(user):
    lihat_fasilitas()
    try:
        id_fas = int(input("\nID Fasilitas : ").strip())
    except ValueError:
        print("ID Fasilitas harus berupa angka.")
        return

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM fasilitas WHERE id = ?", (id_fas,))
    fas = cur.fetchone()
    conn.close()
    if not fas:
        print("Fasilitas tidak ditemukan.")
        return

    tanggal = input("Tanggal (DD-MM-YYYY) : ").strip()
    jam_mulai = input("Jam Mulai (HH:MM)    : ").strip()
    jam_selesai = input("Jam Selesai (HH:MM)  : ").strip()

    if not validasi_tanggal(tanggal):
        print("Format tanggal tidak valid.")
        return
    m_mulai = jam_to_menit(jam_mulai)
    m_selesai = jam_to_menit(jam_selesai)
    if m_mulai is None or m_selesai is None or m_mulai < JAM_BUKA * 60 or m_selesai > JAM_TUTUP * 60 or (m_selesai - m_mulai) < 60:
        print("Jam tidak valid atau kurang dari durasi minimal 1 jam.")
        return

    bentrok = cari_bentrok(id_fas, tanggal, m_mulai, m_selesai)
    durasi_jam = (m_selesai - m_mulai) / 60
    if bentrok:
        print("\nERROR")
        print("Jadwal sudah digunakan.")
        print("Silakan pilih jam lain.")
        saran = rekomendasi_slot(id_fas, tanggal, durasi_jam)
        if saran:
            print("Rekomendasi:")
            for slot in saran:
                print(slot)
        return

    nama_penyewa = input("Nama Penyewa     : ").strip() or user["nama"]
    no_hp = input("Nomor HP         : ").strip() or user["no_hp"]
    catatan = input("Catatan Tambahan : ").strip()
    total_harga = int(durasi_jam * fas["harga_per_jam"])

    conn = get_conn()
    cur = conn.cursor()
    kode = generate_kode_booking(cur)
    cur.execute(
        """
        INSERT INTO booking (
            kode_booking, id_fasilitas, id_user, nama_penyewa, no_hp, catatan,
            tanggal, jam_mulai, jam_selesai, total_harga, status_booking, status_bayar
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'MENUNGGU PEMBAYARAN', 'BELUM BAYAR')
        """,
        (
            kode, id_fas, user["id"], nama_penyewa, no_hp, catatan,
            tanggal, jam_mulai.strip(), jam_selesai.strip(), total_harga,
        ),
    )
    conn.commit()
    conn.close()

    print("\nBooking Berhasil")
    print(f"Kode Booking : {kode}")
    print(f"Total Biaya  : Rp {total_harga:,}")
    print("Status       : MENUNGGU PEMBAYARAN")


def riwayat_booking(user):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT b.*, f.nama_fasilitas
        FROM booking b
        JOIN fasilitas f ON b.id_fasilitas = f.id
        WHERE b.id_user = ?
        ORDER BY b.id DESC
        """,
        (user["id"],),
    )
    rows = cur.fetchall()
    conn.close()

    print("\nKode   | Fasilitas               | Tanggal    | Jam           | Status Booking       | Status Bayar")
    print("-" * 102)
    for r in rows:
        print(
            f"{r['kode_booking']:<6} | {r['nama_fasilitas']:<23} | {r['tanggal']:<10} | "
            f"{r['jam_mulai']}-{r['jam_selesai']:<7} | {r['status_booking']:<20} | {r['status_bayar']}"
        )


def proses_pembayaran(user):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT b.*, f.nama_fasilitas
        FROM booking b
        JOIN fasilitas f ON b.id_fasilitas = f.id
        WHERE b.id_user = ? AND b.status_booking = 'MENUNGGU PEMBAYARAN'
        ORDER BY b.id DESC
        """,
        (user["id"],),
    )
    pending = cur.fetchall()
    if not pending:
        print("\nTidak ada booking yang menunggu pembayaran.")
        conn.close()
        return

    print("\nBooking Menunggu Pembayaran:")
    for r in pending:
        print(f"- {r['kode_booking']} | {r['nama_fasilitas']} | {r['tanggal']} ({r['jam_mulai']}-{r['jam_selesai']}) | Rp {r['total_harga']:,}")

    kode = input("\nMasukkan Kode Booking : ").strip().upper()
    cur.execute("SELECT * FROM booking WHERE kode_booking = ? AND id_user = ?", (kode, user["id"]))
    bk = cur.fetchone()
    if not bk:
        print("Kode booking tidak ditemukan.")
        conn.close()
        return

    print("\nPilih Metode Pembayaran:")
    print("1. Transfer Bank")
    print("2. Bayar di Tempat")
    pilih = input("Pilihan (1/2) : ").strip()

    tgl_bayar = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
    if pilih == "1":
        bank = input("Nama Bank        : ").strip()
        ref = input("Nomor Referensi : ").strip()
        if not bank or not ref:
            print("Nama bank dan nomor referensi wajib diisi.")
            conn.close()
            return
        cur.execute(
            "INSERT INTO pembayaran (id_booking, metode, referensi, tanggal_bayar) VALUES (?, ?, ?, ?)",
            (bk["id"], f"Transfer Bank ({bank})", ref, tgl_bayar),
        )
        cur.execute(
            "UPDATE booking SET status_booking = 'MENUNGGU VERIFIKASI', status_bayar = 'MENUNGGU VERIFIKASI' WHERE id = ?",
            (bk["id"],),
        )
        print("Pembayaran tercatat. Status: MENUNGGU VERIFIKASI")
    elif pilih == "2":
        cur.execute(
            "INSERT INTO pembayaran (id_booking, metode, referensi, tanggal_bayar) VALUES (?, ?, ?, ?)",
            (bk["id"], "Bayar di Tempat", "CASH-ON-SITE", tgl_bayar),
        )
        cur.execute(
            "UPDATE booking SET status_bayar = 'BELUM LUNAS' WHERE id = ?",
            (bk["id"],),
        )
        print("Metode Bayar di Tempat dipilih. Status Bayar: BELUM LUNAS")
    else:
        print("Pilihan tidak valid.")

    conn.commit()
    conn.close()


def notifikasi_jadwal_penggunaan(user):
    hari_ini = datetime.datetime.now().strftime("%d-%m-%Y")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT b.kode_booking, f.nama_fasilitas, b.tanggal, b.jam_mulai, b.jam_selesai, b.status_booking
        FROM booking b
        JOIN fasilitas f ON b.id_fasilitas = f.id
        WHERE b.id_user = ?
          AND b.status_booking IN ('MENUNGGU PEMBAYARAN', 'MENUNGGU VERIFIKASI', 'LUNAS')
        ORDER BY b.tanggal ASC, b.jam_mulai ASC
        """,
        (user["id"],),
    )
    rows = cur.fetchall()
    conn.close()

    print("\n=== NOTIFIKASI JADWAL PENGGUNAAN ===")
    if not rows:
        print("Tidak ada jadwal aktif yang perlu dinotifikasi.")
        return

    for r in rows:
        label = "[HARI INI]" if r["tanggal"] == hari_ini else "[TERJADWAL]"
        print(
            f"{label} {r['kode_booking']} | {r['nama_fasilitas']} | "
            f"{r['tanggal']} pukul {r['jam_mulai']}-{r['jam_selesai']} | Status: {r['status_booking']}"
        )


def kelola_fasilitas():
    while True:
        print("\n--- KELOLA FASILITAS ---")
        print("1. Lihat Fasilitas")
        print("2. Tambah Fasilitas")
        print("3. Ubah Harga Fasilitas")
        print("4. Hapus Fasilitas")
        print("5. Kembali")
        pil = input("Pilih : ").strip()

        conn = get_conn()
        cur = conn.cursor()
        if pil == "1":
            conn.close()
            lihat_fasilitas()
        elif pil == "2":
            nama = input("Nama Fasilitas : ").strip()
            jenis = input("Jenis (Olahraga/Coworking) : ").strip()
            try:
                harga = int(input("Harga per Jam : ").strip())
                cur.execute(
                    "INSERT INTO fasilitas (nama_fasilitas, jenis, harga_per_jam) VALUES (?, ?, ?)",
                    (nama, jenis, harga),
                )
                conn.commit()
                print("Fasilitas ditambahkan.")
            except ValueError:
                print("Harga harus berupa angka.")
            conn.close()
        elif pil == "3":
            conn.close()
            lihat_fasilitas()
            conn = get_conn()
            cur = conn.cursor()
            try:
                idf = int(input("ID Fasilitas : ").strip())
                harga_baru = int(input("Harga Baru per Jam : ").strip())
                cur.execute("UPDATE fasilitas SET harga_per_jam = ? WHERE id = ?", (harga_baru, idf))
                conn.commit()
                print("Harga diperbarui.")
            except ValueError:
                print("Input harus berupa angka.")
            conn.close()
        elif pil == "4":
            conn.close()
            lihat_fasilitas()
            conn = get_conn()
            cur = conn.cursor()
            try:
                idf = int(input("ID Fasilitas yang dihapus : ").strip())
                cur.execute("DELETE FROM fasilitas WHERE id = ?", (idf,))
                conn.commit()
                print("Fasilitas dihapus.")
            except ValueError:
                print("ID harus berupa angka.")
            conn.close()
        elif pil == "5":
            conn.close()
            break
        else:
            conn.close()
            print("Pilihan tidak valid.")


def lihat_semua_booking():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT b.*, f.nama_fasilitas
        FROM booking b
        JOIN fasilitas f ON b.id_fasilitas = f.id
        ORDER BY b.id DESC
        """
    )
    rows = cur.fetchall()
    conn.close()

    print("\nKode   | Penyewa         | Fasilitas          | Tanggal    | Jam         | Status Booking       | Status Bayar")
    print("-" * 112)
    for r in rows:
        print(
            f"{r['kode_booking']:<6} | {r['nama_penyewa']:<15} | {r['nama_fasilitas']:<18} | "
            f"{r['tanggal']:<10} | {r['jam_mulai']}-{r['jam_selesai']:<5} | {r['status_booking']:<20} | {r['status_bayar']}"
        )


def validasi_pembayaran():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT b.kode_booking, b.nama_penyewa, b.total_harga, b.status_booking, p.metode, p.referensi
        FROM booking b
        LEFT JOIN pembayaran p ON p.id = (
            SELECT id FROM pembayaran WHERE id_booking = b.id ORDER BY id DESC LIMIT 1
        )
        WHERE b.status_booking = 'MENUNGGU VERIFIKASI'
        """
    )
    rows = cur.fetchall()
    if not rows:
        print("\nTidak ada pembayaran yang menunggu verifikasi.")
        conn.close()
        return

    print("\nKode   | Penyewa         | Total      | Metode               | Referensi")
    print("-" * 78)
    for r in rows:
        print(f"{r['kode_booking']:<6} | {r['nama_penyewa']:<15} | Rp {r['total_harga']:<7,} | {str(r['metode']):<20} | {r['referensi']}")

    kode = input("\nMasukkan Kode Booking : ").strip().upper()
    cur.execute("SELECT * FROM booking WHERE kode_booking = ?", (kode,))
    bk = cur.fetchone()
    if not bk:
        print("Kode booking tidak ditemukan.")
        conn.close()
        return

    print("1. LUNAS")
    print("2. DITOLAK")
    aksi = input("Pilih (1/2) : ").strip()
    if aksi == "1":
        cur.execute("UPDATE booking SET status_booking = 'LUNAS', status_bayar = 'LUNAS' WHERE id = ?", (bk["id"],))
        print("Pembayaran divalidasi: LUNAS.")
    elif aksi == "2":
        cur.execute("UPDATE booking SET status_booking = 'DITOLAK', status_bayar = 'DITOLAK' WHERE id = ?", (bk["id"],))
        print("Pembayaran ditolak: DITOLAK.")
    else:
        print("Pilihan tidak valid.")

    conn.commit()
    conn.close()


def batalkan_booking():
    lihat_semua_booking()
    kode = input("\nMasukkan Kode Booking yang dibatalkan : ").strip().upper()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM booking WHERE kode_booking = ?", (kode,))
    bk = cur.fetchone()
    if not bk:
        print("Kode booking tidak ditemukan.")
        conn.close()
        return

    if bk["status_booking"] in ("DIBATALKAN", "SELESAI"):
        print(f"Booking sudah berstatus {bk['status_booking']}.")
    else:
        cur.execute("UPDATE booking SET status_booking = 'DIBATALKAN' WHERE id = ?", (bk["id"],))
        conn.commit()
        print(f"Booking {kode} berhasil dibatalkan.")
    conn.close()


def laporan_penggunaan():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) AS total FROM booking")
    total_booking = cur.fetchone()["total"]

    cur.execute(
        "SELECT COUNT(*) AS aktif FROM booking WHERE status_booking IN ('MENUNGGU PEMBAYARAN', 'MENUNGGU VERIFIKASI', 'LUNAS')"
    )
    booking_aktif = cur.fetchone()["aktif"]

    cur.execute("SELECT COUNT(*) AS selesai FROM booking WHERE status_booking = 'SELESAI'")
    booking_selesai = cur.fetchone()["selesai"]

    cur.execute(
        "SELECT COALESCE(SUM(total_harga), 0) AS pendapatan FROM booking WHERE status_booking IN ('LUNAS', 'SELESAI')"
    )
    total_pendapatan = cur.fetchone()["pendapatan"]

    cur.execute(
        """
        SELECT f.nama_fasilitas, COUNT(b.id) AS jml
        FROM fasilitas f
        LEFT JOIN booking b ON f.id = b.id_fasilitas AND b.status_booking NOT IN ('DIBATALKAN', 'DITOLAK')
        GROUP BY f.id
        ORDER BY jml DESC, f.id ASC
        LIMIT 1
        """
    )
    pop = cur.fetchone()
    conn.close()

    print("\n=== LAPORAN PENGGUNAAN SPACE-BOOK ===")
    print(f"Total Booking     : {total_booking} Booking")
    print(f"Booking Aktif     : {booking_aktif} Booking")
    print(f"Booking Selesai   : {booking_selesai} Booking")
    print(f"Total Pendapatan  : Rp {total_pendapatan:,}")
    if pop:
        print(f"Fasilitas Terpopuler : {pop['nama_fasilitas']} ({pop['jml']} Booking)")


def menu_admin(user):
    while True:
        print("\n===== DASHBOARD ADMIN =====")
        print("1. Kelola Fasilitas")
        print("2. Lihat Booking")
        print("3. Validasi Pembayaran")
        print("4. Batalkan Booking")
        print("5. Laporan")
        print("6. Logout")
        pil = input("Pilih menu : ").strip()

        if pil == "1":
            kelola_fasilitas()
        elif pil == "2":
            lihat_semua_booking()
        elif pil == "3":
            validasi_pembayaran()
        elif pil == "4":
            batalkan_booking()
        elif pil == "5":
            laporan_penggunaan()
        elif pil == "6":
            print("Logout berhasil.")
            break
        else:
            print("Pilihan tidak valid.")


def menu_user(user):
    notifikasi_jadwal_penggunaan(user)
    while True:
        print("\n===== SPACE BOOK =====")
        print("1. Lihat Fasilitas")
        print("2. Cek Ketersediaan Jadwal")
        print("3. Booking Fasilitas")
        print("4. Riwayat Booking")
        print("5. Pembayaran")
        print("6. Notifikasi Jadwal Penggunaan")
        print("7. Logout")
        pil = input("Pilih menu : ").strip()

        if pil == "1":
            lihat_fasilitas()
        elif pil == "2":
            cek_ketersediaan()
        elif pil == "3":
            buat_booking(user)
        elif pil == "4":
            riwayat_booking(user)
        elif pil == "5":
            proses_pembayaran(user)
        elif pil == "6":
            notifikasi_jadwal_penggunaan(user)
        elif pil == "7":
            print("Logout berhasil.")
            break
        else:
            print("Pilihan tidak valid.")


def main():
    init_db()
    while True:
        print("\n=== SELAMAT DATANG DI SPACE-BOOK ===")
        print("1. Login")
        print("2. Registrasi User")
        print("3. Keluar")
        pil = input("Pilih menu : ").strip()

        if pil == "1":
            akun = login_akun()
            if akun:
                if akun["role"] == "admin":
                    menu_admin(akun)
                else:
                    menu_user(akun)
        elif pil == "2":
            registrasi_user()
        elif pil == "3":
            print("Terima kasih telah menggunakan SPACE-BOOK.")
            break
        else:
            print("Pilihan tidak valid.")


if __name__ == "__main__":
    main()
