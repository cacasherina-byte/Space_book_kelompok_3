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