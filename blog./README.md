# Studio GH — Blog

Produkční blog s admin rozhraním. Flask + SQLite + Quill WYSIWYG.

## Funkce

- **Veřejný feed** příspěvků v designu webu Studio GH (Playfair + Jost, sand/paper)
- **Detail článku** s formátovaným obsahem a obrázky
- **Admin** chráněný heslem: tvorba, editace, mazání, koncepty vs. publikováno
- **WYSIWYG editor** (Quill) — tučné, kurzíva, nadpisy, seznamy, citace, odkazy, vkládání fotek klikáním
- **Upload fotek** lokálně (titulní fotka + inline v textu), re-encode přes Pillow (strip metadat/payloadů)

## Bezpečnost

- Heslo v `.env` (hash přes Werkzeug, nebo plaintext pro rychlý start)
- Session-based login, HttpOnly + SameSite cookies, secure v produkci
- CSRF ochrana na všech formech (Flask-WTF)
- HTML z editoru sanitizováno přes **bleach** (whitelist tagů) → žádné XSS
- Uploady: kontrola přípony + MIME + Pillow verify + re-encode, limit 8 MB
- Parametrizované SQL dotazy
- Rate limit na login (8 pokusů / 5 min / IP)

## Instalace

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"   # vlož do .env
python set_password.py             # vygeneruje ADMIN_PASSWORD_HASH, vlož do .env

python app.py                      # http://localhost:5000
```

DB se vytvoří automaticky při startu (`instance/blog.db`).

## Produkce

```bash
FLASK_ENV=production gunicorn -w 2 -b 0.0.0.0:8000 app:app
```

Za reverse proxy (nginx) s HTTPS. `static/uploads/` servíruje přímo nginx.
Pozdější migrace na S3: nahradit `_save_image` / `admin_upload` za upload do bucketu.

## Napojení na hlavní web

Blog běží jako samostatná Flask app. Do navigace hlavního webu přidejte odkaz
na `/` (nebo nasaďte pod subdoménu `blog.studiogh.cz`, případně pod cestu
`/blog` přes reverse proxy).
