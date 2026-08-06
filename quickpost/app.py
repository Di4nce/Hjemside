#!/usr/bin/env python3
import subprocess
import re
from datetime import date
from pathlib import Path

from flask import Flask, request, render_template, redirect, url_for, flash
from PIL import Image

BASE = Path(__file__).resolve().parent.parent  # .../site/
POSTS_DIR = BASE / "posts"
UPLOADS_DIR = BASE / "static" / "uploads"
BUILD_SCRIPT = BASE / "build.py"
VENV_PYTHON = BASE / "venv" / "bin" / "python3"

MAX_IMAGE_DIM = 1600  # px, longest side — keeps phone photos from being huge

# Same fixed themes as build.py — kept in sync with THEMES there.
THEMES = {
    "work": ["Information Security", "Quality Management", "Learning"],
    "interests": ["Music", "Tabletop RPGs", "Homelab"],
}

THEME_EMOJI = {
    "Information Security": "🛡️",
    "Quality Management": "🔄️",
    "Learning": "🧑‍🏫",
    "Music": "🎸",
    "Tabletop RPGs": "🎲",
    "Homelab": "💻",
}

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
        theme = request.form["theme"]
        title = request.form["title"].strip()
        body = request.form["body"].strip()
        tags = [t.strip() for t in request.form.get("tags", "").split(",") if t.strip()]

        if theme not in THEMES.get(category, []):
            flash(f"'{theme}' isn't a valid theme for {category}.")
            return redirect(url_for("quickpost"))

        emoji = request.form.get("emoji", "").strip() or THEME_EMOJI.get(theme, "📝")

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
            f"theme: {theme}\n"
            f"tags: {tags_yaml}\n"
            f"{image_line}"
            "---\n\n"
        )

        post_path = POSTS_DIR / category / filename
        post_path.parent.mkdir(parents=True, exist_ok=True)
        post_path.write_text(frontmatter + body + "\n", encoding="utf-8")

        # Rebuild the static site immediately so the post goes live now.
        # Uses the venv's Python directly — same lesson as deploy.sh, this
        # process may not have the venv "activated" in its environment.
        result = subprocess.run(
            [str(VENV_PYTHON), str(BUILD_SCRIPT)],
            capture_output=True, text=True,
        )

        if result.returncode != 0:
            flash(f"Post saved, but the build failed: {result.stderr[-300:]}")
        else:
            flash("Posted and site rebuilt ✅")

        return redirect(url_for("quickpost"))

    return render_template("quickpost.html", themes=THEMES)


if __name__ == "__main__":
    # For local testing only. In production run this behind Apache
    # via gunicorn + a reverse proxy — see the step-by-step guide.
    app.run(host="127.0.0.1", port=5001, debug=False)