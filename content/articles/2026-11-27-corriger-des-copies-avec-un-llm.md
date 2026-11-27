---
title: "Corriger 72 copies d'anglais avec un LLM, sans lui confier la note"
description: "Un correcteur de copies où l'IA repère et explique les fautes, mais où le code calcule la note, vérifie chaque citation et protège les données d'élèves mineurs."
date: 2026-11-27
slug: corriger-des-copies-avec-un-llm
tags: [Architecture IA, Agentic coding, LLM local]
keywords: [correction automatique, LLM, Claude Code, Ollama, RGPD, éducation, sortie structurée JSON]
tldr: "L'IA analyse chaque copie et produit un JSON ; le code vérifie que chaque faute citée existe vraiment, calcule la note et met en page les corrections. Prochaine étape : remplacer l'API par un modèle local, choisi par un banc d'essai mesuré."
problem: "Une professeure d'anglais de collège doit rendre, pour chaque devoir, des corrections individuelles détaillées à trois classes, ce qui prend des soirées entières."
context: "Collège, trois classes de troisième, devoir d'expression écrite (niveaux A1 à B1), copies tapées ou manuscrites d'élèves mineurs."
constraints:
  - "Une note juste et explicable, au demi-point, selon un barème existant"
  - "Aucune faute inventée : chaque erreur citée doit exister dans la copie"
  - "Des textes en français, au « vous », pour des élèves de 14-15 ans"
  - "Données d'élèves mineurs : rien ne doit être versionné ni exposé"
stack: [Claude Code, Python, Jinja2, WeasyPrint, python-docx, Ollama, YAML]
outcome: "Les 72 copies du devoir « Yearbook » corrigées : une correction PDF et Word par élève, une fiche « Retour à la classe » anonyme, un bilan par classe et un fichier de notes. Une contestation se traite en une minute environ. [À CONFIRMER : temps passé avant / après, retour de la professeure]"
faq:
  - q: "Peut-on laisser un LLM noter des copies ?"
    a: "Pas seul. Dans ce projet, le modèle attribue des points critère par critère et explique les fautes, mais le total est calculé par le programme, le critère de longueur est compté mécaniquement et chaque faute citée est vérifiée dans le texte de l'élève. La professeure relit et peut corriger une note en une ligne de fichier."
  - q: "Comment empêcher un LLM d'inventer des fautes ?"
    a: "En exigeant pour chaque faute l'extrait exact de la copie, puis en vérifiant par programme que cet extrait existe. Un extrait introuvable déclenche une nouvelle demande au modèle. C'est une règle simple qui élimine la plupart des hallucinations visibles par l'élève."
  - q: "Pourquoi vouloir un modèle local plutôt qu'une API ?"
    a: "Pour que les copies d'élèves mineurs ne quittent jamais l'établissement ou la maison. L'architecture est prévue pour : seule l'étape d'analyse change de moteur, via une API compatible OpenAI servie par Ollama ou vLLM, et un banc d'essai compare chaque modèle local à la référence avant tout choix."
  - q: "Quel matériel faut-il pour un LLM local de correction ?"
    a: "Un Mac M1 de 16 Go peut faire tourner un modèle de 8 à 9 milliards de paramètres et traiter un devoir de 75 copies en une nuit, d'après les estimations du dossier d'architecture. On n'investit dans une machine plus puissante que si le banc d'essai montre que la qualité ne suffit pas."
linkedin: false
linkedin_post: |
  Corriger 72 copies d'anglais avec une IA ? Facile. Lui faire confiance pour la note ? Non.

  Le besoin venait d'une professeure de collège : des corrections individuelles, détaillées, au « vous », pour trois classes. Des soirées entières à chaque devoir.

  Le piège, c'est de demander à un LLM « corrige et note ». Il invente des fautes, arrondit les notes, tutoie les élèves.

  J'ai séparé les rôles. L'IA analyse et explique. Le code vérifie que chaque faute citée existe vraiment dans la copie, calcule la note, compte les mots, met en page. Une contestation se règle en une ligne de fichier.

  Prochaine étape : un modèle local, pour que les copies d'élèves mineurs ne sortent jamais. Choisi par un banc d'essai mesuré, pas sur la foi d'un classement.

  Où placez-vous la frontière entre ce que décide l'IA et ce que décide le code ?

  #AgenticCoding #ArchitectureIA #EdTech
---
J'ai construit pour une professeure d'anglais de collège un correcteur de copies où un LLM analyse le texte de
chaque élève, mais où le code garde la main sur tout ce qui doit être exact : la note, les citations, la mise en
page et la protection des données. Résultat : 72 copies corrigées avec une correction individuelle par élève, et
une architecture prête à passer sur un modèle local.

## La situation

Pour chaque devoir d'expression écrite, la professeure veut rendre bien plus qu'une note : les fautes soulignées,
leur correction, une explication, des exercices tirés des phrases mêmes de l'élève, et un bilan de classe. Sur
trois classes de troisième, ce niveau de détail coûte des soirées entières.

Le premier devoir traité, « Yearbook », comptait 72 copies, tapées ou manuscrites, de niveau A1 à B1 du CECRL.

## Pourquoi c'est plus difficile qu'il n'y paraît

**La note doit être juste et défendable.** Une note se conteste. Elle doit suivre un barème précis, au demi-point,
et pouvoir être expliquée critère par critère.

**Un LLM invente.** Demandez-lui « corrige cette copie » : il trouvera parfois des fautes qui n'existent pas. Pour un
élève de 14 ans, une fausse faute est pire qu'une faute manquée.

**Le ton compte.** Les textes destinés aux élèves doivent être en français et au « vous ». Un tutoiement glissé par
le modèle suffit à rendre un document inutilisable.

**Ce sont des données de mineurs.** Les copies portent des noms et parfois des éléments personnels. Rien ne doit
être versionné, et à terme rien ne devrait quitter l'établissement.

## Les pistes écartées

| Option | Pourquoi je l'ai écartée |
|---|---|
| Un prompt « corrige et note » | Notes non reproductibles, fautes inventées, aucun contrôle |
| Un correcteur grammatical seul (type LanguageTool) | Repère l'orthographe, mais ne note pas et n'explique pas ; gardé comme pré-passe possible |
| Une plateforme en ligne de correction | Copies d'élèves envoyées à un tiers |

## L'architecture retenue

```text
copies .docx/.pdf/photos ─► extraire ─► ANALYSE (LLM) ─► vérifier ─► exercices ─► rendu
                                         JSON par copie    code         code        PDF, Word,
                                                                                    bilans, notes.csv
```

**Le LLM n'écrit qu'un fichier JSON par copie** : fautes (extrait exact, correction, catégorie, explication),
points par critère, points forts et conseils. Aujourd'hui, c'est Claude qui le produit dans une session Claude
Code : je lui demande « corrige les copies de ce devoir » et il suit les règles décrites dans le dépôt.

**Le code fait tout ce qui doit être exact.** Le critère de longueur est compté par le programme (mots sans la
citation, seuils fixes) ; le total n'est jamais recopié depuis le modèle mais recalculé. Une étape `verifier`
contrôle que chaque extrait cité existe dans la copie, que les notes sont au demi-point, que les catégories existent
et qu'aucun texte ne tutoie l'élève.

**Une taxonomie des fautes** associe à chaque catégorie une règle, un exemple et un exercice. Les mêmes catégories
nourrissent les corrections individuelles, la fiche « Retour à la classe », anonyme et projetable, et les groupes de
besoin du bilan professeur.

**Une contestation coûte une ligne.** La professeure ajoute la modification dans un fichier `corrections.yaml` et
relance le rendu : tout est régénéré en une minute environ, sans refaire l'analyse.

**Les copies manuscrites** sont photographiées ; le modèle en fait une transcription fidèle, fautes comprises, que la
professeure relit avant la correction.

### Vers un modèle local

Le dossier d'architecture prévoit de ne changer qu'une brique : l'analyse passe par une passerelle compatible
OpenAI (Ollama sur Mac, vLLM sur PC), avec une sortie contrainte par un schéma JSON. Pour un modèle de 8 à 30
milliards de paramètres, la tâche est découpée : fautes paragraphe par paragraphe, checklist, notation, rédaction.

Un **banc d'essai** compare chaque modèle candidat aux 72 analyses de référence, sur un échantillon stratifié de 16
copies : rappel et précision des fautes, écart de note (au plus 1,5 point en moyenne, jamais plus de 3), niveau
CECRL, vouvoiement, vitesse. Un modèle sous le seuil en précision ou en écart de note est éliminé, quel que soit son
score global.

## Ce que ça a donné

Les 72 copies du devoir « Yearbook » ont été corrigées : une correction PDF et Word par élève, toutes les corrections
d'une classe prêtes à imprimer, une fiche retour anonyme, un bilan par classe et un fichier de notes critère par
critère. La passerelle vers les modèles locaux et le banc d'essai sont implémentés.

[À CONFIRMER : temps de correction avant / après, résultats du banc d'essai sur les modèles locaux, retour de la professeure.]

## Ce que je referais différemment

La référence du banc d'essai, ce sont les analyses produites par Claude, pas la vérité. Le dossier d'architecture le
dit explicitement et prévoit que la professeure note elle-même dix copies, qui serviront d'étalon à tous les modèles,
Claude compris. Tant que cet étalon humain n'existe pas, aucun chiffre du banc d'essai ne dit qu'un modèle « corrige
bien » : il dit seulement qu'il corrige comme Claude.
