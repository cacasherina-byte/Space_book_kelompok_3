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