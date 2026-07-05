# Studio GH — Skin Balance Method (statický web)

Čistý HTML/CSS/JS web. Žádný build, žádné závislosti.

## Jak rozjet

Otevři `index.html` v prohlížeči. Hotovo.

Pokud chceš lokální server (kvůli relativním cestám se to chová líp):

```bash
# Python
python3 -m http.server 8000
# pak http://localhost:8000

# nebo Node
npx serve
```

## Struktura

```
index.html                    úvodní stránka (10 sekcí dle briefu)
skin-balance-method.html      /skin-balance-method  (text dodá Gabriela)
procedury-cenik.html          /procedury-cenik      (ceník dodá Gabriela)
o-mne.html                    /o-mne                (text dodá Gabriela)
pro-klientky.html             /pro-klientky         (rozcestník)
rezervace.html                /rezervace            (formulář — placeholder)
obchodni-podminky.html        právní
ochrana-osobnich-udaju.html   GDPR
404.html                      chybová stránka
css/styles.css                celý design system
js/main.js                    header, mobilní menu, scroll reveal
```

## Co je potřeba doplnit

- **Fotky** — místo šedých placeholderů (`.ph`) vlož `<img>`. Třída zůstává kvůli poměru stran.
- **Texty podstránek** — dodá Gabriela (SBM, ceník, o mně).
- **E-mail + otevírací doba** — v patičce označeno komentářem `[doplnit]`.
- **Facebook / Messenger odkaz** — zatím `#`.
- **Lead magnet formulář** (sekce 9) a **rezervační formulář** — `action="#"`, napojit na Mailerlite / Webnode / Reservio.
- **Kostky specializací** (sekce 5) zatím nevedou nikam — až budou podstránky, obal je do `<a href="...">`.

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
# gabinaweb
