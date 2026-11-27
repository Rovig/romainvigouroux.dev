#!/usr/bin/env python3
"""Publie sur LinkedIn les nouveaux articles marqués `linkedin: true`.

- Un article n'est publié qu'une seule fois (mémoire dans state/linkedin_published.json).
- Au plus UN post par exécution, et au moins 20 h entre deux posts : pas de rafale si
  plusieurs articles arrivent d'un coup.
- Sans LINKEDIN_ENABLED=1, simple simulation (affiche le post dans le journal).

API utilisée : Posts API (POST https://api.linkedin.com/rest/posts), scope w_member_social.
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

MIN_GAP = dt.timedelta(hours=20)
# Caractères réservés du « Little Text Format » de LinkedIn, à échapper dans `commentary`.
RESERVED = re.compile(r"([\\|{}@\[\]()<>#*_~])")
HASHTAG = re.compile(r"(?<![\w#])#(\w+)")


def to_little_text(text: str) -> str:
    """Échappe le texte et convertit les #hashtags au format attendu par l'API."""
    tags: list[str] = []

    def keep(m):
        tags.append(m.group(1))
        return f"\x00{len(tags) - 1}\x00"

    text = HASHTAG.sub(keep, text.strip())
    text = RESERVED.sub(r"\\\1", text)
    return re.sub(r"\x00(\d+)\x00", lambda m: "{hashtag|\\#|" + tags[int(m.group(1))] + "}", text)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--state", required=True, help="dossier d'état")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    state = Path(args.state)
    published_path = state / "linkedin_published.json"
    published = json.loads(published_path.read_text()) if published_path.exists() else {}
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    today = dt.date.today().isoformat()

    todo = [p for p in sorted(manifest, key=lambda p: p["date"])
            if p.get("linkedin") and p["slug"] not in published and p["date"] <= today]
    if not todo:
        return
    last = max((dt.datetime.fromisoformat(v["at"]) for v in published.values()), default=None)
    now = dt.datetime.now(dt.timezone.utc)
    if last and now - last < MIN_GAP:
        print(f"[linkedin] {len(todo)} en attente, prochain post possible après {last + MIN_GAP:%d/%m %H:%M} UTC")
        return

    post = todo[0]
    text = post.get("linkedin_post") or f"{post['title']}\n\n{post['description']}"
    body = {
        "author": None,
        "commentary": to_little_text(text),
        "visibility": "PUBLIC",
        "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [], "thirdPartyDistributionChannels": []},
        "content": {"article": {"source": post["url"], "title": post["title"], "description": post["description"]}},
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }

    enabled = os.environ.get("LINKEDIN_ENABLED") == "1" and not args.dry_run
    if not enabled:
        print(f"[linkedin] SIMULATION (LINKEDIN_ENABLED≠1) — « {post['title']} »\n{text}")
        return

    tok_path = state / "linkedin_token.json"
    if not tok_path.exists():
        sys.exit("[linkedin] pas de jeton : lancer scripts/linkedin_auth.py")
    tok = json.loads(tok_path.read_text())
    if dt.datetime.fromisoformat(tok["expires_at"]) < now:
        sys.exit("[linkedin] jeton expiré : relancer scripts/linkedin_auth.py")
    body["author"] = tok["person_urn"]

    req = urllib.request.Request("https://api.linkedin.com/rest/posts", data=json.dumps(body).encode(), headers={
        "Authorization": f"Bearer {tok['access_token']}",
        "LinkedIn-Version": os.environ.get("LINKEDIN_VERSION", "202610"),
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            post_id = r.headers.get("x-restli-id", "")
    except urllib.error.HTTPError as e:
        sys.exit(f"[linkedin] HTTP {e.code} : {e.read().decode(errors='replace')[:500]}")
    published[post["slug"]] = {"at": now.isoformat(), "id": post_id, "url": post["url"]}
    published_path.write_text(json.dumps(published, indent=1))
    print(f"[linkedin] publié : {post['title']} → https://www.linkedin.com/feed/update/{post_id}")


if __name__ == "__main__":
    main()
