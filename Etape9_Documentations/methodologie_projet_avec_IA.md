# Méthodologie de construction du projet Early Warning avec l'aide de l'IA

## 1. Ma démarche

Pour construire ce projet, je n'ai pas utilisé l'IA pour lui demander
directement de créer un modèle de Machine Learning. Je l'ai utilisée
comme un **copilote** tout au long du projet : pour m'aider à comprendre
les données, écrire et corriger le code, challenger certains choix et
structurer les analyses.

Mon rôle est resté central : **je définis le besoin, je donne les règles
à respecter, je vérifie les résultats et je valide les choix**. L'IA
m'aide surtout à accélérer le passage entre une question métier et une
solution technique.

Ma démarche a suivi cette logique :

``` text
Besoin métier
→ Diagnostic des données
→ Nettoyage et normalisation
→ Consolidation
→ EDA
→ Feature Engineering
→ Visualisation
→ Définition de la cible et des métriques
→ Machine Learning
→ Analyse et priorisation
```

------------------------------------------------------------------------

## 2. Cadrage du besoin métier

J'ai commencé par clarifier ce que je voulais réellement résoudre. Mon
objectif n'était pas simplement de « faire du Machine Learning », mais
de construire un **système Early Warning** capable d'identifier les
corridors *pays d'origine → pays d'asile* qui risquent de connaître une
forte hausse des demandes à T+1.

J'ai donc cadré l'unité d'analyse comme :

**un pays d'origine × un pays d'asile × une année.**

À partir de là, j'ai guidé l'IA avec une règle simple : chaque
traitement devait pouvoir être relié à ce besoin métier. Cela m'a permis
d'éviter d'ajouter des analyses ou des variables uniquement parce
qu'elles étaient techniquement possibles.

------------------------------------------------------------------------

## 3. Diagnostic des données

Avant de nettoyer ou de transformer les données, j'ai d'abord cherché à
comprendre ce que j'avais réellement.

Avec l'aide de l'IA, j'ai contrôlé :

-   la structure des fichiers et les colonnes disponibles ;
-   les types de données ;
-   la période couverte ;
-   les valeurs manquantes ;
-   les doublons ;
-   les valeurs atypiques ;
-   la cohérence des identifiants pays ;
-   le niveau de granularité des données.

L'IA m'a aidé à écrire les contrôles Python et à interpréter les
résultats. En revanche, je lui ai demandé de **ne jamais considérer
automatiquement une anomalie comme une erreur**. Dans un projet d'Early
Warning, une valeur inhabituelle peut justement contenir un signal
important.

Cette première étape m'a permis de savoir ce qui était exploitable avant
de commencer le Feature Engineering.

------------------------------------------------------------------------

## 4. Nettoyage des données

Le nettoyage a été réalisé avec une règle importante : **ne pas
supprimer silencieusement les observations suspectes**.

J'ai demandé à l'IA de m'aider à identifier les problèmes et à les
quantifier avant toute correction. Les doublons strictement techniques
peuvent être écartés, mais leur traitement doit rester traçable.

Pour les valeurs manquantes, je n'ai pas voulu les remplacer
automatiquement par zéro. Une valeur manquante, une valeur nulle et une
absence réelle d'événement ne signifient pas la même chose.

Cette façon de travailler m'a permis de conserver au maximum
l'information originale tout en rendant les traitements reproductibles.

------------------------------------------------------------------------

## 5. Normalisation et standardisation

Une fois les problèmes identifiés, j'ai harmonisé les données afin de
fiabiliser les traitements suivants.

Cela concernait notamment :

-   les types des identifiants ;
-   les formats des années ;
-   les catégories textuelles ;
-   les noms et codes pays ;
-   les valeurs numériques ;
-   les formats nécessaires aux jointures.

L'IA m'a aidé à écrire ces transformations et surtout à ajouter des
contrôles après traitement.

L'objectif n'était pas de « rendre les données jolies », mais d'éviter
qu'une différence de format crée de faux écarts ou fasse échouer une
jointure.

------------------------------------------------------------------------

## 6. Consolidation des données

J'ai ensuite regroupé les données au niveau correspondant au besoin
métier : **corridor-année**.

Une décision importante a été de calculer les agrégations avant les
variables temporelles. Les lags ne doivent pas être additionnés à partir
de sous-catégories déjà calculées.

Pour les enrichissements, notamment avec le référentiel pays, j'ai
privilégié des **LEFT JOIN**. Je voulais conserver toutes les
observations du dataset principal, même lorsqu'une correspondance
n'était pas trouvée dans un référentiel.

J'ai également demandé à l'IA de vérifier systématiquement :

``` text
Nombre de lignes avant jointure
=
Nombre de lignes après jointure
```

lorsque la relation attendue ne devait pas multiplier les observations.

------------------------------------------------------------------------

## 7. Analyse exploratoire --- EDA

Une fois la base consolidée, j'ai réalisé une analyse exploratoire pour
comprendre les comportements présents dans les données avant de
construire les modèles.

Je me suis notamment intéressé :

-   à l'évolution des demandes dans le temps ;
-   à leur distribution ;
-   aux écarts entre corridors ;
-   aux valeurs extrêmes ;
-   aux principaux corridors en volume ;
-   aux évolutions annuelles ;
-   à la fréquence des fortes hausses.

L'IA m'a aidé à produire les statistiques et les graphiques, mais je
l'ai guidée pour ne pas multiplier les visualisations sans objectif.

Pour chaque graphique, je cherchais à répondre à une question métier
précise.

------------------------------------------------------------------------

## 8. Feature Engineering

Le Feature Engineering a été une étape centrale du projet.

J'ai construit des variables permettant de décrire la situation d'un
corridor à l'année T à partir de son historique et de son contexte, par
exemple :

-   volume actuel de demandes ;
-   volumes à T-1 et T-2 ;
-   croissance passée ;
-   variation absolue ;
-   accélération ;
-   deux hausses consécutives ;
-   poids du corridor dans le pays d'origine ;
-   poids du corridor dans le pays d'asile ;
-   contexte régional ;
-   information IDMC retardée lorsqu'elle était disponible.

Pour chaque feature proposée avec l'aide de l'IA, je me suis posé deux
questions :

> **Est-ce que cette variable a un sens pour le problème métier ?**

> **Est-ce que cette information serait réellement disponible au moment
> où je dois faire la prédiction ?**

Cette deuxième question a été essentielle pour éviter le **target
leakage**.

------------------------------------------------------------------------

## 9. Prévention du Target Leakage

J'ai imposé une règle très claire à l'IA :

> **Pour prédire à T, aucune feature ne doit utiliser une information
> disponible uniquement après T.**

Par exemple, `applied_t1` est utile pour savoir ce qui s'est réellement
passé l'année suivante et construire la cible. En revanche, cette
variable ne peut jamais être donnée au modèle comme information
d'entrée.

Cette règle m'a servi de filtre pour toutes les variables.

``` text
Information disponible à T ?
        │
     Oui ───► feature possible
        │
     Non ───► exclusion du modèle
```

Cela m'a permis de construire un modèle qui reproduit mieux une
situation réelle de prédiction.

------------------------------------------------------------------------

## 10. Visualisation et Data Storytelling

La visualisation a été utilisée pour expliquer le phénomène avant de
présenter le Machine Learning.

J'ai organisé le storytelling autour de questions simples :

1.  Comment le volume global de demandes évolue-t-il dans le temps ?
2.  Quels corridors concentrent les volumes les plus importants ?
3.  À quelle fréquence observe-t-on les fortes hausses que je souhaite
    détecter ?
4.  Le modèle arrive-t-il à mieux identifier ces situations ?

J'ai également remplacé autant que possible les identifiants techniques
par les noms des pays dans les graphiques destinés à la lecture métier.

L'IA m'a aidé à générer les graphiques, mais je lui ai demandé de
privilégier **la lisibilité et le message** plutôt que le nombre de
visualisations.

------------------------------------------------------------------------

## 11. Définition de la cible

Pour transformer le besoin en problème de classification, j'ai défini
une alerte comme une situation où les demandes à T+1 augmentent
simultanément :

-   d'au moins **30 %** ;
-   et d'au moins **100 demandes**.

``` python
target = (
    (applied_t1 >= applied * 1.30)
    &
    ((applied_t1 - applied) >= 100)
)
```

La combinaison des deux critères permet d'éviter de considérer comme
critique une très forte hausse en pourcentage portant sur un volume très
faible.

L'IA m'a aidé à traduire cette règle métier en code et à la tester sur
plusieurs cas simples.

------------------------------------------------------------------------

## 12. Choix des métriques

Je n'ai pas retenu l'accuracy comme seul indicateur, car les alertes
représentent une classe minoritaire.

J'ai donc évalué les modèles avec plusieurs métriques :

  |Métrique        |    Ce que je cherche à mesurer|
  | --- | --- |
 | Recall         |     Combien de vraies alertes mon modèle détecte|
 | Precision       |    Parmi mes alertes, combien sont réellement pertinentes|
 | F1-score        |    Le compromis entre Recall et Precision|
|  PR-AUC    |          La capacité à distinguer la classe rare|
|  ROC-AUC        |     La capacité globale de discrimination|
 | Balanced Accuracy |  La performance en tenant compte des deux classes|

Le choix des métriques a donc été lié au besoin opérationnel : **rater
une alerte importante et générer une fausse alerte n'ont pas le même
coût**.

------------------------------------------------------------------------

## 13. Machine Learning

Pour éviter de choisir immédiatement un modèle complexe, j'ai demandé à
l'IA de construire une comparaison progressive entre :

1.  une **baseline naïve** ;
2.  une **régression logistique** ;
3.  un **Random Forest** ;
4.  un **XGBoost**.

La baseline était importante : elle permet de vérifier que le Machine
Learning apporte réellement quelque chose par rapport à une stratégie
très simple.

J'ai également imposé un **split temporel**, et non aléatoire :

  |Jeu    |      Période|
  |---|---|
  |Train |       2000--2018|
 | Validation |  2019--2021|
 | Test |        2022--2024|
  |2025      |   hors évaluation supervisée|

Ce choix reproduit mieux la situation réelle : apprendre sur le passé
pour prédire le futur.

------------------------------------------------------------------------

## 14. Comment j'ai utilisé l'IA pour écrire et contrôler le code

Je n'ai pas demandé à l'IA de générer tout le projet en une seule fois.

J'ai travaillé étape par étape :

``` text
Je précise le besoin
        ↓
L’IA propose une logique
        ↓
L’IA écrit le code
        ↓
J’exécute et j’observe le résultat
        ↓
Je challenge les incohérences
        ↓
L’IA corrige
        ↓
Je valide avec des contrôles
```

J'ai progressivement appris à ne pas demander uniquement :

> « Donne-moi le code. »

mais plutôt :

> **« Explique ce que tu proposes, écris le code, puis donne-moi les
> contrôles permettant de vérifier que le résultat est correct. »**

Cette manière de guider l'IA a été particulièrement utile pour les
jointures, les valeurs manquantes, les features temporelles et le
Machine Learning.

------------------------------------------------------------------------

## 15. Ce que l'IA m'a apporté

L'IA m'a principalement permis de gagner du temps sur :

-   l'écriture du code Python ;
-   la structuration des notebooks ;
-   la création des contrôles ;
-   le diagnostic des erreurs ;
-   la proposition de features ;
-   la comparaison des modèles ;
-   l'interprétation des métriques ;
-   la création des visualisations ;
-   la documentation du projet.

Mais je n'ai pas considéré ses réponses comme automatiquement correctes.

Une réponse peut être techniquement convaincante tout en étant mauvaise
pour le besoin métier. J'ai donc utilisé l'IA comme **assistant de
raisonnement et de production**, et non comme décideur.

------------------------------------------------------------------------

## 16. La méthode que j'ai utilisée pour bien guider l'IA

Au fur et à mesure du projet, j'ai rendu mes demandes plus structurées.

Une bonne instruction contenait généralement :

**Contexte** --- ce que je cherche à résoudre.

**Grain** --- à quel niveau les données doivent être analysées.

**Contraintes** --- ce que l'IA ne doit pas faire.

**Temporalité** --- quelles informations sont réellement disponibles à
T.

**Résultat attendu** --- code, graphique, analyse ou documentation.

**Contrôles** --- comment vérifier que le résultat est correct.

Par exemple :

> Je travaille au niveau corridor-année. Je veux construire une feature
> utilisable à T pour prédire une hausse à T+1. Elle ne doit utiliser
> aucune information future. Ne supprime aucune anomalie
> silencieusement. Explique la logique, écris le code et ajoute les
> contrôles permettant de vérifier le résultat.

Cette façon de travailler a considérablement réduit les réponses trop
générales ou les solutions techniquement correctes mais mal adaptées au
projet.

------------------------------------------------------------------------

## 17. Répartition finale des responsabilités

 | Mon rôle              |       Rôle de l'IA|
  |---|---|
|  Définir le besoin métier |    Reformuler le besoin|
 | Fixer les règles          |   Proposer une implémentation|
 | Challenger les choix      |  Expliquer les alternatives|
  |Valider les données        |  Produire les contrôles|
 | Valider les features       |  Proposer et coder les features|
 | Arbitrer les métriques     |  Calculer et expliquer les métriques|
 | Choisir l'usage du score   |  Construire le scoring|
 | Valider les résultats      |  Aider à les interpréter|
 | Prendre la décision finale |  Assister la décision|

------------------------------------------------------------------------

## 18. Ce que je retiens de cette démarche

Ce projet m'a montré que la qualité du résultat dépend moins de la
capacité à écrire un « prompt parfait » que de la capacité à **piloter
une conversation technique de manière structurée**.

Ma méthode peut être résumée par trois questions :

> **Pourquoi faisons-nous ce traitement ?**\
> **Comment allons-nous le réaliser ?**\
> **Comment allons-nous vérifier qu'il est correct ?**

L'IA m'a permis d'aller plus vite dans la construction du projet, mais
le cadrage métier, les règles de qualité, la temporalité, les contrôles
et les décisions sont restés sous ma responsabilité.

C'est cette combinaison entre **expertise humaine, données vérifiées et
assistance IA** qui m'a permis de construire un projet plus structuré,
explicable et aligné avec le besoin métier.
