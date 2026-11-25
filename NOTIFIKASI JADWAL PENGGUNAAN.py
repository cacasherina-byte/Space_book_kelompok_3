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
