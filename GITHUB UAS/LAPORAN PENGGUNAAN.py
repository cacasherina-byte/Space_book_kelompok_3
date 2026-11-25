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
