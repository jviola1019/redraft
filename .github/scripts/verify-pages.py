"""Assemble a fixed Pages upload from isolated Jekyll output."""

import re
import shutil
import sys
from html.parser import HTMLParser
from pathlib import Path


FILES = {"index.html", "site.css"}
REPO = "https://github.com/jviola1019/redraft"
SITE = "https://redraft-time-machine.daddyjoev.chatgpt.site/"


class LandingPage(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.styles = []
        self.embeds = []

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == "a":
            self.links.append(attrs.get("href"))
        elif tag == "link":
            self.styles.append((attrs.get("rel"), attrs.get("href")))
        if tag in {"script", "iframe", "object", "embed", "form", "base"} or "src" in attrs:
            self.embeds.append(tag)


def verify(directory):
    files = {path.name for path in directory.iterdir()}
    if files != FILES or any(path.is_symlink() or not path.is_file() for path in directory.iterdir()):
        raise ValueError(f"Unexpected contents in Pages upload: {sorted(files)}")

    page = LandingPage()
    page.feed((directory / "index.html").read_text(encoding="utf-8"))
    if page.styles != [("stylesheet", "site.css")] or page.embeds:
        raise ValueError("Pages must use only the relative landing stylesheet")

    archive = re.compile(re.escape(REPO) + r"/archive/([0-9a-f]{40})\.zip")
    matches = [match for href in page.links if href and (match := archive.fullmatch(href))]
    if len(matches) != 1:
        raise ValueError("Expected one immutable source ZIP link")

    revision = matches[0][1]
    expected = {
        SITE,
        f"{REPO}/archive/{revision}.zip",
        f"{REPO}/blob/{revision}/INSTALL.md",
        f"{REPO}/blob/{revision}/docs/release/CURRENT_RELEASE.md",
        f"{REPO}/pull/1",
        REPO,
    }
    if set(page.links) != expected or len(page.links) != len(expected):
        raise ValueError("Unexpected Pages links or documentation revision")
    print(f"Verified Pages upload {sorted(files)} and review revision {revision}")


def assemble(source, destination):
    destination.mkdir()
    for name in sorted(FILES):
        path = source / name
        if path.is_symlink() or not path.is_file() or path.stat().st_nlink != 1:
            raise ValueError(f"Expected regular Jekyll output: {path}")
        shutil.copyfile(path, destination / name)
    verify(destination)


if __name__ == "__main__":
    if len(sys.argv) == 2:
        verify(Path(sys.argv[1]))
    elif len(sys.argv) == 3:
        assemble(Path(sys.argv[1]), Path(sys.argv[2]))
    else:
        raise SystemExit("Usage: verify-pages.py [JEKYLL_OUTPUT] PAGES_UPLOAD")
