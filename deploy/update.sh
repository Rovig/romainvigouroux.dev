#!/usr/bin/env bash
# Récupère le dépôt, reconstruit le site si quelque chose a changé, bascule atomiquement,
# puis notifie IndexNow et publie sur LinkedIn. Lancé toutes les 5 min par site-update.timer.
#   FORCE=1 deploy/update.sh   → reconstruit même sans nouveau commit
set -euo pipefail

BASE="${BASE:-/srv/romainvigouroux.dev}"
REPO="$BASE/repo"
STATE="$BASE/state"
RELEASES="$BASE/releases"
mkdir -p "$STATE" "$RELEASES"

cd "$REPO"
git fetch --quiet origin main
if [[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" && "${FORCE:-0}" != "1" && -e "$BASE/current" ]]; then
  exit 0
fi
git reset --quiet --hard origin/main
COMMIT=$(git rev-parse --short HEAD)

RELEASE="$RELEASES/$(date +%Y%m%d-%H%M%S)-$COMMIT"
python3 build.py --out "$RELEASE"
chmod -R a+rX "$RELEASE"

# Bascule atomique : Caddy sert toujours une version complète.
ln -sfn "$RELEASE" "$BASE/current.tmp"
mv -Tf "$BASE/current.tmp" "$BASE/current"
echo "[update] en ligne : $COMMIT"

# On garde les 5 dernières versions (retour arrière : ln -sfn <ancienne> current).
ls -1dt "$RELEASES"/*/ | tail -n +6 | xargs -r rm -rf

# Notifications — un échec ici ne doit pas casser le déploiement.
python3 scripts/indexnow.py --site-dir "$BASE/current" --state "$STATE/indexnow.json" || echo "[update] IndexNow en échec"
python3 scripts/linkedin_publish.py --manifest "$BASE/current/manifest.json" --state "$STATE" || echo "[update] LinkedIn en échec"
