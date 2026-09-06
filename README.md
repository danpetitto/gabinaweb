# Studio GH — web + blog

Statické stránky (HTML/CSS/JS) + blog s adminem (Flask + SQLite), vše servíruje
jedna Flask aplikace. Deploy na Railway jedním pushem na `main`.

## Struktura

```
app.py                        Flask — servíruje statické stránky + blog + admin
index.html, o-mne.html, …     statické stránky webu (kořen repa)
templates/                    šablony blogu (feed, článek, login, admin)
css/styles.css                design system webu
css/blog.css                  styly blogu (načítá se po styles.css)
js/main.js                    header, mobilní menu, scroll reveal
js/cookie-consent.js          cookie lišta (GA4 Consent Mode v2)
js/editor.js                  Quill editor v adminu
static/                       obrázky a PDF webu
instance/                     SQLite + uploady (negitováno; v produkci BLOG_DATA_DIR)
```

## URL

- `/` a `/<stranka>.html` — statické stránky
- `/pro-klientky` — blog (feed), `/pro-klientky/<slug>` — článek
- `/admin` — správa článků (heslo), `/uploads/<soubor>` — nahrané obrázky

## Lokální spuštění

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env               # doplň SECRET_KEY a ADMIN_PASSWORD(_HASH)
flask --app app run                # http://localhost:5000
```

## Produkce (Railway)

Start příkaz je v `railway.json` (gunicorn). V Railway nastav proměnné:

- `SECRET_KEY` — `python3 -c "import secrets; print(secrets.token_hex(32))"`
- `ADMIN_PASSWORD_HASH` — `python3 set_password.py` (nebo dočasně `ADMIN_PASSWORD`)
- `FLASK_ENV=production`
- `BLOG_DATA_DIR=/data` + **volume mountnutý na `/data`** — jinak se články
  a nahrané fotky ztratí při každém redeployi!

## Barvy

| Token | HEX | Použití |
|---|---|---|
| accent | #D7B387 | tlačítka hover, čísla |
| ink | #544A4A | hlavní text |
| cloud | #FAF6F0 | pozadí |
| paper | #F2E9DD | druhé pozadí |
| sand | #E8DAC8 | linky |
| smoke | #8A7E78 | sekundární text |
| wine | #6E3B3B | patička |

Vše je v `:root` v `css/styles.css` — změníš na jednom místě.
