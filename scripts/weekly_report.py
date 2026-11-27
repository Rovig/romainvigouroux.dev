#!/usr/bin/env python3
"""Rapport de trafic hebdomadaire, calculé depuis les journaux JSON de Caddy.

Trois populations, mesurées sur les 7 derniers jours et comparées aux 7 précédents :
  1. Humains        pages vues, visiteurs uniques (estimés), pages et référents principaux
  2. Venus d'une IA visiteurs arrivés depuis ChatGPT, Perplexity, Claude, Gemini, Copilot…
  3. Robots         robots d'IA (entraînement / recherche), moteurs, aperçus sociaux

Aucun cookie, aucun script dans le navigateur : les IP ne sont jamais stockées, seulement
un hachage salé par jour pour estimer les visiteurs uniques.

    python3 scripts/weekly_report.py --logs /var/log/caddy --out reports --state state [--email] [--days 7]
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import gzip
import hashlib
import html
import json
import os
import re
import smtplib
import sys
from email.message import EmailMessage
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

# ---------------------------------------------------------------- classification
AI_BOTS = {  # motif User-Agent → (nom, catégorie)
    "GPTBot": ("GPTBot (OpenAI)", "entraînement"),
    "OAI-SearchBot": ("OAI-SearchBot (ChatGPT Search)", "recherche"),
    "ChatGPT-User": ("ChatGPT-User (lecture à la demande)", "à la demande"),
    "ClaudeBot": ("ClaudeBot (Anthropic)", "entraînement"),
    "Claude-SearchBot": ("Claude-SearchBot", "recherche"),
    "Claude-User": ("Claude-User (lecture à la demande)", "à la demande"),
    "anthropic-ai": ("anthropic-ai", "entraînement"),
    "PerplexityBot": ("PerplexityBot", "recherche"),
    "Perplexity-User": ("Perplexity-User (lecture à la demande)", "à la demande"),
    "Google-CloudVertexBot": ("Google-CloudVertexBot", "à la demande"),
    "Gemini-Deep-Research": ("Gemini Deep Research", "à la demande"),
    "Applebot-Extended": ("Applebot-Extended", "entraînement"),
    "Amazonbot": ("Amazonbot", "entraînement"),
    "meta-externalagent": ("Meta-ExternalAgent", "entraînement"),
    "meta-externalfetcher": ("Meta-ExternalFetcher", "à la demande"),
    "CCBot": ("CCBot (Common Crawl)", "entraînement"),
    "Bytespider": ("Bytespider (ByteDance)", "entraînement"),
    "cohere-ai": ("Cohere", "entraînement"),
    "DuckAssistBot": ("DuckAssistBot", "à la demande"),
    "MistralAI-User": ("MistralAI-User (Le Chat)", "à la demande"),
    "YouBot": ("YouBot", "recherche"),
}
SEARCH_BOTS = {"Googlebot": "Googlebot", "bingbot": "Bingbot", "Applebot": "Applebot",
               "DuckDuckBot": "DuckDuckBot", "YandexBot": "YandexBot", "Qwantbot": "Qwant",
               "Baiduspider": "Baidu", "SeznamBot": "Seznam"}
SOCIAL_BOTS = {"LinkedInBot": "LinkedIn (aperçu)", "facebookexternalhit": "Facebook (aperçu)",
               "Twitterbot": "X (aperçu)", "Slackbot": "Slack (aperçu)", "Discordbot": "Discord (aperçu)",
               "WhatsApp": "WhatsApp (aperçu)", "TelegramBot": "Telegram (aperçu)"}
GENERIC_BOT = re.compile(r"bot|crawl|spider|slurp|fetch|scan|curl|wget|python|httpx|go-http|java/|axios|"
                         r"headless|lighthouse|monitor|preview|feed|okhttp|libwww|node-fetch", re.I)

AI_REFERRERS = {"chatgpt.com": "ChatGPT", "chat.openai.com": "ChatGPT", "perplexity.ai": "Perplexity",
                "claude.ai": "Claude", "gemini.google.com": "Gemini", "copilot.microsoft.com": "Copilot",
                "chat.mistral.ai": "Le Chat (Mistral)", "you.com": "You.com", "phind.com": "Phind",
                "deepseek.com": "DeepSeek", "kagi.com": "Kagi", "meta.ai": "Meta AI", "grok.com": "Grok"}
OTHER_REFERRERS = {"linkedin.com": "LinkedIn", "lnkd.in": "LinkedIn", "medium.com": "Medium",
                   "github.com": "GitHub", "google.": "Google", "bing.com": "Bing", "duckduckgo.com": "DuckDuckGo",
                   "qwant.com": "Qwant", "ecosia.org": "Ecosia", "t.co": "X", "x.com": "X",
                   "news.ycombinator.com": "Hacker News", "reddit.com": "Reddit"}
ASSET = re.compile(r"^/static/|\.(css|js|svg|png|jpe?g|webp|gif|ico|woff2?|xml|json|txt|md|map)$", re.I)


def classify_ua(ua: str) -> tuple[str, str]:
    """→ (type, nom) avec type ∈ {ai, search, social, bot, human}."""
    for pat, (name, _cat) in AI_BOTS.items():
        if pat.lower() in ua.lower():
            return "ai", name
    for pat, name in SEARCH_BOTS.items():
        if pat.lower() in ua.lower():
            return "search", name
    for pat, name in SOCIAL_BOTS.items():
        if pat.lower() in ua.lower():
            return "social", name
    if not ua or GENERIC_BOT.search(ua) or "Mozilla" not in ua:
        return "bot", "Autres robots"
    return "human", ""


def classify_referrer(ref: str, uri: str, own_host: str) -> tuple[str, str] | None:
    """→ (type, source) avec type ∈ {ai, other}, ou None (direct / interne)."""
    q = parse_qs(urlsplit(uri).query)
    utm = (q.get("utm_source") or [""])[0].lower()
    if utm:  # ChatGPT ajoute ?utm_source=chatgpt.com aux liens cités
        for dom, name in AI_REFERRERS.items():
            if dom.split(".")[0] in utm:
                return "ai", name
    if not ref:
        return ("other", f"utm:{utm}") if utm else None
    host = (urlsplit(ref).hostname or "").lower().removeprefix("www.")
    if not host or host == own_host:
        return None
    for dom, name in AI_REFERRERS.items():
        if host == dom or host.endswith("." + dom):
            return "ai", name
    for dom, name in OTHER_REFERRERS.items():
        if dom in host:
            return "other", name
    return "other", host


# ---------------------------------------------------------------- lecture des journaux
def iter_log_lines(log_dir: Path):
    for path in sorted(log_dir.glob("site*.log*")):
        opener = gzip.open if path.suffix == ".gz" else open
        try:
            with opener(path, "rt", encoding="utf-8", errors="replace") as f:
                yield from f
        except OSError as e:
            print(f"[report] lecture impossible {path}: {e}", file=sys.stderr)


def header(req: dict, name: str) -> str:
    for k, v in (req.get("headers") or {}).items():
        if k.lower() == name.lower():
            return v[0] if isinstance(v, list) and v else str(v)
    return ""


def new_bucket() -> dict:
    return {"pageviews": 0, "visitors": set(), "pages": collections.Counter(), "referrers": collections.Counter(),
            "ai_referrals": collections.Counter(), "ai_referral_pages": collections.Counter(),
            "ai_bots": collections.Counter(), "ai_bot_pages": collections.Counter(), "ai_bot_cat": collections.Counter(),
            "search_bots": collections.Counter(), "social_bots": collections.Counter(), "other_bots": 0,
            "llms_txt": collections.Counter(), "markdown_fetch": 0, "not_found": collections.Counter()}


def analyse(log_dir: Path, start: dt.datetime, mid: dt.datetime, end: dt.datetime, own_host: str):
    cur, prev = new_bucket(), new_bucket()
    for line in iter_log_lines(log_dir):
        try:
            e = json.loads(line)
        except ValueError:
            continue
        ts = dt.datetime.fromtimestamp(float(e.get("ts", 0)), dt.timezone.utc)
        if not (start <= ts < end):
            continue
        b = cur if ts >= mid else prev
        req = e.get("request") or {}
        if req.get("method") not in ("GET", "HEAD"):
            continue
        uri = req.get("uri", "/")
        path = urlsplit(uri).path or "/"
        status = int(e.get("status", 0))
        ua = header(req, "User-Agent")
        kind, name = classify_ua(ua)

        if status == 404 and kind == "human":
            b["not_found"][path] += 1
        if kind == "ai":
            b["ai_bots"][name] += 1
            b["ai_bot_cat"][next(c for p, (n, c) in AI_BOTS.items() if n == name)] += 1
            if status < 400 and not path.startswith("/static/"):
                b["ai_bot_pages"][path] += 1
        elif kind == "search":
            b["search_bots"][name] += 1
        elif kind == "social":
            b["social_bots"][name] += 1
        elif kind == "bot":
            b["other_bots"] += 1
        if path in ("/llms.txt", "/llms-full.txt") and status < 400:
            b["llms_txt"][name or ("Humain" if kind == "human" else "Robot non identifié")] += 1
        if path.endswith(".md") and status < 400 and kind != "human":
            b["markdown_fetch"] += 1

        if kind != "human" or status >= 400 or ASSET.search(path):
            continue
        b["pageviews"] += 1
        ip = req.get("client_ip") or header(req, "Cf-Connecting-Ip") or req.get("remote_ip", "")
        day_salt = ts.strftime("%Y-%m-%d") + os.environ.get("REPORT_SALT", "rv")
        b["visitors"].add(hashlib.sha256(f"{day_salt}|{ip}|{ua}".encode()).hexdigest()[:16])
        b["pages"][path] += 1
        ref = classify_referrer(header(req, "Referer"), uri, own_host)
        if ref:
            rtype, source = ref
            b["referrers"][source] += 1
            if rtype == "ai":
                b["ai_referrals"][source] += 1
                b["ai_referral_pages"][path] += 1
    for b in (cur, prev):
        b["visitors"] = len(b["visitors"])
    return cur, prev


# ---------------------------------------------------------------- rendu
def delta(now: int, before: int) -> str:
    if before == 0:
        return "nouveau" if now else "="
    pct = round((now - before) / before * 100)
    return f"{'+' if pct >= 0 else ''}{pct} %"


def table(title: str, counter: collections.Counter, n: int = 10, col: str = "") -> str:
    if not counter:
        return f"<h3>{html.escape(title)}</h3><p style='color:#777'>Rien cette semaine.</p>"
    rows = "".join(f"<tr><td>{html.escape(str(k))}</td><td style='text-align:right'><b>{v}</b></td></tr>"
                   for k, v in counter.most_common(n))
    return (f"<h3>{html.escape(title)}</h3><table cellpadding='6' style='border-collapse:collapse;width:100%'>"
            f"<tr style='background:#f2efe6'><th align='left'>{col}</th><th align='right'>Nb</th></tr>{rows}</table>")


def render(cur: dict, prev: dict, start: dt.date, end: dt.date, site: str, warnings: list[str]) -> tuple[str, str]:
    ai_ref, ai_ref_prev = sum(cur["ai_referrals"].values()), sum(prev["ai_referrals"].values())
    ai_hits, ai_hits_prev = sum(cur["ai_bots"].values()), sum(prev["ai_bots"].values())
    kpis = [("Pages vues (humains)", cur["pageviews"], prev["pageviews"]),
            ("Visiteurs uniques (est.)", cur["visitors"], prev["visitors"]),
            ("Visites venues d'une IA", ai_ref, ai_ref_prev),
            ("Passages de robots d'IA", ai_hits, ai_hits_prev)]
    text_lines = [f"Rapport {site} — semaine du {start} au {end}", ""]
    text_lines += [f"- {k} : {v} ({delta(v, p)})" for k, v, p in kpis]
    cells = "".join(
        f"<td style='padding:14px;border:1px solid #d9d4c7;background:#fff'>"
        f"<div style='font-size:12px;color:#666'>{k}</div><div style='font-size:28px;font-weight:700'>{v}</div>"
        f"<div style='font-size:12px;color:#8a6500'>{delta(v, p)} vs sem. préc.</div></td>" for k, v, p in kpis)
    warn = "".join(f"<p style='background:#fff3cd;padding:10px;border-left:4px solid #f2b705'>{html.escape(w)}</p>"
                   for w in warnings)
    text_lines += [""] + [f"⚠ {w}" for w in warnings]
    cats = ", ".join(f"{c} : {n}" for c, n in cur["ai_bot_cat"].most_common()) or "aucun"
    body = f"""<!doctype html><html><body style="font-family:system-ui,sans-serif;max-width:720px;margin:auto;color:#16181d;background:#f7f5ef;padding:20px">
<h2 style="margin-bottom:0">{html.escape(site)}</h2><p style="color:#666;margin-top:4px">Semaine du {start} au {end}</p>
{warn}
<table style="border-collapse:collapse;width:100%"><tr>{cells}</tr></table>
<h2>1. Les IA vous citent-elles ?</h2>
<p>Visiteurs arrivés depuis un assistant IA (lien cité puis cliqué).</p>
{table("Par assistant", cur["ai_referrals"], col="Source")}
{table("Pages d'arrivée depuis une IA", cur["ai_referral_pages"], col="Page")}
<h2>2. Les IA vous lisent-elles ?</h2>
<p>Par type d'usage — {html.escape(cats)}. Fichiers Markdown lus par des robots : <b>{cur["markdown_fetch"]}</b>.</p>
{table("Robots d'IA", cur["ai_bots"], col="Robot")}
{table("Pages les plus lues par les robots d'IA", cur["ai_bot_pages"], col="Page")}
{table("Lectures de llms.txt / llms-full.txt", cur["llms_txt"], col="Lecteur")}
<h2>3. Les humains</h2>
{table("Pages les plus vues", cur["pages"], col="Page")}
{table("Référents", cur["referrers"], col="Source")}
<h2>4. Le reste</h2>
{table("Moteurs de recherche", cur["search_bots"], col="Robot")}
{table("Aperçus sociaux (partages)", cur["social_bots"], col="Robot")}
<p>Autres robots non identifiés : {cur["other_bots"]}</p>
{table("Pages introuvables (404) demandées par des humains", cur["not_found"], col="Chemin")}
<p style="color:#888;font-size:12px">Source : journaux Caddy du Raspberry Pi. Les ressources servies depuis le cache Cloudflare
(CSS, images) n'y figurent pas. Visiteurs uniques estimés par jour, sans cookie.</p>
</body></html>"""
    return body, "\n".join(text_lines)


def linkedin_warnings(state_dir: Path) -> list[str]:
    tok = state_dir / "linkedin_token.json"
    if not tok.exists():
        return []
    try:
        exp = dt.datetime.fromisoformat(json.loads(tok.read_text())["expires_at"])
    except (KeyError, ValueError):
        return []
    days = (exp - dt.datetime.now(dt.timezone.utc)).days
    if days < 10:
        return [f"Le jeton LinkedIn expire dans {max(days, 0)} jour(s) : relancer scripts/linkedin_auth.py."]
    return []


def send_email(subject: str, html_body: str, text_body: str) -> None:
    need = ["SMTP_HOST", "SMTP_USER", "SMTP_PASS", "REPORT_TO"]
    if missing := [k for k in need if not os.environ.get(k)]:
        sys.exit(f"[report] variables manquantes pour l'e-mail : {', '.join(missing)}")
    msg = EmailMessage()
    msg["Subject"], msg["To"] = subject, os.environ["REPORT_TO"]
    msg["From"] = os.environ.get("REPORT_FROM") or os.environ["SMTP_USER"]
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")
    with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.environ.get("SMTP_PORT", 587)), timeout=30) as s:
        s.starttls()
        s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
        s.send_message(msg)
    print(f"[report] envoyé à {os.environ['REPORT_TO']}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--logs", default="/var/log/caddy")
    ap.add_argument("--out", default="reports")
    ap.add_argument("--state", default="state")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--host", default="romainvigouroux.dev")
    ap.add_argument("--email", action="store_true")
    ap.add_argument("--end", help="date de fin exclusive AAAA-MM-JJ (défaut : aujourd'hui)")
    args = ap.parse_args()

    end_d = dt.date.fromisoformat(args.end) if args.end else dt.date.today()
    end = dt.datetime.combine(end_d, dt.time(), dt.timezone.utc)
    mid = end - dt.timedelta(days=args.days)
    start = mid - dt.timedelta(days=args.days)
    cur, prev = analyse(Path(args.logs), start, mid, end, args.host)
    warnings = linkedin_warnings(Path(args.state))
    html_body, text_body = render(cur, prev, mid.date(), (end - dt.timedelta(days=1)).date(), args.host, warnings)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    stem = f"{end_d.isocalendar().year}-S{end_d.isocalendar().week:02d}"
    (out / f"{stem}.html").write_text(html_body, encoding="utf-8")
    summary = {k: (dict(v.most_common()) if isinstance(v, collections.Counter) else v) for k, v in cur.items()}
    (out / f"{stem}.json").write_text(json.dumps({"from": str(mid.date()), "to": str(end_d), **summary},
                                                 ensure_ascii=False, indent=1), encoding="utf-8")
    print(text_body)
    print(f"[report] {out / (stem + '.html')}")
    if args.email:
        ai = sum(cur["ai_referrals"].values())
        send_email(f"[{args.host}] {cur['pageviews']} pages vues · {ai} venues d'IA · "
                   f"{sum(cur['ai_bots'].values())} passages de robots IA", html_body, text_body)


if __name__ == "__main__":
    main()
