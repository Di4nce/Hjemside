# Lerseth blog build — integration notes

## What this is

A static-site generator for lerseth.com. It reads Markdown posts, renders
them through Jinja2 templates, and produces a plain HTML/CSS site in
`output/` the only thing Apache needs to serve.

A small optional Flask app (`quickpost/`) gives a mobile-friendly
form to add a new post (with a photo) from phone mid-session; it
writes the Markdown file and re-runs the build.

```
posts/work/*.md          <- your work project posts (source)
posts/interests/*.md     <- your interest/hobby posts (source)
templates/               <- Jinja2 HTML templates
static/styles.css        <- your existing stylesheet, extended
static/uploads/          <- post images end up here
build.py                 <- run this to regenerate the site
output/                  <- generated site — point Apache DocumentRoot here
quickpost/               <- optional mobile "add a post" form
```

## 1. Writing a new post by hand

Create a file like `posts/work/2026-08-05-a-new-post.md`:

```markdown
---
title: "A new post"
date: 2026-08-05
emoji: 🛡️
tags: [Information Security]
image: static/uploads/some-photo.jpg   # optional
excerpt: One-line teaser shown on the card. Optional — auto-generated if omitted.
---

Post body in **Markdown** goes here.
```

Then run:

```bash
python3 build.py
```

and sync/deploy `output/` to your Apache container as usual (rsync,
git push + webhook, etc. — whatever you already use).

## 2. Setting up the mobile quick-post form

This runs as a small always-on Python process, kept behind Apache and
protected with HTTP Basic Auth.

```bash
cd quickpost
pip install -r requirements.txt
python3 app.py     # listens on 127.0.0.1:5001 by default
```

For production, run it under something that keeps it alive
(`systemd` service, or `gunicorn` behind `mod_proxy`), e.g. a
`quickpost.service` unit running:

```
gunicorn -w 1 -b 127.0.0.1:5001 app:app
```

Then in your Apache config, reverse-proxy a path to it **and**
require auth on that path:

```apache
<Location "/quickpost/">
    ProxyPass "http://127.0.0.1:5001/"
    ProxyPassReverse "http://127.0.0.1:5001/"

    AuthType Basic
    AuthName "Quick Post"
    AuthUserFile /etc/apache2/quickpost.htpasswd
    Require valid-user
</Location>
```

Create the password file once:

```bash
htpasswd -c /etc/apache2/quickpost.htpasswd yourusername
```

Now `https://lerseth.com/quickpost/` prompts for a login before it
ever reaches Flask, and from phone you can fill in the form,
attach a photo taken right at the table, and hit "Post it" it saves
the Markdown file, resizes/strips EXIF from the photo, and re-runs
`build.py` automatically so the new post is live immediately.

## 3. Notes

- `app.secret_key` in `quickpost/app.py` is only used for flash
  messages, replace it with something random regardless.
- Post excerpts auto-generate from the first ~140 characters if you
  don't set one in the frontmatter.
- Tag filtering on `work.html` / `interests.html` is plain JavaScript
  (no framework) — a good place to practice extending things further,
  e.g. multi-tag filtering or a search box.
- `MAX_IMAGE_DIM` in `quickpost/app.py` controls how large uploaded
  photos are allowed to be (currently 1600px on the long side).
