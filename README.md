# romainvigouroux.dev

Blog d'architecte IA optimisé pour le GEO, construit avec [Hugo](https://gohugo.io), en français, anglais et allemand,
auto-hébergé sur un Raspberry Pi 3 B+, publié depuis Claude.

```text
Claude (conversation / Claude Code) ──► git push ──► GitHub (dépôt = source de vérité)
                                                        │  toutes les 5 min
                                                        ▼
Raspberry Pi 3 B+ ── update.sh : git pull → hugo → bascule atomique → IndexNow → LinkedIn
     │
  Caddy 127.0.0.1:8090 (journaux JSON) ◄── cloudflared (tunnel sortant, aucun port ouvert)
                                                        │
                                   Cloudflare (HTTPS, cache, DNS) ◄── humains, Google, Bing, robots d'IA
     │
  chaque lundi 8 h : weekly_report.py → e-mail (humains · venus d'une IA · robots d'IA)
```

| Élément | Rôle GEO |
|---|---|
| `hugo.toml`, `layouts/` | Pages HTML FR/EN/DE + graphe schema.org (`Person` unique, `TechArticle`, `FAQPage`, `BreadcrumbList`), `hreflang` |
| `llms.txt`, `llms-full.txt`, `…/index.md` | Versions Markdown propres pour les agents et LLM (une par langue) |
| `robots.txt` | Autorise explicitement les robots d'IA + `Content-Signal` |
| `sitemap.xml`, `feed.xml` | Découverte et fraîcheur (`lastmod`, RSS complet) |
| `scripts/indexnow.py` | Indexation immédiate par Bing (qui alimente ChatGPT Search et Copilot) |
| `scripts/weekly_report.py` | Mesure : qui lit (robots d'IA) et qui cite (visites depuis ChatGPT, Perplexity…) |
| `CLAUDE.md` | Règles d'écriture que Claude suit pour chaque article |

---

## Mise en route (≈ 1 h 30)

### 1. Dépôt GitHub
C'est fait : https://github.com/Rovig/romainvigouroux.dev

### 2. Raspberry Pi
Le site s'installe sur le **Raspberry Pi 3 B+ qui sert déjà le site des peintures** (rbrtvgrx, robertvigouroux.com).
Pas de nouvelle carte SD ni de réinstallation : on garde le système en place.

1. Connecte-toi au 3B+ en SSH (`ssh <utilisateur>@<nom-du-3B+>.local`, comme pour le site des peintures), puis :
```bash
git clone https://github.com/Rovig/romainvigouroux.dev.git /tmp/rv
sudo bash /tmp/rv/deploy/install.sh https://github.com/Rovig/romainvigouroux.dev.git
```
Pas de token : le 3B+ a déjà un tunnel Cloudflare, celui du site des peintures, et on lui ajoute simplement un nom
d'hôte (étape 3).

Ce que le script laisse intact : **nginx** (ports 80 et 8080), le `hugo` du système (0.111.3) dont dépend le site des
peintures, son webhook et son tunnel. Hugo 0.170.1 est installé **à part, dans `/opt/hugo`** (somme de contrôle
vérifiée), en version `arm64` ou `arm` selon que le système est en 64 ou 32 bits. Caddy écoute sur `127.0.0.1:8090`
et le script s'arrête sans rien modifier si ce port est déjà pris ; le site Caddy est un fichier séparé
(`/etc/caddy/romainvigouroux.caddy`) ajouté par `import`, et Caddy est installé sans démarrer son site de démonstration
sur le port 80 tenu par nginx. Si le dépôt est privé,
utilise l'URL `git@github.com:Rovig/romainvigouroux.dev.git` et colle la **clé de déploiement** affichée dans
GitHub → dépôt → Settings → Deploy keys (lecture seule).

### 3. Cloudflare
1. **Tunnel** : Zero Trust → Networks → Tunnels → ouvre **le tunnel existant du 3B+** (celui de robertvigouroux.com,
   sans rien y modifier d'autre) → *Public hostname* → *Add* : `romainvigouroux.dev` → `HTTP` → `127.0.0.1:8090` (pas `localhost` : Caddy n'écoute qu'en IPv4). Ajoute aussi `www` et une *Redirect Rule*
   `www.romainvigouroux.dev/*` → `https://romainvigouroux.dev/${1}` (301).
   Un tunnel ne peut servir que des domaines du même compte Cloudflare : si robertvigouroux.com est dans un autre
   compte que romainvigouroux.dev, ajoute d'abord romainvigouroux.dev au compte qui porte le tunnel.
2. **Robots d'IA — le réglage le plus important.** Ton domaine est récent : Cloudflare applique par défaut des blocages
   de certains robots d'IA. Dans *Security → Settings → Bot traffic* (ou *AI Crawl Control*) :
   - **Block AI bots** : désactivé ; autoriser toutes les catégories (Search, Agent, Training).
   - **Manage your robots.txt** (robots.txt géré) : **désactivé** — sinon Cloudflare ajoute des `Disallow` devant le tien.
   - **Bot Fight Mode** : désactivé (il peut défier des robots légitimes).
   Ces réglages se font **par domaine** : ne touche pas à ceux de robertvigouroux.com, qui doit rester fermé aux robots.
   Vérifie ensuite : `curl -s https://romainvigouroux.dev/robots.txt` doit commencer par `# robots.txt — romainvigouroux.dev`.
3. **SSL/TLS** : mode *Full*. **Always Use HTTPS** : activé.
4. **E-mail** : *Email Routing* → `contact@romainvigouroux.dev` vers ta boîte personnelle (gratuit).

### 4. Secrets et rapport hebdomadaire
```bash
sudo nano /etc/romainvigouroux/secrets.env      # SMTP (Gmail : mot de passe d'application) + REPORT_TO
sudo systemctl start site-report.service && journalctl -u site-report -n 30   # test immédiat
```
Le rapport arrive chaque **lundi à 8 h** ; les versions HTML/JSON sont aussi gardées dans `/srv/romainvigouroux.dev/reports/`.

### 5. LinkedIn
1. https://www.linkedin.com/developers/apps → *Create app* (une page entreprise est exigée : crée-en une à ton nom si besoin).
2. Onglet *Products* : ajoute **Share on LinkedIn** et **Sign In with LinkedIn using OpenID Connect**.
3. Onglet *Auth* : redirection `http://localhost:8765/callback` ; copie Client ID / Secret dans `secrets.env`.
4. Autorise une fois (procédure SSH dans l'en-tête de `scripts/linkedin_auth.py`), puis `LINKEDIN_ENABLED=1`.
5. Le jeton dure **60 jours** : le rapport du lundi te prévient 10 jours avant l'expiration.

Un article part sur LinkedIn seulement si son frontmatter contient `linkedin: true` — un post maximum toutes les 20 h.

### 6. Moteurs
- Clé IndexNow : `python3 -c "import uuid; print(uuid.uuid4().hex)"` → `indexnowKey` dans `hugo.toml` (le fichier de vérification est créé automatiquement).
- **Bing Webmaster Tools** et **Google Search Console** : ajoute le domaine (vérification DNS via Cloudflare) et soumets `/sitemap.xml`.

### 7. Cohérence d'identité (aussi important que le site)
- Bio LinkedIn, Medium et `hugo.toml → bio` : **mêmes mots-clés, même intitulé** (« Architecte IA » / « AI Architect » / « KI-Architekt »).
- LinkedIn → *Coordonnées → Site web* et section *Sélection* : `https://romainvigouroux.dev`.
- Republier sur Medium via **Import a story** (Medium pose alors un lien canonique vers ton site : pas de contenu dupliqué).
- Dépose ta photo dans `static/romain-vigouroux.jpg` et complète la section *Parcours* de `content/a-propos.md`, `.en.md` et `.de.md`.

---

## Publier un article depuis Claude

**Avec Claude Code** (recommandé) : ouvre le dépôt, puis par exemple
> « Écris un article sur la mission X : le client devait…, la contrainte était…, on a mis en place…, résultat… »

Claude lit `CLAUDE.md`, crée `content/articles/AAAA-MM-JJ-slug.md` et ses traductions `.en.md` et `.de.md`, vérifie le build et pousse. 5 minutes plus tard
c'est en ligne, IndexNow est notifié et, si tu l'as validé (`linkedin: true`), le post LinkedIn part.

**Depuis claude.ai** : relie le dépôt GitHub à la conversation et demande la même chose.

Commandes utiles en local (avec [Hugo installé](https://gohugo.io/installation/)) : `hugo server -D` (prévisualisation sur http://localhost:1313),
`hugo new content articles/2026-12-01-mon-sujet.md` (squelette d'article).

## Exploitation

| Besoin | Commande (sur le Pi) |
|---|---|
| Journal des déploiements | `journalctl -u site-update -f` |
| Forcer un rebuild | `sudo -u blog env FORCE=1 /srv/romainvigouroux.dev/repo/deploy/update.sh` |
| Revenir à la version précédente | `ls /srv/romainvigouroux.dev/releases` puis `sudo -u blog ln -sfn <dossier> /srv/romainvigouroux.dev/current` |
| Rapport à la demande | `sudo systemctl start site-report.service` |
| Timers | `systemctl list-timers 'site-*'` |

Mesure précise de `llms.txt` : Cloudflare met en cache les `.txt` par défaut, donc certaines lectures n'atteignent pas
le Pi. Pour tout compter, ajoute une *Cache Rule* « Bypass cache » sur les URL qui se terminent par `llms.txt`, `llms-full.txt`, `robots.txt` et `.md`.

Mettre Hugo à jour : changer `HUGO_VERSION` dans `deploy/install.sh` et relancer le script.
