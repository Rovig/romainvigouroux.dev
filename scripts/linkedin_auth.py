#!/usr/bin/env python3
"""Autorisation LinkedIn (OAuth 2.0), à faire une fois puis tous les ~60 jours.

Prérequis : une app sur https://www.linkedin.com/developers/apps avec les produits
« Share on LinkedIn » et « Sign In with LinkedIn using OpenID Connect », et l'URL de
redirection http://localhost:8765/callback déclarée dans l'onglet Auth.

Sur le Pi (sans écran), depuis ton ordinateur :
    ssh -L 8765:localhost:8765 pi@romainvigouroux.local
    sudo -u blog env $(sudo cat /etc/romainvigouroux/secrets.env | xargs) \
        python3 /srv/romainvigouroux.dev/repo/scripts/linkedin_auth.py --state /srv/romainvigouroux.dev/state
puis ouvre l'URL affichée dans ton navigateur et connecte-toi à LinkedIn.
"""
import argparse
import datetime as dt
import http.server
import json
import os
import secrets
import sys
import urllib.parse
import urllib.request
from pathlib import Path

REDIRECT = "http://localhost:8765/callback"
SCOPES = "openid profile w_member_social"


def post_form(url: str, data: dict) -> dict:
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode(),
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def get_json(url: str, token: str) -> dict:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default="state")
    args = ap.parse_args()
    cid, csec = os.environ.get("LINKEDIN_CLIENT_ID"), os.environ.get("LINKEDIN_CLIENT_SECRET")
    if not (cid and csec):
        sys.exit("LINKEDIN_CLIENT_ID et LINKEDIN_CLIENT_SECRET doivent être définis.")
    state = secrets.token_urlsafe(16)
    url = "https://www.linkedin.com/oauth/v2/authorization?" + urllib.parse.urlencode(
        {"response_type": "code", "client_id": cid, "redirect_uri": REDIRECT, "state": state, "scope": SCOPES})
    print("Ouvre cette URL dans ton navigateur :\n\n" + url + "\n")

    result: dict = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            q = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
            ok = q.get("state", [""])[0] == state and "code" in q
            result.update(code=q.get("code", [""])[0] if ok else "", error=q.get("error_description", [""])[0])
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("<h2>C'est bon, tu peux fermer cet onglet.</h2>".encode() if ok
                             else "<h2>Échec de l'autorisation.</h2>".encode())

        def log_message(self, *a):
            pass

    srv = http.server.HTTPServer(("127.0.0.1", 8765), Handler)
    while "code" not in result:
        srv.handle_request()
    if not result["code"]:
        sys.exit(f"Autorisation refusée : {result.get('error')}")

    tok = post_form("https://www.linkedin.com/oauth/v2/accessToken", {
        "grant_type": "authorization_code", "code": result["code"], "redirect_uri": REDIRECT,
        "client_id": cid, "client_secret": csec})
    me = get_json("https://api.linkedin.com/v2/userinfo", tok["access_token"])
    expires = dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=int(tok.get("expires_in", 0)))
    data = {"access_token": tok["access_token"], "expires_at": expires.isoformat(),
            "refresh_token": tok.get("refresh_token"), "person_urn": f"urn:li:person:{me['sub']}",
            "name": me.get("name")}
    out = Path(args.state) / "linkedin_token.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=1))
    os.chmod(out, 0o600)
    print(f"Jeton enregistré pour {data['name']} ({data['person_urn']}), valable jusqu'au {expires:%d/%m/%Y}.")


if __name__ == "__main__":
    main()
