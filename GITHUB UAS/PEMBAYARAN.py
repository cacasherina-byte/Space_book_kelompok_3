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

