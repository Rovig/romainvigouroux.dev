#!/usr/bin/env bash
# Installation complète sur Raspberry Pi 4 (Raspberry Pi OS Lite 64 bits, Debian Bookworm ou plus récent).
#
#   sudo bash install.sh <URL_DU_DEPOT_GIT> [TOKEN_TUNNEL_CLOUDFLARE]
#
# Exemple : sudo bash install.sh https://github.com/Rovig/romainvigouroux.dev.git eyJhIjoi...
# Le script est idempotent : on peut le relancer sans risque.
set -euo pipefail

REPO_URL="${1:?Usage: sudo bash install.sh <URL_DU_DEPOT_GIT> [TOKEN_TUNNEL]}"
TUNNEL_TOKEN="${2:-}"
BASE=/srv/romainvigouroux.dev
[[ $EUID -eq 0 ]] || { echo "Lancer avec sudo"; exit 1; }

echo "==> Paquets système"
apt-get update -qq
apt-get install -y -qq git curl gnupg debian-keyring debian-archive-keyring apt-transport-https \
  python3 unattended-upgrades

echo "==> Hugo (version figée, vérifiée par somme SHA-256)"
HUGO_VERSION=0.170.1   # pour mettre à jour : changer ce numéro et relancer install.sh
if [[ "$(hugo version 2>/dev/null)" != *"v$HUGO_VERSION"* ]]; then
  ARCH=$(dpkg --print-architecture)
  DEB="hugo_${HUGO_VERSION}_linux-${ARCH}.deb"
  URL="https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}"
  (cd /tmp && curl -fsSL -O "$URL/$DEB" && curl -fsSL -o hugo_checksums.txt "$URL/hugo_${HUGO_VERSION}_checksums.txt" \
     && grep " ${DEB}\$" hugo_checksums.txt | sha256sum -c -)
  apt-get install -y -qq "/tmp/$DEB" && rm -f "/tmp/$DEB" /tmp/hugo_checksums.txt
fi
hugo version

echo "==> Caddy (dépôt officiel : la version Debian est trop ancienne pour la config)"
if [[ ! -f /etc/apt/sources.list.d/caddy-stable.list ]]; then
  curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/gpg.key | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt > /etc/apt/sources.list.d/caddy-stable.list
fi

echo "==> cloudflared (dépôt officiel Cloudflare)"
if [[ ! -f /etc/apt/sources.list.d/cloudflared.list ]]; then
  mkdir -p --mode=0755 /usr/share/keyrings
  curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg > /usr/share/keyrings/cloudflare-main.gpg
  echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared any main" \
    > /etc/apt/sources.list.d/cloudflared.list
fi
apt-get update -qq
apt-get install -y -qq caddy cloudflared

echo "==> Utilisateur de service 'blog' et arborescence"
id blog &>/dev/null || useradd --system --create-home --home-dir /home/blog --shell /usr/sbin/nologin blog
mkdir -p "$BASE"/{releases,state,reports} /var/log/caddy /etc/romainvigouroux
chown -R blog:blog "$BASE"
chown caddy:caddy /var/log/caddy && chmod 0755 /var/log/caddy

if [[ ! -f /home/blog/.ssh/id_ed25519 ]]; then
  sudo -u blog mkdir -p /home/blog/.ssh
  sudo -u blog ssh-keygen -q -t ed25519 -N "" -C "blog@raspberrypi" -f /home/blog/.ssh/id_ed25519
  sudo -u blog bash -c 'ssh-keyscan -t ed25519 github.com >> /home/blog/.ssh/known_hosts 2>/dev/null'
  echo
  echo "!!! Clé de déploiement (lecture seule) à ajouter sur GitHub → dépôt → Settings → Deploy keys :"
  cat /home/blog/.ssh/id_ed25519.pub
  echo
  read -rp "Appuie sur Entrée une fois la clé ajoutée (ou si le dépôt est public)... "
fi

echo "==> Dépôt"
if [[ ! -d "$BASE/repo/.git" ]]; then
  sudo -u blog git clone --quiet "$REPO_URL" "$BASE/repo"
fi

echo "==> Secrets (à remplir ensuite)"
if [[ ! -f /etc/romainvigouroux/secrets.env ]]; then
  cp "$BASE/repo/deploy/secrets.env.example" /etc/romainvigouroux/secrets.env
fi
chown root:blog /etc/romainvigouroux/secrets.env && chmod 0640 /etc/romainvigouroux/secrets.env

echo "==> Caddy"
install -m 0644 "$BASE/repo/deploy/Caddyfile" /etc/caddy/Caddyfile
caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
systemctl enable --now caddy && systemctl reload caddy

echo "==> Premier build"
sudo -u blog env FORCE=1 "$BASE/repo/deploy/update.sh"

echo "==> Timers systemd"
install -m 0644 "$BASE"/repo/deploy/systemd/*.{service,timer} /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now site-update.timer site-report.timer

if [[ -n "$TUNNEL_TOKEN" ]]; then
  echo "==> Tunnel Cloudflare"
  cloudflared service install "$TUNNEL_TOKEN" || echo "(tunnel déjà installé)"
  systemctl enable --now cloudflared
fi

echo
echo "Terminé. Vérifications :"
echo "  curl -sI http://127.0.0.1:8080/            # doit répondre 200"
echo "  systemctl list-timers 'site-*'             # deux timers actifs"
echo "  journalctl -u site-update -n 20            # journal des déploiements"
echo "Ensuite : remplir /etc/romainvigouroux/secrets.env (SMTP, LinkedIn)."
