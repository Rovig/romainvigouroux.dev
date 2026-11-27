#!/usr/bin/env python3
"""Signale à IndexNow (Bing, Yandex, Seznam, Naver…) les URL nouvelles ou modifiées.

Bing alimente la recherche web de ChatGPT et de Copilot : être indexé vite par Bing,
c'est être récupérable vite par ces assistants.

La clé se règle dans hugo.toml → [params] indexnowKey. Le fichier de vérification
<clé>.txt est écrit automatiquement à la racine du site construit.
"""
import argparse
import json
import sys
import tomllib
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site-dir", required=True)
    ap.add_argument("--state", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cfg = tomllib.loads((ROOT / "hugo.toml").read_text(encoding="utf-8"))
    key = cfg.get("params", {}).get("indexnowKey", "")
    if not key:
        print("[indexnow] pas de clé (hugo.toml → params.indexnowKey), ignoré")
        return
    base = cfg["baseURL"].rstrip("/")
    site = Path(args.site_dir)
    (site / f"{key}.txt").write_text(key)

    manifest = []
    for m in [site / "manifest.json", *sorted(site.glob("*/manifest.json"))]:
        if m.exists():
            manifest += json.loads(m.read_text(encoding="utf-8"))
    state_path = Path(args.state)
    seen = json.loads(state_path.read_text()) if state_path.exists() else {}

    changed = [p["url"] for p in manifest if seen.get(p["url"]) != p["hash"]]
    if not changed:
        return
    urls = changed + [f"{base}/", f"{base}/articles/", f"{base}/en/", f"{base}/llms.txt", f"{base}/sitemap.xml"]
    payload = {"host": base.split("//", 1)[1], "key": key, "keyLocation": f"{base}/{key}.txt", "urlList": urls}
    print(f"[indexnow] {len(changed)} URL modifiée(s)")
    if args.dry_run:
        print(json.dumps(payload, indent=1, ensure_ascii=False))
        return
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            print(f"[indexnow] HTTP {r.status}")
    except Exception as e:  # noqa: BLE001
        sys.exit(f"[indexnow] erreur : {e}")
    seen.update({p["url"]: p["hash"] for p in manifest})
    state_path.write_text(json.dumps(seen, indent=1))


if __name__ == "__main__":
    main()
