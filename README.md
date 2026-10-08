# Projet UNHCR ML --- Priorisation des corridors à risque d'escalade des demandes d'asile

> Projet Data & Machine Learning consacré à l'analyse des demandes
> d'asile et à la construction d'un système **Early Warning** permettant
> de prioriser les corridors *pays d'origine → pays d'asile*
> susceptibles de connaître une forte hausse à l'année suivante.

![UNHCR](./data/images/unhcr-logo.png)

## Objectif

L'objectif n'est pas uniquement de prédire une évolution des demandes
d'asile, mais de répondre à une question opérationnelle :

> **À partir des informations disponibles à l'année T, quels corridors
> pays d'origine → pays d'asile doivent être surveillés en priorité pour
> anticiper une forte hausse des demandes à T+1 ?**

Le Machine Learning est utilisé comme **outil d'aide à la
priorisation**. Le score produit vise à orienter l'analyse humaine, et
non à la remplacer.

**Unité d'analyse :** `Pays d'origine × Pays d'asile × Année`

## À propos de l'UNHCR

L'**UNHCR (United Nations High Commissioner for Refugees)** est l'agence
des Nations Unies pour les réfugiés, fondée le 14 décembre 1950.

Elle protège et assiste notamment les réfugiés, demandeurs d'asile,
déplacés internes et personnes apatrides. Ses actions couvrent l'aide
d'urgence ainsi que la recherche de solutions durables comme le retour
volontaire, l'intégration locale ou la réinstallation dans un pays
tiers.

## Données

Le périmètre comprend plusieurs familles de données :

|Source                     |      Contenu|
|---|---|
| **UNHCR --- End-year population figures**   |  Stocks annuels : réfugiés, déplacés internes, demandeurs d'asile, etc.|
|  **UNHCR --- Solutions**    |        Retours, réinstallations, naturalisations et retours de déplacés internes|
|  **IDMC**                 |           Déplacements internes liés notamment aux conflits et violences|
| **UNRWA**                  |         Réfugiés de Palestine sous mandat de l'UNRWA|
|**Demographics**           |         Informations démographiques disponibles pour certaines sources|


Les données sont principalement ventilées par année, type de population,
pays/territoire d'origine et pays/territoire d'asile. La période de
travail couvre **2000 à 2025**.

### Principaux codes de population

   | Code    |  Signification | 
  |--- | ----  | 
  | `REF`  |   Refugees|
  | `ROC`   |People in refugee-like situation|
  | `ASY`  |Asylum-seekers|
  |`OIP`  |Other people in need of international protection|
  |`IDP` |Internally displaced persons|
  |`IOC` |People in IDP-like situation|
  |`STA` |Stateless people|
  |`OOC` |Others of concern|
  |`HST` |Host community|

### Solutions

`RET` = Returned refugees · 
`RST` = Resettled refugees · 
`NAT` = Naturalized refugees · 
`RDP` = Returned IDPs.

Le HCR utilise également certains codes ISO3 spécifiques, notamment
`UKN` pour *Various/unknown* et `STA` pour *Stateless*.

## Méthodologie

Le projet a été construit progressivement afin de ne pas commencer
directement par le Machine Learning :

``` text
Besoin métier
→ Diagnostic des données
→ Nettoyage & normalisation
→ Consolidation
→ EDA
→ Feature Engineering
→ Visualisation & Data Storytelling
→ Définition de la cible
→ Machine Learning
→ Scoring & priorisation
```

### 1. Diagnostic, nettoyage et consolidation

La première étape consiste à comprendre la structure, les types, la
granularité, les valeurs manquantes, doublons, valeurs atypiques et
référentiels.

Une règle est conservée pendant tout le projet : **aucune anomalie n'est
supprimée silencieusement**.

Les identifiants et formats sont ensuite normalisés. Les enrichissements
privilégient les **LEFT JOIN** afin de préserver les observations du
dataset principal.

Les données sont finalement consolidées au niveau **corridor-année**,
avant le calcul des variables temporelles.

### 2. EDA

L'analyse exploratoire étudie l'évolution annuelle des demandes, leur
distribution, les principaux corridors, les valeurs extrêmes et les
dynamiques de croissance.

L'objectif est de comprendre le phénomène avant de chercher à le
modéliser.

### 3. Feature Engineering

Les features décrivent uniquement la situation connue à T ou avant T.
Elles comprennent notamment :

``` text
applied
applied_lag1
applied_lag2
growth_past_1
absolute_change_past_1
acceleration
two_consecutive_increases
origin_applied_total_t
asylum_applied_total_t
segment_share_origin_t
segment_share_asylum_t
idmc_total_origin_lag1
```

Les variables de contexte comme l'année, les identifiants pays et les
régions sont également conservées.

### 4. Target Leakage

La règle centrale est :

> **Une variable utilisée pour prédire à T doit être disponible à T ou
> avant T.**

`applied_t1` est nécessaire pour observer ce qui se produit à T+1 et
construire la cible, mais elle est **strictement exclue des features du
modèle**.

### 5. Visualisation & Data Storytelling

Les visualisations suivent une logique métier : évolution globale des
demandes, principaux corridors en volume cumulé, fréquence des
événements d'alerte et performances des modèles.

Les noms de pays sont privilégiés dans les restitutions métier, tandis
que les identifiants restent disponibles pour la traçabilité technique.

## Cible Early Warning

Un événement est considéré comme une alerte lorsque les demandes à T+1
augmentent simultanément :

-   d'au moins **30 %** ;
-   d'au moins **100 demandes**.

``` python
target = (
    (applied_t1 >= applied * 1.30)
    &
    ((applied_t1 - applied) >= 100)
)
```

Cette double condition évite qu'une forte variation relative portant sur
un très faible volume soit automatiquement considérée comme une escalade
importante.

## Machine Learning

Quatre approches sont comparées :

1.  **Baseline naïve**
2.  **Logistic Regression**
3.  **Random Forest**
4.  **XGboost**

La baseline permet de vérifier que le Machine Learning apporte
réellement une amélioration par rapport à une stratégie triviale.

### Split temporel

  Dataset      Période      Rôle
  ------------ ------------ -------------------------------
  Train        2000--2018   apprentissage
  Validation   2019--2021   comparaison et choix du seuil
  Test         2022--2024   évaluation finale
  2025         ---          T+1 non encore disponible

Le principe est simple : **apprendre sur le passé pour évaluer sur le
futur**.

## Métriques

L'événement d'alerte étant minoritaire, l'accuracy seule n'est pas
suffisante.

 | Métrique     |           Lecture |
  |---|---|
  |**Recall**   |           part des vraies alertes détectées|
  |**Precision**          |part des alertes émises réellement pertinentes|
  |**F1-score**           | compromis Precision / Recall|
  |**PR-AUC**             | capacité à distinguer la classe minoritaire|
  |**ROC-AUC**            | capacité globale de discrimination|
  |**Balanced Accuracy**  | performance équilibrée entre les classes|

Le choix du modèle et du seuil doit tenir compte du coût opérationnel
des **faux positifs** et des **faux négatifs**.

## Score de risque

La sortie du modèle est utilisée comme score de priorisation :

``` text
Risk score = probabilité prédite × 100
```

Le score sert à classer les corridors par niveau de risque estimé. Il
s'agit d'un **outil de priorisation**, et non d'une décision
automatique.

## Structure du repository

``` text
## Structure du repository

Projet-UNHCR-ML/
│
├── data/
│   ├── raw/                          # données brutes issues des sources / API
│   ├── cleaned/                      # données nettoyées
│   ├── normalized/                   # données normalisées et harmonisées
│   ├── consolidated/                 # données consolidées entre les différentes sources
│   ├── processed/                    # datasets intermédiaires ou préparés pour l'analyse
│   ├── feature_engineering_outputs/  # dataset final et audits issus du Feature Engineering
│   └── images/                       # images utilisées dans le README / documentation
│
├── notebooks/
│   ├── Etape0_Extraction_UNHCR_API.ipynb
│   ├── Etape1_Diagnostic_Qualite.ipynb
│   ├── Etape2_Nettoyage.ipynb
│   ├── Etape3_Normalisation.ipynb
│   ├── Etape4_Consolidation.ipynb
│   ├── Etape5_EDA.ipynb
│   ├── Etape6_Feature_Engineering.ipynb
│   ├── Etape7_Visualisation_Storytelling.ipynb
│   └── Etape8_Machine_Learning.ipynb
│
├── model/
│   └── best_model_*.joblib           # modèle ML final sauvegardé
│
├── docs/                             # documentation méthodologique du projet
│
├── requirements.txt                  # dépendances Python
└── README.md                         # documentation principale du projet
```


## Notebooks

- Etape0_Extraction_UNHCR_API.ipynb,
- Etape1_Diagnostic_Qualitee.ipynb
- Etape2_Nettoyage.ipynb,
- Etape3_Normalisation.ipynb,
- Etape4_Consolidation.ipynb,
- Etape5_EDA.ipynb,
- Eape6_Feature_engineering.ipynb,
- Etape7_Visualisation_storytelling.ipynb,
- Etape8_Machine_Learning.ipynb


## Utilisation de l'IA

L'IA générative a été utilisée comme **copilote** pour structurer le
projet, écrire et corriger du code Python, proposer des contrôles Data
Quality, challenger le Feature Engineering, détecter les risques de
target leakage, analyser les résultats, créer les visualisations et
documenter les choix.

La méthode de travail a été itérative :

``` text
Je définis le besoin
→ je précise les contraintes
→ l’IA propose
→ j’exécute
→ je contrôle
→ je challenge
→ nous corrigeons
→ je valide
```

Les choix métier, les règles de qualité et la validation finale restent
sous responsabilité humaine.

## Principes de gouvernance

-   aucune suppression silencieuse d'anomalie ;
-   traçabilité des contrôles et exclusions ;
-   LEFT JOIN pour préserver les observations ;
-   quantification des valeurs manquantes ;
-   pas d'imputation statistique avant le split ML ;
-   aucune information future dans les features ;
-   baseline obligatoire ;
-   validation chronologique ;
-   distinction entre score ML et décision métier ;
-   validation humaine des alertes.

## Limites

Le projet est un **système d'aide à la décision**. Une hausse des
demandes d'asile dépend de facteurs politiques, sociaux, économiques,
administratifs et géopolitiques qui ne sont pas tous représentés dans
les données utilisées.

Une absence d'alerte ne signifie donc pas une absence de risque, et une
alerte ne garantit pas qu'une hausse se produira.

## Perspectives

Les prochaines étapes peuvent inclure la validation du seuil avec les
utilisateurs métier, l'analyse des faux positifs et faux négatifs,
l'automatisation du pipeline, le monitoring de la Data Quality et du
modèle, l'historisation des scores, la calibration éventuelle des
probabilités et l'intégration de nouvelles sources disponibles à T.

## Avertissement

Ce repository est un projet d'analyse de données et de Machine Learning
construit à partir de données relatives aux déplacements forcés et aux
demandes d'asile.

Les résultats, scores et alertes produits sont des **indicateurs
analytiques**. Ils ne constituent ni une position officielle de l'UNHCR,
ni une prédiction certaine, ni une décision concernant des personnes ou
populations.

Le modèle doit être utilisé avec contexte, prudence et validation
humaine.
