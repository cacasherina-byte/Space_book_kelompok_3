#KELOLA FAASILITAS
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