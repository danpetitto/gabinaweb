"""Interaktivně vygeneruje bezpečný hash admin hesla.

Spuštění:  python set_password.py
Výstup vložte do .env jako ADMIN_PASSWORD_HASH=...
"""
import getpass

from werkzeug.security import generate_password_hash


def main() -> None:
    pw1 = getpass.getpass("Nové admin heslo: ")
    if len(pw1) < 8:
        print("Heslo musí mít aspoň 8 znaků.")
        return
    pw2 = getpass.getpass("Heslo znovu: ")
    if pw1 != pw2:
        print("Hesla se neshodují.")
        return

    pw_hash = generate_password_hash(pw1)
    print("\nVložte tento řádek do .env:\n")
    print(f"ADMIN_PASSWORD_HASH={pw_hash}")


if __name__ == "__main__":
    main()
