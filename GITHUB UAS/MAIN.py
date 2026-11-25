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
