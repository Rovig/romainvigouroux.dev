#!/usr/bin/env bash
# Installation complète sur Raspberry Pi 3 B+ (ou plus récent) — Raspberry Pi OS Lite, 64 bits conseillé,
# 32 bits accepté (Debian Bookworm ou plus récent).
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
PORT=8090   # doit correspondre à deploy/romainvigouroux.caddy

echo "==> Vérification du port $PORT (avant toute modification du système)"
# Le site rbrtvgrx est servi par nginx sur ce même Pi (ports 80 et 8080) : on vérifie qu'il n'y a pas de collision.
OCCUPANT=$(ss -ltnpH "sport = :$PORT" 2>/dev/null || true)
if [[ -n "$OCCUPANT" && "$OCCUPANT" != *caddy* ]]; then
  echo "Le port $PORT est déjà utilisé par autre chose que Caddy :"
  echo "$OCCUPANT"
  echo "Choisis un autre port dans romainvigouroux.caddy et PORT= ci-dessus, puis relance. Rien n'a été modifié."
  exit 1
fi
if systemctl is-active --quiet nginx; then
  echo "    nginx est actif (autre site) : il n'est pas modifié, Caddy écoute à côté sur 127.0.0.1:$PORT."
fi

echo "==> Paquets système"
apt-get update -qq
apt-get install -y -qq git curl gnupg debian-keyring debian-archive-keyring apt-transport-https \
  python3 unattended-upgrades

echo "==> Hugo (version figée, isolée dans /opt : le hugo du système n'est pas touché)"
# Un autre site du Pi peut dépendre du hugo installé par apt (ex. 0.111.3) : on ne le remplace pas.
HUGO_VERSION=0.170.1   # pour mettre à jour : changer ce numéro et relancer install.sh
HUGO_DIR=/opt/hugo/$HUGO_VERSION
if [[ ! -x "$HUGO_DIR/hugo" ]]; then
  case "$(dpkg --print-architecture)" in
    arm64) ARCH=arm64 ;;   # Raspberry Pi OS 64 bits (Pi 3 B+, Pi 4, Pi 5)
    armhf) ARCH=arm ;;     # Raspberry Pi OS 32 bits : Hugo publie cette archive sous le nom linux-arm
    amd64) ARCH=amd64 ;;
    *) echo "Architecture non prise en charge : $(dpkg --print-architecture)"; exit 1 ;;
  esac
  TGZ="hugo_${HUGO_VERSION}_linux-${ARCH}.tar.gz"
  URL="https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}"
  (cd /tmp && curl -fsSL -O "$URL/$TGZ" && curl -fsSL -o hugo_checksums.txt "$URL/hugo_${HUGO_VERSION}_checksums.txt" \
     && grep " ${TGZ}\$" hugo_checksums.txt | sha256sum -c -)
  mkdir -p "$HUGO_DIR" && tar -xzf "/tmp/$TGZ" -C "$HUGO_DIR" hugo && rm -f "/tmp/$TGZ" /tmp/hugo_checksums.txt
fi
ln -sfn "$HUGO_DIR" /opt/hugo/current
/opt/hugo/current/hugo version

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
dpkg -s cloudflared &>/dev/null || apt-get install -y -qq cloudflared
if ! dpkg -s caddy &>/dev/null && [[ ! -e /usr/sbin/policy-rc.d ]]; then
  # Le paquet démarre Caddy avec un site de démonstration sur :80, port déjà tenu par nginx :
  # on empêche ce démarrage automatique ; Caddy est lancé plus bas, avec la bonne configuration.
  printf '#!/bin/sh\nexit 101\n' > /usr/sbin/policy-rc.d && chmod 0755 /usr/sbin/policy-rc.d
  trap 'rm -f /usr/sbin/policy-rc.d' EXIT
  apt-get install -y -qq caddy
  rm -f /usr/sbin/policy-rc.d
  trap - EXIT
elif ! dpkg -s caddy &>/dev/null; then
  apt-get install -y -qq caddy   # policy-rc.d déjà présent sur le système : on ne le touche pas
fi

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

echo "==> Caddy (le site est un fichier à part, importé : une configuration existante est conservée)"
install -m 0644 "$BASE/repo/deploy/romainvigouroux.caddy" /etc/caddy/romainvigouroux.caddy
if ! grep -qs "romainvigouroux.caddy" /etc/caddy/Caddyfile; then
  NOUVEAU=$(mktemp)
  if grep -qs "The Caddyfile is an easy way" /etc/caddy/Caddyfile || [[ ! -s /etc/caddy/Caddyfile ]]; then
    # Fichier d'exemple livré avec le paquet (site de démo sur :80) : remplacé.
    echo "import /etc/caddy/romainvigouroux.caddy" > "$NOUVEAU"
  else
    # Configuration existante (autre site) : conservée, on ajoute seulement l'import.
    cat /etc/caddy/Caddyfile > "$NOUVEAU"
    printf '\nimport /etc/caddy/romainvigouroux.caddy\n' >> "$NOUVEAU"
  fi
  # On valide AVANT de toucher au vrai fichier : en cas d'erreur, rien n'est modifié.
  caddy validate --config "$NOUVEAU" --adapter caddyfile
  [[ -f /etc/caddy/Caddyfile ]] && cp -a /etc/caddy/Caddyfile "/etc/caddy/Caddyfile.avant-romainvigouroux.$(date +%Y%m%d%H%M%S)"
  install -m 0644 "$NOUVEAU" /etc/caddy/Caddyfile && rm -f "$NOUVEAU"
fi
caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
systemctl enable caddy
if systemctl is-active --quiet caddy; then systemctl reload caddy; else systemctl restart caddy; fi

echo "==> Premier build"
sudo -u blog env FORCE=1 "$BASE/repo/deploy/update.sh"

echo "==> Timers systemd"
install -m 0644 "$BASE"/repo/deploy/systemd/*.{service,timer} /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now site-update.timer site-report.timer

if systemctl list-unit-files cloudflared.service &>/dev/null && systemctl is-enabled cloudflared &>/dev/null; then
  echo "==> Tunnel Cloudflare déjà en service sur ce Pi : on n'y touche pas."
  echo "    Dans le tableau de bord Cloudflare, ajoute à CE tunnel un Public hostname :"
  echo "    romainvigouroux.dev → HTTP → 127.0.0.1:8090"
elif [[ -n "$TUNNEL_TOKEN" ]]; then
  echo "==> Tunnel Cloudflare"
  cloudflared service install "$TUNNEL_TOKEN"
  systemctl enable --now cloudflared
fi

echo
echo "Terminé. Vérifications :"
echo "  curl -sI http://127.0.0.1:8090/            # doit répondre 200"
echo "  systemctl list-timers 'site-*'             # deux timers actifs"
echo "  journalctl -u site-update -n 20            # journal des déploiements"
echo "Ensuite : remplir /etc/romainvigouroux/secrets.env (SMTP, LinkedIn)."
