"""Studio GH — Blog & admin.

Single-file Flask app: public feed + article pages, password-protected admin
for CRUD on articles with WYSIWYG editor and local image uploads.
"""
from __future__ import annotations

import os
import re
import secrets
import sqlite3
import unicodedata
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path

import bleach
from dotenv import load_dotenv
from flask import (
    Flask,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf
from PIL import Image
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "instance" / "blog.db"
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
ALLOWED_EXT = {"png", "jpg", "jpeg", "webp", "gif"}
ALLOWED_MIME = {"image/png", "image/jpeg", "image/webp", "image/gif"}
MAX_UPLOAD = 8 * 1024 * 1024  # 8 MB

# HTML allowed out of the WYSIWYG editor. Anything else is stripped.
ALLOWED_TAGS = [
    "p", "br", "strong", "em", "u", "s", "blockquote", "h2", "h3", "h4",
    "ul", "ol", "li", "a", "img", "figure", "figcaption", "hr", "pre", "code",
    "span",
]
ALLOWED_ATTRS = {
    "a": ["href", "title", "target", "rel"],
    "img": ["src", "alt"],
    "span": ["class"],
    "*": ["class"],
}
ALLOWED_PROTOCOLS = ["http", "https", "mailto"]


def get_secret_key() -> str:
    key = os.environ.get("SECRET_KEY")
    if not key:
        # Stable fallback for dev so sessions survive reloads; set SECRET_KEY in prod.
        key = "dev-only-change-me-" + secrets.token_hex(8)
    return key


app = Flask(__name__)
app.config.update(
    SECRET_KEY=get_secret_key(),
    MAX_CONTENT_LENGTH=MAX_UPLOAD,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("FLASK_ENV") == "production",
    PERMANENT_SESSION_LIFETIME=60 * 60 * 8,
)
csrf = CSRFProtect(app)

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------- #
# Database
# --------------------------------------------------------------------------- #
def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_exc: BaseException | None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    db = sqlite3.connect(DB_PATH)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS articles (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT    NOT NULL,
            slug        TEXT    NOT NULL UNIQUE,
            excerpt     TEXT    NOT NULL DEFAULT '',
            body        TEXT    NOT NULL DEFAULT '',
            cover       TEXT,
            published   INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT    NOT NULL,
            updated_at  TEXT    NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_articles_pub
            ON articles (published, created_at DESC);
        """
    )
    db.commit()
    db.close()


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    value = re.sub(r"[-\s]+", "-", value)
    return value or "clanek"


def unique_slug(base: str, exclude_id: int | None = None) -> str:
    db = get_db()
    slug = base
    i = 2
    while True:
        row = db.execute(
            "SELECT id FROM articles WHERE slug = ? AND id IS NOT ?",
            (slug, exclude_id),
        ).fetchone()
        if row is None:
            return slug
        slug = f"{base}-{i}"
        i += 1


def sanitize_html(raw: str) -> str:
    cleaned = bleach.clean(
        raw or "",
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )
    # Force safe rel on external links.
    return cleaned.replace("<a ", '<a rel="noopener noreferrer" ')


def strip_tags(html: str) -> str:
    return re.sub(r"\s+", " ", bleach.clean(html or "", tags=[], strip=True)).strip()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


@app.context_processor
def inject_globals():
    return {"csrf_token": generate_csrf, "current_year": datetime.now().year}


# --------------------------------------------------------------------------- #
# Rate limiting (in-memory, login only)
# --------------------------------------------------------------------------- #
_login_attempts: dict[str, list[float]] = {}
RATE_WINDOW = 300  # 5 min
RATE_MAX = 8


def rate_limited(ip: str) -> bool:
    now = datetime.now(timezone.utc).timestamp()
    attempts = [t for t in _login_attempts.get(ip, []) if now - t < RATE_WINDOW]
    _login_attempts[ip] = attempts
    return len(attempts) >= RATE_MAX


def record_attempt(ip: str) -> None:
    _login_attempts.setdefault(ip, []).append(
        datetime.now(timezone.utc).timestamp()
    )


# --------------------------------------------------------------------------- #
# Public routes
# --------------------------------------------------------------------------- #
@app.route("/")
def feed():
    db = get_db()
    articles = db.execute(
        "SELECT * FROM articles WHERE published = 1 ORDER BY created_at DESC"
    ).fetchall()
    return render_template("feed.html", articles=articles)


@app.route("/clanek/<slug>")
def article(slug: str):
    db = get_db()
    row = db.execute(
        "SELECT * FROM articles WHERE slug = ? AND published = 1", (slug,)
    ).fetchone()
    if row is None:
        abort(404)
    return render_template("article.html", a=row)


# --------------------------------------------------------------------------- #
# Auth
# --------------------------------------------------------------------------- #
@app.route("/admin/login", methods=["GET", "POST"])
def login():
    if session.get("admin"):
        return redirect(url_for("admin"))

    if request.method == "POST":
        ip = request.remote_addr or "unknown"
        if rate_limited(ip):
            flash("Příliš mnoho pokusů. Zkuste to za pár minut.", "error")
            return render_template("login.html"), 429

        password = request.form.get("password", "")
        pw_hash = os.environ.get("ADMIN_PASSWORD_HASH")
        plain = os.environ.get("ADMIN_PASSWORD")

        ok = False
        if pw_hash:
            ok = check_password_hash(pw_hash, password)
        elif plain:
            ok = secrets.compare_digest(plain, password)

        if ok:
            session.clear()
            session["admin"] = True
            session.permanent = True
            nxt = request.args.get("next", "")
            if nxt and nxt.startswith("/admin"):
                return redirect(nxt)
            return redirect(url_for("admin"))

        record_attempt(ip)
        flash("Nesprávné heslo.", "error")

    return render_template("login.html")


@app.route("/admin/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    return redirect(url_for("feed"))


# --------------------------------------------------------------------------- #
# Admin
# --------------------------------------------------------------------------- #
@app.route("/admin")
@login_required
def admin():
    db = get_db()
    articles = db.execute(
        "SELECT * FROM articles ORDER BY updated_at DESC"
    ).fetchall()
    return render_template("admin/list.html", articles=articles)


@app.route("/admin/new", methods=["GET", "POST"])
@login_required
def admin_new():
    if request.method == "POST":
        return _save_article(None)
    return render_template("admin/edit.html", a=None)


@app.route("/admin/edit/<int:aid>", methods=["GET", "POST"])
@login_required
def admin_edit(aid: int):
    db = get_db()
    row = db.execute("SELECT * FROM articles WHERE id = ?", (aid,)).fetchone()
    if row is None:
        abort(404)
    if request.method == "POST":
        return _save_article(aid)
    return render_template("admin/edit.html", a=row)


def _save_article(aid: int | None):
    db = get_db()
    title = (request.form.get("title") or "").strip()
    if not title:
        flash("Titulek je povinný.", "error")
        return redirect(request.url)

    body = sanitize_html(request.form.get("body", ""))
    excerpt = (request.form.get("excerpt") or "").strip()
    if not excerpt:
        excerpt = strip_tags(body)[:200]
    published = 1 if request.form.get("published") == "on" else 0

    cover = request.form.get("cover_existing") or None
    file = request.files.get("cover")
    if file and file.filename:
        saved = _save_image(file)
        if saved:
            cover = saved

    ts = now_iso()
    if aid is None:
        slug = unique_slug(slugify(title))
        db.execute(
            """INSERT INTO articles
               (title, slug, excerpt, body, cover, published, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (title, slug, excerpt, body, cover, published, ts, ts),
        )
        flash("Článek vytvořen.", "ok")
    else:
        existing = db.execute(
            "SELECT slug FROM articles WHERE id = ?", (aid,)
        ).fetchone()
        slug = existing["slug"]
        db.execute(
            """UPDATE articles
               SET title=?, excerpt=?, body=?, cover=?, published=?, updated_at=?
               WHERE id=?""",
            (title, excerpt, body, cover, published, ts, aid),
        )
        flash("Článek uložen.", "ok")
    db.commit()
    return redirect(url_for("admin"))


@app.route("/admin/delete/<int:aid>", methods=["POST"])
@login_required
def admin_delete(aid: int):
    db = get_db()
    db.execute("DELETE FROM articles WHERE id = ?", (aid,))
    db.commit()
    flash("Článek smazán.", "ok")
    return redirect(url_for("admin"))


# --------------------------------------------------------------------------- #
# Image upload (used by editor + cover). Re-encodes to strip metadata/payloads.
# --------------------------------------------------------------------------- #
def _save_image(file) -> str | None:
    filename = secure_filename(file.filename or "")
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXT:
        return None
    if file.mimetype not in ALLOWED_MIME:
        return None

    try:
        img = Image.open(file.stream)
        img.verify()  # detect truncated/forged files
        file.stream.seek(0)
        img = Image.open(file.stream)
    except Exception:
        return None

    out_ext = "jpg" if ext in {"jpg", "jpeg"} else ext
    name = f"{secrets.token_hex(16)}.{out_ext}"
    dest = UPLOAD_DIR / name

    save_kwargs = {}
    fmt = "JPEG" if out_ext == "jpg" else out_ext.upper()
    if fmt == "JPEG" and img.mode in {"RGBA", "P"}:
        img = img.convert("RGB")
    if fmt == "JPEG":
        save_kwargs = {"quality": 85, "optimize": True}

    # Cap dimensions to keep files sane.
    img.thumbnail((2000, 2000))
    img.save(dest, fmt, **save_kwargs)
    return name


@app.route("/admin/upload", methods=["POST"])
@login_required
def admin_upload():
    """AJAX endpoint for the WYSIWYG editor's inline images."""
    file = request.files.get("image")
    if not file:
        return {"error": "no file"}, 400
    saved = _save_image(file)
    if not saved:
        return {"error": "invalid image"}, 400
    return {"url": url_for("static", filename=f"uploads/{saved}")}


@app.errorhandler(404)
def not_found(_e):
    return render_template("404.html"), 404


@app.errorhandler(413)
def too_large(_e):
    flash("Soubor je příliš velký (max 8 MB).", "error")
    return redirect(request.referrer or url_for("admin")), 413


if __name__ == "__main__":
    init_db()
    app.run(debug=os.environ.get("FLASK_ENV") != "production", port=5000)