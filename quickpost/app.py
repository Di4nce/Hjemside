#!/usr/bin/env python3
"""
quickpost/app.py — tiny mobile-friendly form for posting a new blog entry
(with an optional photo) straight from your phone.

Meant to run as a small, always-on service behind Apache, reachable only
at an obscure/authenticated path — e.g. Apache reverse-proxies
/quickpost/ to this app, and an Apache <Location> block requires HTTP
Basic Auth before requests ever reach Flask. See README.md for the
Apache config snippet.

After saving a post, it runs build.py so the live site updates
immediately — no separate step needed once you're back at a computer.
"""

import subprocess
import re
from datetime import date
from pathlib import Path

from flask import Flask, request, render_template, redirect, url_for, flash
from PIL import Image
from PIL.ExifTags import TAGS

BASE = Path(__file__).resolve().parent.parent  # .../site/
POSTS_DIR = BASE / "posts"
UPLOADS_DIR = BASE / "static" / "uploads"
BUILD_SCRIPT = BASE / "build.py"

MAX_IMAGE_DIM = 1600  # px, longest side — keeps phone photos from being huge

app = Flask(__name__)
app.secret_key = "change-this-to-something-random"  # only used for flash messages


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:60]


def save_and_resize_image(file_storage, slug):
    """Save an uploaded photo, downscale it, strip EXIF, return the relative path."""
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    dest = UPLOADS_DIR / f"{slug}.jpg"

    img = Image.open(file_storage.stream)
    img = img.convert("RGB")  # drops EXIF/alpha, normalizes format

    img.thumbnail((MAX_IMAGE_DIM, MAX_IMAGE_DIM))
    img.save(dest, "JPEG", quality=82)

    return f"static/uploads/{slug}.jpg"


@app.route("/", methods=["GET", "POST"])
def quickpost():
    if request.method == "POST":
        category = request.form["category"]  # "work" or "interests"
        title = request.form["title"].strip()
        body = request.form["body"].strip()
        tags = [t.strip() for t in request.form.get("tags", "").split(",") if t.strip()]
        emoji = request.form.get("emoji", "").strip() or ("🎲" if category == "interests" else "🛡️")

        if not title or not body:
            flash("Title and body are required.")
            return redirect(url_for("quickpost"))

        slug = slugify(title)
        today = date.today().isoformat()
        filename = f"{today}-{slug}.md"

        image_line = ""
        photo = request.files.get("photo")
        if photo and photo.filename:
            image_path = save_and_resize_image(photo, slug)
            image_line = f"image: {image_path}\n"

        tags_yaml = "[" + ", ".join(tags) + "]" if tags else "[]"

        frontmatter = (
            "---\n"
            f"title: \"{title}\"\n"
            f"date: {today}\n"
            f"emoji: {emoji}\n"
            f"tags: {tags_yaml}\n"
            f"{image_line}"
            "---\n\n"
        )

        post_path = POSTS_DIR / category / filename
        post_path.parent.mkdir(parents=True, exist_ok=True)
        post_path.write_text(frontmatter + body + "\n", encoding="utf-8")

        # Rebuild the static site immediately so the post goes live now.
        result = subprocess.run(
            ["python3", str(BUILD_SCRIPT)],
            capture_output=True, text=True,
        )

        if result.returncode != 0:
            flash(f"Post saved, but the build failed: {result.stderr[-300:]}")
        else:
            flash("Posted and site rebuilt ✅")

        return redirect(url_for("quickpost"))

    return render_template("quickpost.html")


if __name__ == "__main__":
    # For local testing only. In production run this behind Apache
    # (mod_wsgi or a reverse proxy to gunicorn) — see README.md.
    app.run(host="127.0.0.1", port=5001, debug=False)
