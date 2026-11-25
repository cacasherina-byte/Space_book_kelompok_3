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
