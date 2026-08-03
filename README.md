# Markdown Static Blog Generator

## What this is

A lightweight static-site generator that converts Markdown blog posts into a
plain HTML/CSS website.

The generator reads Markdown files with frontmatter metadata, renders them
through Jinja2 templates, and outputs a ready-to-serve static website.

An optional Flask-based quick-post application is included for creating new
posts from a mobile device. It supports uploading images, creating Markdown
posts, and triggering a rebuild.

The generated website contains only static files, making it suitable for
hosting with Apache, Nginx, GitHub Pages, or any other static web server.

## Project structure

```
posts/                  <- Markdown blog posts
templates/              <- Jinja2 HTML templates
static/                 <- CSS, JavaScript, and uploaded assets
static/uploads/         <- Post images
build.py                <- Static site generator
output/                 <- Generated website
quickpost/              <- Optional mobile post creation app
```

## Creating a new post

Create a Markdown file inside the `posts/` directory:

```
posts/2026-08-05-example-post.md
```

Example:

```markdown
---
title: "Example post"
date: 2026-08-05
emoji: 📝
tags: [Example, Markdown]
image: static/uploads/example.jpg
excerpt: Short description shown on post cards.
---

# Hello World

This is the post content written in **Markdown**.
```

Then generate the website:

```bash
python3 build.py
```

The generated files will be placed in:

```
output/
```

Deploy the contents of this directory to your preferred web server.

## Optional: Mobile quick-post application

The optional Flask application provides a simple interface for creating posts
from a mobile device.

Features:

- Create Markdown posts through a web form
- Upload images
- Resize uploaded images
- Remove image metadata (EXIF)
- Automatically rebuild the static website

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
python3 app.py
```

By default, the application listens locally:

```
127.0.0.1:5001
```

For production use, run it behind a reverse proxy such as Apache or Nginx,
and protect it with authentication.

Example using Gunicorn:

```bash
gunicorn -w 1 -b 127.0.0.1:5001 app:app
```

## Reverse proxy example

Example Apache configuration:

```apache
<Location "/quickpost/">
    ProxyPass "http://127.0.0.1:5001/"
    ProxyPassReverse "http://127.0.0.1:5001/"

    AuthType Basic
    AuthName "Quick Post"
    AuthUserFile /path/to/password/file
    Require valid-user
</Location>
```

Create authentication credentials:

```bash
htpasswd -c /path/to/password/file username
```

## Configuration notes

- Replace the Flask `secret_key` with a unique random value before deployment.
- Post excerpts can be automatically generated from the post content if not
  provided.
- Tags and filtering are implemented using simple JavaScript and can be
  extended with additional functionality.
- Image upload limits can be adjusted through the image configuration settings.
- The generated website has no runtime dependencies and can be hosted almost
  anywhere.

## Requirements

Typical requirements:

- Python 3.x
- Jinja2
- Markdown parser
- Flask (only required for the optional quick-post application)

Install dependencies:

```bash
pip install -r requirements.txt
```