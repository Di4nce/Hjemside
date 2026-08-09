#!/usr/bin/env python3
"""
build.py — static site generator for lerseth.com

Reads Markdown posts from posts/work/ and posts/interests/,
renders them (and the index/list pages) through Jinja2 templates,
and writes the finished static site to output/.

Usage:
    python3 build.py
"""

import shutil
from pathlib import Path
from datetime import datetime

import frontmatter
import markdown
from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).parent
POSTS_DIR = ROOT / "posts"
TEMPLATES_DIR = ROOT / "templates"
STATIC_DIR = ROOT / "static"
OUTPUT_DIR = ROOT / "output"

CATEGORIES = ["work", "interests"]

# The three fixed themes each section is organized around. These drive
# the filter buttons on work.html / interests.html, and every post must
# declare one of them (see the "theme" field check in load_posts below).
THEMES = {
    "work": ["Information Security", "Quality Management", "Learning"],
    "interests": ["Music", "Tabletop RPGs", "Homelab"],
}

env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))


def load_posts(category):
    """Read every .md file in posts/<category>/ and return a list of post dicts."""
    posts = []
    folder = POSTS_DIR / category

    for md_file in sorted(folder.glob("*.md")):
        post = frontmatter.load(md_file)

        required = ["title", "date", "emoji", "theme"]
        missing = [f for f in required if f not in post.metadata]
        if missing:
            print(f"  ! Skipping {md_file.name}: missing frontmatter field(s) {missing}")
            continue

        theme = post["theme"]
        if theme not in THEMES[category]:
            print(f"  ! Skipping {md_file.name}: theme '{theme}' must be one of {THEMES[category]}")
            continue

        date = post["date"]
        if isinstance(date, str):
            date = datetime.strptime(date, "%Y-%m-%d")
        elif hasattr(date, "year") and not isinstance(date, datetime):
            # frontmatter parses bare YAML dates as datetime.date
            date = datetime(date.year, date.month, date.day)

        body_html = markdown.markdown(post.content, extensions=["extra", "sane_lists"])

        # Slug: filename without the date prefix and extension, e.g.
        # 2026-07-31-terraforming-mars.md -> terraforming-mars
        stem = md_file.stem
        slug = stem[11:] if len(stem) > 11 and stem[10] == "-" else stem

        excerpt = post.metadata.get("excerpt")
        if not excerpt:
            plain = markdown.markdown(post.content)
            # crude strip of tags for a short fallback excerpt
            import re
            plain = re.sub("<[^<]+?>", "", plain)
            excerpt = (plain[:140] + "…") if len(plain) > 140 else plain

        posts.append({
            "title": post["title"],
            "date": date,
            "emoji": post.get("emoji", ""),
            "theme": theme,
            "tags": post.get("tags", []),  # optional extra labels, just for display
            "image": post.get("image", ""),
            "category": category,
            "slug": slug,
            "excerpt": excerpt,
            "body_html": body_html,
            "path": md_file,  # source file — used by quickpost to append updates
        })

    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


def build():
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)

    # Copy static assets (css, uploaded images) as-is
    shutil.copytree(STATIC_DIR, OUTPUT_DIR / "static")

    all_posts = {cat: load_posts(cat) for cat in CATEGORIES}

    # --- index.html ---
    index_tpl = env.get_template("index.html")
    (OUTPUT_DIR / "index.html").write_text(
        index_tpl.render(
            root="",
            latest_work=all_posts["work"][:3],
            latest_interests=all_posts["interests"][:3],
        ),
        encoding="utf-8",
    )

    # --- work.html / interests.html ---
    list_tpl = env.get_template("list.html")
    titles = {"work": "Work Projects", "interests": "Interests"}

    for cat in CATEGORIES:
        (OUTPUT_DIR / f"{cat}.html").write_text(
            list_tpl.render(
                root="",
                page_title=titles[cat],
                posts=all_posts[cat],
                themes=THEMES[cat],
            ),
            encoding="utf-8",
        )

    # --- individual post pages: output/posts/<slug>.html ---
    (OUTPUT_DIR / "posts").mkdir(exist_ok=True)
    post_tpl = env.get_template("post.html")

    for cat in CATEGORIES:
        for post in all_posts[cat]:
            (OUTPUT_DIR / "posts" / f"{post['slug']}.html").write_text(
                post_tpl.render(root="../", post=post),
                encoding="utf-8",
            )

    total = sum(len(v) for v in all_posts.values())
    print(f"Built {total} post(s) -> {OUTPUT_DIR}/")


if __name__ == "__main__":
    build()