#!/usr/bin/env python3
"""
quickpost/app.py — tiny mobile-friendly form for posting a new blog entry,
or adding a quick update (photo/video/audio + comment) to an existing
post, straight from your phone.

Meant to run as a small, always-on service behind Apache, reachable only
at an obscure/authenticated path — e.g. Apache reverse-proxies
/quickpost/ to this app, and an Apache <Location> block requires HTTP
Basic Auth before requests ever reach Flask. See README.md for the
Apache config snippet.

After saving, it runs build.py so the live site updates immediately.
"""

import subprocess
import re
import sys
from datetime import date, datetime
from pathlib import Path

from flask import Flask, request, render_template, redirect, url_for, flash
from PIL import Image, ImageOps

BASE = Path(__file__).resolve().parent.parent  # .../site/
POSTS_DIR = BASE / "posts"
UPLOADS_DIR = BASE / "static" / "uploads"
BUILD_SCRIPT = BASE / "build.py"
VENV_PYTHON = BASE / "venv" / "bin" / "python3"

# Reuse build.py's own post-parsing logic, theme list, and media-type
# detection directly, rather than duplicating them — so the two files
# can't drift out of sync.
sys.path.insert(0, str(BASE))
from build import load_posts, THEMES, detect_media_type  # noqa: E402

MAX_IMAGE_DIM = 1600  # px, longest side — keeps phone photos from being huge

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

# Safety net: stops a huge accidental upload from filling the server's
# disk before ffmpeg even gets a chance to compress it down.
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500 MB


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:60]


def save_and_resize_image(file_storage, filename_stem):
    """Save an uploaded photo, downscale it, strip EXIF, return the relative path."""
    dest = UPLOADS_DIR / f"{filename_stem}.jpg"

    img = Image.open(file_storage.stream)
    img = ImageOps.exif_transpose(img)  # rotate pixels to match how the phone was actually held
    img = img.convert("RGB")  # then safe to drop EXIF/alpha, normalize format

    img.thumbnail((MAX_IMAGE_DIM, MAX_IMAGE_DIM))
    img.save(dest, "JPEG", quality=82)

    return f"static/uploads/{filename_stem}.jpg"


def compress_video(file_storage, filename_stem):
    """Save an uploaded video, transcoding it to a compressed, universally
    playable H.264 mp4 capped at 1280px wide (smaller videos aren't
    upscaled). Always outputs .mp4 regardless of the source format."""
    tmp_path = UPLOADS_DIR / f"_incoming_{filename_stem}{Path(file_storage.filename).suffix}"
    dest = UPLOADS_DIR / f"{filename_stem}.mp4"
    file_storage.save(tmp_path)

    result = subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(tmp_path),
            "-vf", "scale='min(1280,iw)':'-2'",  # cap width at 1280px, never upscale
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",  # lets the video start playing before it's fully downloaded
            str(dest),
        ],
        capture_output=True, text=True,
    )

    tmp_path.unlink(missing_ok=True)  # remove the original upload either way

    if result.returncode != 0:
        raise RuntimeError(f"Video compression failed: {result.stderr[-400:]}")

    return f"static/uploads/{filename_stem}.mp4"


def save_media(file_storage, filename_stem):
    """Save an uploaded photo, video, or audio file, dispatching by type.

    Images are resized; video is compressed via ffmpeg; audio is stored
    as uploaded (already small, no compatibility issues to fix). Returns
    (relative_path, media_type). Raises RuntimeError if video compression
    fails (e.g. ffmpeg isn't installed) — callers should catch this.
    """
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    media_type = detect_media_type(file_storage.filename)

    if media_type == "image":
        return save_and_resize_image(file_storage, filename_stem), "image"

    if media_type == "video":
        return compress_video(file_storage, filename_stem), "video"

    # audio — store as-is
    ext = Path(file_storage.filename).suffix.lower()
    dest = UPLOADS_DIR / f"{filename_stem}{ext}"
    file_storage.save(dest)
    return f"static/uploads/{filename_stem}{ext}", "audio"


def media_markdown(relative_path, media_type):
    """Return the Markdown/HTML snippet to embed a piece of media inline
    in a post body. Images use standard Markdown syntax; video/audio use
    raw HTML, which Python-Markdown passes through untouched."""
    # ../ because posts live one folder deeper than static/ on the live site
    src = f"../{relative_path}"
    if media_type == "video":
        return f'<video class="post-media" src="{src}" controls preload="metadata"></video>\n\n'
    if media_type == "audio":
        return f'<audio class="post-audio" src="{src}" controls preload="metadata"></audio>\n\n'
    return f"![]({src})\n\n"


def get_recent_posts():
    """All posts across both categories, newest first."""
    all_posts = load_posts("work") + load_posts("interests")
    all_posts.sort(key=lambda p: p["date"], reverse=True)
    return all_posts


@app.route("/", methods=["GET", "POST"])
def quickpost():
    if request.method == "POST":
        mode = request.form.get("mode", "new")
        if mode == "update":
            return handle_update()
        return handle_new_post()

    return render_quickpost_form()


def render_quickpost_form():
    recent = get_recent_posts()
    recent_json = [
        {
            "key": f"{p['category']}/{p['slug']}",
            "title": p["title"],
            "emoji": p["emoji"],
            "date_iso": p["date"].strftime("%Y-%m-%d"),
            "date_display": p["date"].strftime("%d %b"),
        }
        for p in recent
    ]
    return render_template(
        "quickpost.html",
        themes=THEMES,
        recent_posts=recent_json,
        today=date.today().isoformat(),
    )


def handle_new_post():
    category = request.form["category"]  # "work" or "interests"
    theme = request.form["theme"]
    title = request.form["title"].strip()
    body = request.form["body"].strip()
    tags = [t.strip() for t in request.form.get("tags", "").split(",") if t.strip()]

    if theme not in THEMES.get(category, []):
        flash(f"'{theme}' isn't a valid theme for {category}.")
        return redirect(url_for("quickpost"))

    if not title or not body:
        flash("Title and body are required for a new post.")
        return redirect(url_for("quickpost"))

    emoji = request.form.get("emoji", "").strip() or THEME_EMOJI.get(theme, "📝")

    slug = slugify(title)
    today = date.today().isoformat()
    filename = f"{today}-{slug}.md"

    media_line = ""
    media_file = request.files.get("media")
    if media_file and media_file.filename:
        try:
            media_path, _media_type = save_media(media_file, slug)
            media_line = f"media: {media_path}\n"
        except RuntimeError as e:
            flash(f"Couldn't process that file, post not saved: {e}")
            return redirect(url_for("quickpost"))

    tags_yaml = "[" + ", ".join(tags) + "]" if tags else "[]"

    frontmatter = (
        "---\n"
        f"title: \"{title}\"\n"
        f"date: {today}\n"
        f"emoji: {emoji}\n"
        f"theme: {theme}\n"
        f"tags: {tags_yaml}\n"
        f"{media_line}"
        "---\n\n"
    )

    post_path = POSTS_DIR / category / filename
    post_path.parent.mkdir(parents=True, exist_ok=True)
    post_path.write_text(frontmatter + body + "\n", encoding="utf-8")

    return rebuild_and_redirect("Posted and site rebuilt ✅")


def handle_update():
    existing_key = request.form.get("existing_post", "")
    comment = request.form.get("comment", "").strip()

    if "/" not in existing_key:
        flash("Pick a post to update.")
        return redirect(url_for("quickpost"))

    category, slug = existing_key.split("/", 1)

    # Look the post up the same way build.py does, so we get its real file
    # path regardless of the date prefix in the filename.
    matches = [p for p in load_posts(category) if p["slug"] == slug]
    if not matches:
        flash("Couldn't find that post — it may have been renamed or removed.")
        return redirect(url_for("quickpost"))

    post_path = matches[0]["path"]

    media_file = request.files.get("update_media")
    has_media = bool(media_file and media_file.filename)

    if not comment and not has_media:
        flash("Add a photo/video/audio clip, a comment, or both.")
        return redirect(url_for("quickpost"))

    media_html = ""
    if has_media:
        timestamp = datetime.now().strftime("%H%M%S")
        try:
            media_path, media_type = save_media(media_file, f"{slug}-{timestamp}")
            media_html = media_markdown(media_path, media_type)
        except RuntimeError as e:
            flash(f"Couldn't process that file, update not saved: {e}")
            return redirect(url_for("quickpost"))

    time_label = datetime.now().strftime("%H:%M")
    addition = f"\n\n---\n\n*{time_label}*\n\n{media_html}{comment}\n"

    with post_path.open("a", encoding="utf-8") as f:
        f.write(addition)

    return rebuild_and_redirect("Update added ✅")


def rebuild_and_redirect(success_message):
    result = subprocess.run(
        [str(VENV_PYTHON), str(BUILD_SCRIPT)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        flash(f"Saved, but the build failed: {result.stderr[-300:]}")
    else:
        flash(success_message)
    return redirect(url_for("quickpost"))


if __name__ == "__main__":
    # For local testing only. In production this runs behind gunicorn + Apache.
    app.run(host="127.0.0.1", port=5001, debug=False)