#!/usr/bin/env python3
"""Générateur de site statique pour romainvigouroux.dev, pensé pour le GEO.

Dépendances (paquets Debian / Raspberry Pi OS) :
    sudo apt install python3-markdown python3-yaml python3-jinja2 python3-pygments

Usage :
    python3 build.py                 # construit dans ./public
    python3 build.py --out /tmp/x    # autre dossier de sortie
    python3 build.py --drafts        # inclut les brouillons (prévisualisation)
    python3 build.py --serve         # construit puis sert sur http://localhost:8000

Sorties produites, en plus des pages HTML :
    feed.xml          RSS 2.0 avec le contenu complet
    sitemap.xml       avec <lastmod>
    robots.txt        ouvert aux crawlers IA + Content-Signal
    llms.txt          index lisible par les LLM (standard llmstxt.org)
    llms-full.txt     tout le contenu en Markdown, un seul fichier
    articles/<slug>.md  version Markdown brute de chaque article
    manifest.json     liste machine des articles (utilisée par IndexNow / LinkedIn)
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import re
import shutil
import sys
import unicodedata
from email.utils import format_datetime
from pathlib import Path

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
TEMPLATES = ROOT / "templates"
STATIC = ROOT / "static"

# Crawlers IA explicitement autorisés (un Allow explicite évite toute ambiguïté
# avec des règles génériques ou des robots.txt "managés" ajoutés par un CDN).
AI_CRAWLERS = [
    "GPTBot", "OAI-SearchBot", "ChatGPT-User",
    "ClaudeBot", "Claude-User", "Claude-SearchBot",
    "PerplexityBot", "Perplexity-User",
    "Google-Extended", "Googlebot", "Bingbot", "Applebot", "Applebot-Extended",
    "Amazonbot", "DuckAssistBot", "MistralAI-User", "CCBot", "meta-externalagent",
]


# --------------------------------------------------------------------------- utils
def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    return re.sub(r"[-\s_]+", "-", value)


def to_date(value) -> dt.date:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    return dt.date.fromisoformat(str(value))


def iso(d: dt.date) -> str:
    return d.isoformat()


def rfc822(d: dt.date) -> str:
    return format_datetime(dt.datetime(d.year, d.month, d.day, 8, 0, tzinfo=dt.timezone.utc))


def read_doc(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text
    _, fm, body = text.split("---", 2)
    return (yaml.safe_load(fm) or {}), body.lstrip("\n")


def md_renderer() -> markdown.Markdown:
    return markdown.Markdown(
        extensions=["extra", "sane_lists", "toc", "codehilite", "admonition"],
        extension_configs={
            "toc": {"permalink": "#", "permalink_title": "Lien vers cette section",
                    "slugify": lambda v, sep: slugify(v), "toc_depth": "2-3"},
            "codehilite": {"guess_lang": False, "css_class": "hl"},
        },
        output_format="html",
    )


def strip_html(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", s))


# --------------------------------------------------------------------------- content
class Site:
    def __init__(self, cfg: dict, include_drafts: bool):
        self.cfg = cfg
        self.url = cfg["url"].rstrip("/")
        self.include_drafts = include_drafts
        self.person_id = f"{self.url}/#person"
        self.website_id = f"{self.url}/#website"
        self.posts = self._load_posts()
        self.pages = self._load_pages()
        self.tags = self._collect_tags()

    def abs(self, path: str) -> str:
        return self.url + path

    # -- posts
    def _load_posts(self) -> list[dict]:
        posts = []
        for path in sorted((CONTENT / "posts").glob("*.md")):
            meta, body = read_doc(path)
            if meta.get("draft") and not self.include_drafts:
                continue
            for required in ("title", "description", "date"):
                if required not in meta:
                    sys.exit(f"[build] {path.name}: champ obligatoire manquant « {required} »")
            stem = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", path.stem)
            slug = meta.get("slug") or slugify(stem)
            md = md_renderer()
            html_body = md.convert(body)
            words = len(re.findall(r"\w+", strip_html(html_body)))
            date = to_date(meta["date"])
            updated = to_date(meta.get("updated", date))
            post = {
                **meta,
                "source": path,
                "slug": slug,
                "path": f"/articles/{slug}/",
                "md_path": f"/articles/{slug}.md",
                "body_md": body,
                "html": html_body,
                "toc": md.toc_tokens,
                "date": date,
                "updated": updated,
                "words": words,
                "reading_min": max(1, round(words / 230)),
                "tags": meta.get("tags", []),
                "keywords": meta.get("keywords", []),
                "faq": meta.get("faq", []),
                "constraints": meta.get("constraints", []),
                "stack": meta.get("stack", []),
            }
            post["url"] = self.abs(post["path"])
            post["hash"] = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
            posts.append(post)
        posts.sort(key=lambda p: p["date"], reverse=True)
        return posts

    def _load_pages(self) -> list[dict]:
        pages = []
        for path in sorted((CONTENT / "pages").glob("*.md")):
            meta, body = read_doc(path)
            slug = meta.get("slug", path.stem)
            md = md_renderer()
            page = {
                **meta,
                "slug": slug,
                "path": "/" if slug == "index" else f"/{slug}/",
                "body_md": body,
                "html": md.convert(body),
                "updated": to_date(meta.get("updated", dt.date.today())),
            }
            page["url"] = self.abs(page["path"])
            pages.append(page)
        return pages

    def _collect_tags(self) -> dict[str, dict]:
        tags: dict[str, dict] = {}
        for p in self.posts:
            for t in p["tags"]:
                key = slugify(t)
                tags.setdefault(key, {"name": t, "slug": key, "path": f"/sujets/{key}/", "posts": []})
                tags[key]["posts"].append(p)
        return dict(sorted(tags.items(), key=lambda kv: -len(kv[1]["posts"])))

    # -- schema.org
    def person_ld(self, full: bool = False) -> dict:
        a = self.cfg["author"]
        ld = {"@type": "Person", "@id": self.person_id, "name": a["name"],
              "url": self.url + "/", "jobTitle": a["job_title"], "sameAs": a["same_as"]}
        if full:
            ld.update({
                "description": " ".join(a["bio"].split()),
                "knowsAbout": a["knows_about"],
                "email": f"mailto:{a['email']}",
                "image": self.abs(a["image"]),
                "homeLocation": {"@type": "Country", "name": a["location"]},
                "mainEntityOfPage": self.abs("/a-propos/"),
            })
        return ld

    def website_ld(self) -> dict:
        return {"@type": "WebSite", "@id": self.website_id, "url": self.url + "/",
                "name": self.cfg["title"], "description": " ".join(self.cfg["description"].split()),
                "inLanguage": self.cfg["language"], "publisher": {"@id": self.person_id},
                "author": {"@id": self.person_id}}

    def breadcrumb_ld(self, crumbs: list[tuple[str, str]]) -> dict:
        return {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": name, "item": self.abs(path)}
            for i, (name, path) in enumerate(crumbs)]}

    def post_ld(self, p: dict) -> list[dict]:
        article = {
            "@type": "TechArticle", "@id": p["url"] + "#article",
            "headline": p["title"], "description": p["description"],
            "url": p["url"], "mainEntityOfPage": p["url"],
            "datePublished": iso(p["date"]), "dateModified": iso(p["updated"]),
            "inLanguage": self.cfg["language"], "wordCount": p["words"],
            "timeRequired": f"PT{p['reading_min']}M",
            "author": {"@id": self.person_id}, "publisher": {"@id": self.person_id},
            "isPartOf": {"@id": self.website_id},
            "keywords": ", ".join(p["keywords"] + p["tags"]),
            "about": [{"@type": "Thing", "name": t} for t in p["tags"]],
            "encoding": {"@type": "MediaObject", "encodingFormat": "text/markdown",
                         "contentUrl": self.abs(p["md_path"])},
        }
        if p.get("problem"):
            article["abstract"] = p["problem"]
        if p.get("stack"):
            article["mentions"] = [{"@type": "SoftwareApplication", "name": s} for s in p["stack"]]
        if p.get("image"):
            article["image"] = self.abs(p["image"])
        graph = [article, self.person_ld(),
                 self.breadcrumb_ld([("Accueil", "/"), ("Articles", "/articles/"), (p["title"], p["path"])])]
        if p["faq"]:
            graph.append({"@type": "FAQPage", "@id": p["url"] + "#faq", "mainEntity": [
                {"@type": "Question", "name": f["q"],
                 "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in p["faq"]]})
        return graph

    @staticmethod
    def ld_script(graph: list[dict]) -> str:
        data = {"@context": "https://schema.org", "@graph": graph}
        return json.dumps(data, ensure_ascii=False, indent=1).replace("</", "<\\/")


# --------------------------------------------------------------------------- build
def write(out: Path, rel: str, content: str) -> None:
    target = out / rel.lstrip("/")
    if rel.endswith("/"):
        target = target / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def build(out: Path, include_drafts: bool = False) -> Site:
    cfg = yaml.safe_load((ROOT / "site.yaml").read_text(encoding="utf-8"))
    site = Site(cfg, include_drafts)
    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=select_autoescape(["html"]),
                      trim_blocks=True, lstrip_blocks=True)
    months = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
              "septembre", "octobre", "novembre", "décembre"]
    env.filters["slug"] = slugify
    env.filters["date_fr"] = lambda d: f"{d.day} {months[d.month - 1]} {d.year}"
    env.globals.update(site=site, cfg=cfg, year=dt.date.today().year)

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    if STATIC.exists():
        shutil.copytree(STATIC, out / "static")
        from pygments.formatters import HtmlFormatter
        css = out / "static" / "style.css"
        css.write_text(css.read_text(encoding="utf-8") + "\n/* Coloration syntaxique (pygments, monokai) */\n"
                       + HtmlFormatter(style="monokai").get_style_defs(".hl") + "\n", encoding="utf-8")

    def render(tpl: str, **ctx) -> str:
        return env.get_template(tpl).render(**ctx)

    # Accueil
    home = next((pg for pg in site.pages if pg["slug"] == "index"), None)
    write(out, "/", render("home.html", page=home, posts=site.posts[:6], canonical=site.url + "/",
                           ld=site.ld_script([site.website_ld(), site.person_ld(full=True)])))

    # Pages
    for pg in site.pages:
        if pg["slug"] == "index":
            continue
        graph = [site.breadcrumb_ld([("Accueil", "/"), (pg["title"], pg["path"])])]
        if pg["slug"] == "a-propos":
            graph += [{"@type": "ProfilePage", "url": pg["url"], "mainEntity": site.person_ld(full=True),
                       "dateModified": iso(pg["updated"])}]
        elif pg["slug"] == "contact":
            graph += [{"@type": "ContactPage", "url": pg["url"], "about": {"@id": site.person_id}},
                      site.person_ld()]
        write(out, pg["path"], render("page.html", page=pg, canonical=pg["url"], ld=site.ld_script(graph)))

    # Articles
    for i, p in enumerate(site.posts):
        newer = site.posts[i - 1] if i > 0 else None
        older = site.posts[i + 1] if i + 1 < len(site.posts) else None
        related = [q for q in site.posts if q is not p and set(q["tags"]) & set(p["tags"])][:3]
        write(out, p["path"], render("post.html", post=p, newer=newer, older=older, related=related,
                                     canonical=p["url"], ld=site.ld_script(site.post_ld(p))))
        write(out, p["md_path"], markdown_export(site, p))

    # Listes
    list_ld = lambda name, path, items: site.ld_script([
        {"@type": "CollectionPage", "name": name, "url": site.abs(path), "isPartOf": {"@id": site.website_id},
         "mainEntity": {"@type": "ItemList", "itemListElement": [
             {"@type": "ListItem", "position": k + 1, "url": q["url"], "name": q["title"]}
             for k, q in enumerate(items)]}},
        site.breadcrumb_ld([("Accueil", "/"), (name, path)])])
    write(out, "/articles/", render("list.html", title="Articles", posts=site.posts,
                                    intro="Problèmes rencontrés, architectures retenues, résultats mesurés.",
                                    canonical=site.abs("/articles/"),
                                    ld=list_ld("Articles", "/articles/", site.posts)))
    write(out, "/sujets/", render("tags.html", tags=site.tags.values(), canonical=site.abs("/sujets/"),
                                  ld=site.ld_script([site.breadcrumb_ld([("Accueil", "/"), ("Sujets", "/sujets/")])])))
    for t in site.tags.values():
        write(out, t["path"], render("list.html", title=f"Sujet : {t['name']}", posts=t["posts"],
                                     intro=f"Tous les articles de Romain Vigouroux sur {t['name']}.",
                                     canonical=site.abs(t["path"]),
                                     ld=list_ld(t["name"], t["path"], t["posts"])))
    write(out, "/404.html", render("404.html", canonical=None, ld=None))

    # Fichiers machine
    write(out, "/feed.xml", feed(site))
    write(out, "/sitemap.xml", sitemap(site))
    write(out, "/robots.txt", robots(site))
    write(out, "/llms.txt", llms_txt(site))
    write(out, "/llms-full.txt", llms_full(site))
    if cfg.get("indexnow_key"):
        write(out, f"/{cfg['indexnow_key']}.txt", cfg["indexnow_key"])
    manifest = [{"slug": p["slug"], "url": p["url"], "title": p["title"], "description": p["description"],
                 "date": iso(p["date"]), "updated": iso(p["updated"]), "hash": p["hash"],
                 "linkedin": bool(p.get("linkedin", False)), "linkedin_post": p.get("linkedin_post", ""),
                 "tags": p["tags"]} for p in site.posts]
    write(out, "/manifest.json", json.dumps(manifest, ensure_ascii=False, indent=1))
    return site


def markdown_export(site: Site, p: dict) -> str:
    head = [f"# {p['title']}", "", f"> {p['description']}", "",
            f"- Auteur : {site.cfg['author']['name']}, {site.cfg['author']['job_title']} ({site.url})",
            f"- Publié : {iso(p['date'])} — mis à jour : {iso(p['updated'])}",
            f"- URL : {p['url']}"]
    if p["tags"]:
        head.append(f"- Sujets : {', '.join(p['tags'])}")
    card = []
    for label, key in (("TL;DR", "tldr"), ("Problème", "problem"), ("Contexte", "context"),
                       ("Résultat", "outcome")):
        if p.get(key):
            card.append(f"**{label}** : {' '.join(str(p[key]).split())}")
    if p["constraints"]:
        card.append("**Contraintes** : " + " ; ".join(p["constraints"]))
    if p["stack"]:
        card.append("**Stack** : " + ", ".join(p["stack"]))
    faq = []
    if p["faq"]:
        faq = ["", "## Questions fréquentes", ""]
        for f in p["faq"]:
            faq += [f"### {f['q']}", "", f["a"], ""]
    return "\n".join(head + [""] + card + ["", p["body_md"].strip()] + faq) + "\n"


def feed(site: Site) -> str:
    items = []
    for p in site.posts[:30]:
        items.append(f"""  <item>
    <title>{html.escape(p['title'])}</title>
    <link>{p['url']}</link>
    <guid isPermaLink="true">{p['url']}</guid>
    <pubDate>{rfc822(p['date'])}</pubDate>
    <dc:creator>{html.escape(site.cfg['author']['name'])}</dc:creator>
    <description>{html.escape(p['description'])}</description>
    {''.join(f'<category>{html.escape(t)}</category>' for t in p['tags'])}
    <content:encoded><![CDATA[{p['html'].replace(']]>', ']]]]><![CDATA[>')}]]></content:encoded>
  </item>""")
    last = rfc822(site.posts[0]["updated"]) if site.posts else rfc822(dt.date.today())
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:dc="http://purl.org/dc/elements/1.1/">
<channel>
  <title>{html.escape(site.cfg['title'])}</title>
  <link>{site.url}/</link>
  <atom:link href="{site.url}/feed.xml" rel="self" type="application/rss+xml"/>
  <description>{html.escape(' '.join(site.cfg['description'].split()))}</description>
  <language>{site.cfg['language']}</language>
  <lastBuildDate>{last}</lastBuildDate>
{chr(10).join(items)}
</channel>
</rss>
"""


def sitemap(site: Site) -> str:
    urls = [(site.url + "/", site.posts[0]["updated"] if site.posts else dt.date.today())]
    urls += [(pg["url"], pg["updated"]) for pg in site.pages if pg["slug"] != "index"]
    urls += [(site.abs("/articles/"), site.posts[0]["updated"] if site.posts else dt.date.today())]
    urls += [(p["url"], p["updated"]) for p in site.posts]
    urls += [(site.abs(t["path"]), max(q["updated"] for q in t["posts"])) for t in site.tags.values()]
    body = "\n".join(f"  <url><loc>{u}</loc><lastmod>{iso(d)}</lastmod></url>" for u, d in urls)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + body + "\n</urlset>\n")


def robots(site: Site) -> str:
    lines = ["# robots.txt — romainvigouroux.dev",
             "# Ce site SOUHAITE être lu, indexé, cité et appris par les moteurs de recherche et les IA.",
             "# Content Signals (https://contentsignals.org) : recherche, réponses IA et entraînement autorisés.",
             "", "User-agent: *", "Content-Signal: search=yes, ai-input=yes, ai-train=yes", "Allow: /", ""]
    for bot in AI_CRAWLERS:
        lines += [f"User-agent: {bot}", "Allow: /", ""]
    lines += [f"Sitemap: {site.url}/sitemap.xml", ""]
    return "\n".join(lines)


def llms_txt(site: Site) -> str:
    a = site.cfg["author"]
    out = [f"# {a['name']}", "", f"> {' '.join(a['bio'].split())}", "",
           f"Domaines d'expertise : {', '.join(a['knows_about'])}.",
           f"Contact : {a['email']} — LinkedIn : {site.cfg['contact']['linkedin']}",
           "Chaque article existe aussi en Markdown brut (lien .md ci-dessous). "
           f"Version intégrale en un seul fichier : {site.url}/llms-full.txt", "",
           "## Pages", "",
           f"- [À propos de {a['name']}]({site.abs('/a-propos/')}): parcours, expertise, façon de travailler",
           f"- [Contact]({site.abs('/contact/')}): comment soumettre un problème ou une mission",
           "", "## Articles", ""]
    for p in site.posts:
        summary = p.get("tldr") or p["description"]
        out.append(f"- [{p['title']}]({site.abs(p['md_path'])}): {' '.join(str(summary).split())}")
    out += ["", "## Optional", "", f"- [Flux RSS]({site.url}/feed.xml)", f"- [Sitemap]({site.url}/sitemap.xml)", ""]
    return "\n".join(out)


def llms_full(site: Site) -> str:
    parts = [llms_txt(site), "\n---\n"]
    for pg in site.pages:
        parts += [f"# {pg.get('title', site.cfg['title'])}\n\nURL : {pg['url']}\n\n{pg['body_md'].strip()}\n", "\n---\n"]
    for p in site.posts:
        parts += [markdown_export(site, p), "\n---\n"]
    return "\n".join(parts)


# --------------------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(ROOT / "public"))
    ap.add_argument("--drafts", action="store_true")
    ap.add_argument("--serve", action="store_true")
    args = ap.parse_args()
    out = Path(args.out)
    site = build(out, args.drafts)
    print(f"[build] {len(site.posts)} article(s), {len(site.pages)} page(s), {len(site.tags)} sujet(s) → {out}")
    if args.serve:
        import functools
        import http.server
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(out))
        print("[serve] http://localhost:8000")
        http.server.ThreadingHTTPServer(("127.0.0.1", 8000), handler).serve_forever()


if __name__ == "__main__":
    main()
