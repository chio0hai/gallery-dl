# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extractors for https://mangaread.org/"""

from .common import ChapterExtractor, MangaExtractor
from .. import text, exception
import re


class MangareadBase():
    """Base class for Mangaread extractors"""
    category = "mangaread"
    root = "https://www.mangaread.org"

    @staticmethod
    def parse_chapter_string(chapter_string, data):
        match = re.match(
            r"(?:(.+)\s*-\s*)?[Cc]hapter\s*(\d+)(\.\d+)?(?:\s*-\s*(.+))?",
            text.unescape(chapter_string).strip())
        manga, chapter, minor, title = match.groups()
        manga = manga.strip() if manga else ""
        data["manga"] = data.pop("manga", manga)
        data["chapter"] = text.parse_int(chapter)
        data["chapter_minor"] = minor or ""
        data["title"] = title or ""
        data["lang"] = "en"
        data["language"] = "English"


class MangareadChapterExtractor(MangareadBase, ChapterExtractor):
    """Extractor for manga-chapters from mangaread.org"""
    pattern = (r"(?:https?://)?(?:www\.)?mangaread\.org"
               r"(/manga/[^/?#]+/[^/?#]+)")
    test = (
        ("https://www.mangaread.org/manga/one-piece/chapter-1053-3/", {
            "pattern": (r"https://www\.mangaread\.org/wp-content/uploads"
                        r"/WP-manga/data/manga_[^/]+/[^/]+/[^.]+\.\w+"),
            "count": 11,
            "keyword": {
                "manga"   : "One Piece",
                "title"   : "",
                "chapter" : 1053,
                "chapter_minor": ".3",
                "tags"    : ["Oda Eiichiro"],
                "lang"    : "en",
                "language": "English",
            }
        }),
        ("https://www.mangaread.org/manga/one-piece/chapter-1000000/", {
            "exception": exception.NotFoundError,
        }),
        (("https://www.mangaread.org"
         "/manga/kanan-sama-wa-akumade-choroi/chapter-10/"), {
            "pattern": (r"https://www\.mangaread\.org/wp-content/uploads"
                        r"/WP-manga/data/manga_[^/]+/[^/]+/[^.]+\.\w+"),
            "count": 9,
            "keyword": {
                "manga"   : "Kanan-sama wa Akumade Choroi",
                "title"   : "",
                "chapter" : 10,
                "chapter_minor": "",
                "tags"    : list,
                "lang"    : "en",
                "language": "English",
            }
        }),
        # 'Chapter146.5'
        #        ^^ no whitespace
        ("https://www.mangaread.org/manga/above-all-gods/chapter146-5/", {
            "pattern": (r"https://www\.mangaread\.org/wp-content/uploads"
                        r"/WP-manga/data/manga_[^/]+/[^/]+/[^.]+\.\w+"),
            "count": 6,
            "keyword": {
                "manga"   : "Above All Gods",
                "title"   : "",
                "chapter" : 146,
                "chapter_minor": ".5",
                "tags"    : list,
                "lang"    : "en",
                "language": "English",
            }
        }),
    )

    def metadata(self, page):
        data = {"tags": list(text.extract_iter(page, "class>", "<"))}
        info = text.extr(page, '<h1 id="chapter-heading">', "</h1>")
        if not info:
            raise exception.NotFoundError("chapter")
        self.parse_chapter_string(info, data)
        return data

    def images(self, page):
        page = text.extr(
            page, '<div class="reading-content">', '<div class="entry-header')
        return [
            (url.strip(), None)
            for url in text.extract_iter(page, 'data-src="', '"')
        ]


class MangareadMangaExtractor(MangareadBase, MangaExtractor):
    """Extractor for manga from mangaread.org"""
    chapterclass = MangareadChapterExtractor
    pattern = r"(?:https?://)?(?:www\.)?mangaread\.org(/manga/[^/?#]+)/?$"
    test = (
        ("https://www.mangaread.org/manga/kanan-sama-wa-akumade-choroi", {
            "pattern": (r"https://www\.mangaread\.org/manga"
                        r"/kanan-sama-wa-akumade-choroi"
                        r"/chapter-\d+(-.+)?/"),
            "count"      : ">= 13",
            "keyword": {
                "manga"  : "Kanan-sama wa Akumade Choroi",
                "author" : ["nonco"],
                "artist" : ["nonco"],
                "type"   : "Manga",
                "genres" : ["Comedy", "Romance", "Shounen", "Supernatural"],
                "rating" : float,
                "release": 2022,
                "status" : "OnGoing",
                "lang"   : "en",
                "language"   : "English",
                "manga_alt"  : list,
                "description": str,
            }
        }),
        ("https://www.mangaread.org/manga/one-piece", {
            "pattern": (r"https://www\.mangaread\.org/manga"
                        r"/one-piece/chapter-\d+(-.+)?/"),
            "count"      : ">= 1066",
            "keyword": {
                "manga"  : "One Piece",
                "author" : ["Oda Eiichiro"],
                "artist" : ["Oda Eiichiro"],
                "type"   : "Manga",
                "genres" : list,
                "rating" : float,
                "release": 1997,
                "status" : "OnGoing",
                "lang"   : "en",
                "language"   : "English",
                "manga_alt"  : ["One Piece"],
                "description": str,
            }
        }),
        ("https://www.mangaread.org/manga/doesnotexist", {
            "exception": exception.NotFoundError,
        }),
    )

    def chapters(self, page):
        if 'class="error404' in page:
            raise exception.NotFoundError("manga")
        data = self.metadata(page)
        result = []
        for chapter in text.extract_iter(
                page, '<li class="wp-manga-chapter', "</li>"):
            url , pos = text.extract(chapter, '<a href="', '"')
            info, _ = text.extract(chapter, ">", "</a>", pos)
            self.parse_chapter_string(info, data)
            result.append((url, data.copy()))
        return result

    def metadata(self, page):
        extr = text.extract_from(text.extr(
            page, 'class="summary_content">', 'class="manga-action"'))
        return {
            "manga"      : text.extr(page, "<h1>", "</h1>").strip(),
            "description": text.unescape(text.remove_html(text.extract(
                page, ">", "</div>", page.index("summary__content"))[0])),
            "rating"     : text.parse_float(
                extr('total_votes">', "</span>").strip()),
            "manga_alt"  : text.remove_html(
                extr("Alternative </h5>\n</div>", "</div>")).split("; "),
            "author"     : list(text.extract_iter(
                extr('class="author-content">', "</div>"), '"tag">', "</a>")),
            "artist"     : list(text.extract_iter(
                extr('class="artist-content">', "</div>"), '"tag">', "</a>")),
            "genres"     : list(text.extract_iter(
                extr('class="genres-content">', "</div>"), '"tag">', "</a>")),
            "type"       : text.remove_html(
                extr("Type </h5>\n</div>", "</div>")),
            "release"    : text.parse_int(text.remove_html(
                extr("Release </h5>\n</div>", "</div>"))),
            "status"     : text.remove_html(
                extr("Status </h5>\n</div>", "</div>")),
        }
