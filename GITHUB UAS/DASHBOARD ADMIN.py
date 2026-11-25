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

