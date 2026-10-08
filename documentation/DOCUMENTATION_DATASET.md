# Documentation du dataset final — Feature Engineering

## Projet UNHCR Early Warning — Priorisation des corridors de demandes d'asile

---

## 1. Objectif du document

Cette documentation décrit le dataset final produit à l'issue de l'étape de **Feature Engineering** du projet UNHCR Early Warning.

Le document a pour objectifs de :

- rendre le dataset compréhensible sans devoir relire l'ensemble des notebooks ;
- documenter la granularité, les sources et les transformations ;
- fournir un **Data Dictionary** complet ;
- expliquer les valeurs manquantes structurelles ;
- distinguer les variables disponibles à l'année T des informations futures ;
- prévenir les risques de **Target Leakage** ;
- faciliter la reproductibilité, l'audit et la réutilisation du dataset pour l'EDA, la visualisation et le Machine Learning.

> **Principe central : le dataset final constitue une interface entre la préparation des données et la modélisation. Sa documentation fait partie du livrable Data.**

---

# 2. Informations générales

| Attribut | Valeur |
|---|---|
| **Nom du fichier analysé** | `dataset_ml_features(3).csv` |
| **Nom recommandé dans le repository** | `dataset_ml_features.csv` |
| **Emplacement recommandé** | `data/feature_engineering_outputs/dataset_ml_features.csv` |
| **Format actuel** | CSV |
| **Encodage recommandé** | UTF-8 |
| **Nombre de lignes** | **86 234** |
| **Nombre de colonnes** | **20** |
| **Période couverte** | **2000–2025** |
| **Nombre d'années** | **26** |
| **Pays/territoires d'origine (`coo_id`)** | **215** identifiants distincts |
| **Pays/territoires d'asile (`coa_id`)** | **186** identifiants distincts |
| **Granularité** | 1 ligne = 1 corridor origine × asile × année |
| **Doublons stricts observés** | **0** |
| **Doublons sur la clé `coo_id × coa_id × year`** | **0** |
| **Usage principal** | EDA, visualisation, storytelling et Machine Learning Early Warning |
| **Horizon ML** | T → T+1 |

---

# 3. Finalité métier

Le dataset a été construit pour répondre à la question suivante :

> **À partir des informations disponibles à l'année T, quels corridors entre pays d'origine et pays d'asile doivent être examinés en priorité car ils présentent des signaux associés historiquement à une forte hausse des demandes d'asile à T+1 ?**

Le dataset ne constitue donc pas uniquement une table analytique. Il prépare une utilisation opérationnelle dans laquelle le Machine Learning produit un **signal de priorisation** destiné aux analystes.

```text
Données historiques
      ↓
Nettoyage / Normalisation / Consolidation
      ↓
Granularité corridor × année
      ↓
Feature Engineering
      ↓
dataset_ml_features.csv
      ↓
EDA / Visualisation
      ↓
Machine Learning
      ↓
Score de priorisation
      ↓
Analyse humaine
```

> **Le modèle priorise. L'analyste interprète. L'humain décide.**

---

# 4. Granularité et clé métier

L'unité d'observation est :

```text
1 ligne = 1 coo_id × 1 coa_id × 1 year
```

avec :

- `coo_id` : identifiant du pays ou territoire d'origine ;
- `coa_id` : identifiant du pays ou territoire d'asile ;
- `year` : année d'observation.

La clé métier attendue est donc :

```python
["coo_id", "coa_id", "year"]
```

Le fichier analysé ne contient **aucun doublon sur cette clé**.

Cette granularité est importante : les variables temporelles sont calculées **après agrégation au niveau corridor-année**. Les lags pré-calculés sur des sous-catégories ne doivent pas être additionnés.

---

# 5. Sources de données

| Source | Rôle | Variables / informations utilisées |
|---|---|---|
| **UNHCR — Asylum applications** | Source principale | volumes de demandes d'asile par origine, asile et année |
| **Référentiel pays** | Enrichissement descriptif | noms des pays/territoires associés à `coo_id` et `coa_id` |
| **UNHCR / référentiels géographiques** | Enrichissement géographique | région d'origine et région d'asile |
| **IDMC** | Enrichissement contextuel | volume de déplacements internes du pays d'origine, décalé dans le temps |

La mesure quantitative principale issue des données de demandes d'asile est `applied`.

Lorsque la source contient une variable descriptive telle que `app_pc`, le volume est conservé dans `applied` : il n'est pas recalculé à partir de `app_pc`.

---

# 6. Data Dictionary

## 6.1 Identifiants et dimensions descriptives

| Colonne | Type observé | Description | Valeurs / unité | Source | Transformation / usage |
|---|---|---|---|---|---|
| `year` | `int64` | Année T de l'observation | 2000 à 2025 | UNHCR | Dimension temporelle et feature ML |
| `coo_id` | `int64` | Identifiant du pays/territoire d'origine | 215 valeurs distinctes observées | UNHCR / référentiel | Clé corridor et feature catégorielle |
| `coa_id` | `int64` | Identifiant du pays/territoire d'asile | 186 valeurs distinctes observées | UNHCR / référentiel | Clé corridor et feature catégorielle |
| `coa_name` | `object` | Nom du pays/territoire d'asile | Texte | Référentiel pays | Ajout par LEFT JOIN ; restitution métier |
| `coo_name` | `object` | Nom du pays/territoire d'origine | Texte | Référentiel pays | Ajout par LEFT JOIN ; restitution métier |
| `origin_region` | `object` | Région géographique du pays d'origine | Catégorie | Référentiel | Feature catégorielle |
| `asylum_region` | `object` | Région géographique du pays d'asile | Catégorie | Référentiel | Feature catégorielle |

Les noms de pays sont destinés à la lisibilité des restitutions. Les identifiants restent conservés pour la traçabilité et les jointures.

---

## 6.2 Volume courant et historique du corridor

| Colonne | Type observé | Description | Valeurs / unité | Transformation |
|---|---|---|---|---|
| `applied` | `int64` | Volume de demandes enregistré pour le corridor à l'année T | nombre ≥ 0 | Agrégation au niveau corridor-année |
| `applied_lag1` | `float64` | Volume du même corridor à T-1 | nombre ou NA | Décalage temporel de 1 an |
| `applied_lag2` | `float64` | Volume du même corridor à T-2 | nombre ou NA | Décalage temporel de 2 ans |
| `applied_t1` | `float64` | Volume observé pour le corridor à T+1 | nombre ou NA | Décalage vers le futur ; support de construction de la cible uniquement |

### Point de gouvernance

`applied_t1` est une **information future** par rapport à T.

> **Elle ne doit jamais être incluse dans les variables d'entrée du modèle.**

Son rôle est uniquement de construire et d'évaluer la cible supervisée pendant les périodes pour lesquelles T+1 est connu.

---

## 6.3 Indicateurs de dynamique temporelle

| Colonne | Type observé | Description | Interprétation | Transformation |
|---|---|---|---|---|
| `growth_past_1` | `float64` | Croissance récente du volume par rapport à T-1 | positif = hausse ; négatif = baisse | Calcul à partir de T et T-1 |
| `absolute_change_past_1` | `float64` | Variation absolue entre T et T-1 | unité : volume de demandes | `applied - applied_lag1` |
| `acceleration` | `float64` | Évolution de la dynamique récente du corridor | positif = accélération de la dynamique | Calcul nécessitant un historique suffisant |
| `two_consecutive_increases` | `float64` dans le CSV | Indique si deux hausses successives sont observées | `1` = oui, `0` = non, `NA` = historique insuffisant | Indicateur construit à partir de plusieurs années |

`two_consecutive_increases` est conceptuellement un indicateur binaire nullable. Le CSV le recharge en `float64` en raison de la présence de valeurs manquantes.

---

## 6.4 Indicateurs de contexte origine / asile

| Colonne | Type observé | Description | Unité | Transformation |
|---|---|---|---|---|
| `origin_applied_total_t` | `int64` | Volume total de demandes associé au pays d'origine à T, tous pays d'asile confondus | volume | Agrégation par origine et année |
| `asylum_applied_total_t` | `int64` | Volume total de demandes reçues par le pays d'asile à T, toutes origines confondues | volume | Agrégation par asile et année |
| `segment_share_origin_t` | `float64` | Part du corridor dans le volume total de l'origine à T | ratio, généralement 0–1 | `applied / origin_applied_total_t` |
| `segment_share_asylum_t` | `float64` | Part du corridor dans le volume total du pays d'asile à T | ratio, généralement 0–1 | `applied / asylum_applied_total_t` |

Ces variables replacent un corridor dans son environnement : un même volume n'a pas la même signification selon son poids dans l'ensemble des demandes liées à l'origine ou à l'asile.

---

## 6.5 Enrichissement IDMC

| Colonne | Type observé | Description | Unité | Transformation |
|---|---|---|---|---|
| `idmc_total_origin_lag1` | `float64` | Indicateur IDMC disponible pour le pays d'origine à T-1 | volume selon la donnée IDMC consolidée | Enrichissement sur l'origine avec décalage d'un an |

Le décalage T-1 vise à préserver la logique temporelle du système : une variable explicative ne doit pas dépendre d'une information indisponible au moment du scoring.

---

# 7. Qualité du dataset final

## 7.1 Complétude

| Colonne | Valeurs manquantes | Taux |
|---|---:|---:|
| `applied_lag1` | 19 277 | **22,35 %** |
| `applied_lag2` | 24 406 | **28,30 %** |
| `growth_past_1` | 19 277 | **22,35 %** |
| `absolute_change_past_1` | 19 277 | **22,35 %** |
| `acceleration` | 29 220 | **33,88 %** |
| `two_consecutive_increases` | 29 220 | **33,88 %** |
| `idmc_total_origin_lag1` | 55 278 | **64,10 %** |
| `applied_t1` | 3 967 | **4,60 %** |
| Toutes les autres colonnes | 0 | **0 %** |

### Interprétation

Ces valeurs manquantes ne doivent pas être supprimées automatiquement.

Les lags et indicateurs temporels peuvent être absents lorsqu'un corridor ne dispose pas d'un historique suffisant. `acceleration` et `two_consecutive_increases` nécessitent davantage d'historique, ce qui explique leur taux de NA supérieur.

`idmc_total_origin_lag1` présente **64,10 %** de valeurs manquantes. Cette couverture partielle doit être considérée explicitement lors de la modélisation.

`applied_t1` est absent pour **3 967 lignes (4,60 %)**. Dans la version actuelle, cette absence correspond à l'horizon pour lequel T+1 n'est pas disponible, notamment le scoring 2025 → 2026.

> **Aucune ligne ne doit être supprimée uniquement parce qu'une feature historique ou contextuelle est manquante.**

L'imputation statistique nécessaire au ML doit être réalisée **dans le pipeline, après le split temporel**, afin d'éviter toute fuite d'information.

---

## 7.2 Unicité

Contrôles réalisés sur le fichier :

```text
Doublons stricts : 0
Doublons coo_id × coa_id × year : 0
```

La clé métier est donc unique dans le dataset analysé.

---

## 7.3 Validité et cohérence

Les contrôles attendus comprennent :

```text
year compris dans la période couverte
applied numérique et non négatif
coo_id / coa_id renseignés
coo_name / coa_name renseignés
ratios contrôlés
clé corridor-année unique
features temporelles calculées dans le bon ordre
aucune information T+1 dans X
```

---

# 8. Profil du volume `applied`

Le fichier analysé présente les statistiques suivantes :

| Indicateur | Valeur |
|---|---:|
| Nombre d'observations | 86 234 |
| Moyenne | 472,29 |
| Médiane | 23 |
| 90e percentile | 584 |
| 95e percentile | 1 530,35 |
| 99e percentile | 7 750,74 |
| Maximum | 406 901 |

La distribution est donc fortement asymétrique : la médiane est de **23**, alors que le maximum atteint **406 901**.

Cette asymétrie justifie une lecture prudente des moyennes et confirme l'intérêt de conserver les valeurs extrêmes : dans un contexte Early Warning, une valeur très élevée peut représenter un événement réel et non une erreur à supprimer.

---

# 9. Transformation appliquée

Le pipeline de construction peut être résumé ainsi :

```text
Données nettoyées / normalisées / consolidées
                  ↓
Agrégation corridor × année
                  ↓
Contrôle de l'unicité
                  ↓
Création des lags T-1 et T-2
                  ↓
Calcul de la croissance récente
                  ↓
Calcul de la variation absolue
                  ↓
Calcul de l'accélération
                  ↓
Détection des hausses consécutives
                  ↓
Agrégats origine / asile à T
                  ↓
Parts relatives du corridor
                  ↓
Enrichissement IDMC décalé
                  ↓
Construction de applied_t1
                  ↓
Enrichissement avec les noms de pays
                  ↓
Contrôles Data Quality
                  ↓
Export du dataset final
```

### Règles de transformation

1. Les volumes sont d'abord agrégés à la granularité corridor-année.
2. Les lags sont ensuite calculés dans chaque corridor.
3. Les features ne doivent utiliser que des informations disponibles à T ou avant T.
4. Les enrichissements utilisent des jointures conservatrices de type **LEFT JOIN**.
5. Les noms de pays sont descriptifs ; les identifiants sont conservés pour la traçabilité.
6. Les valeurs manquantes structurelles ne sont pas supprimées.
7. `applied_t1` reste séparé des features explicatives.

---

# 10. Prévention du Target Leakage

Le principe de production est :

> **Une variable utilisée pour prédire T+1 doit être calculable au moment T.**

### Variables utilisables comme features

```text
year
coo_id
coa_id
origin_region
asylum_region
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

### Colonnes descriptives

```text
coo_name
coa_name
```

Elles servent principalement à la restitution et au storytelling.

### Variable interdite dans X

```text
applied_t1
```

`applied_t1` contient une information future. Son inclusion dans X provoquerait une fuite de cible.

---

# 11. Construction de la cible Machine Learning

La cible Early Warning n'est pas stockée directement dans ce fichier. Elle est construite dans l'étape Machine Learning à partir de `applied` et `applied_t1`.

La règle retenue est :

```python
target = (
    (applied_t1 >= applied * 1.30)
    &
    ((applied_t1 - applied) >= 100)
)
```

Une observation est donc positive lorsque T+1 présente simultanément :

- une hausse d'au moins **30 %** ;
- une hausse absolue d'au moins **100 demandes**.

Cette double condition évite de considérer comme alerte une très forte croissance relative portant sur un volume absolu très faible.

`applied_t1` doit ensuite être exclu des variables explicatives.

---

# 12. Gestion des valeurs manquantes pour le Machine Learning

La stratégie recommandée est de conserver les NA dans le dataset de Feature Engineering et de traiter l'imputation **après le split temporel**, à l'intérieur du pipeline ML.

```text
Dataset final
    ↓
Split temporel
    ↓
Train / Validation / Test
    ↓
Fit de l'imputation sur Train uniquement
    ↓
Transformation Validation / Test
```

Cette stratégie évite qu'une médiane ou une autre statistique calculée sur le futur influence artificiellement l'entraînement.

Pour les variables numériques, le pipeline ML peut combiner :

```text
SimpleImputer(strategy="median", add_indicator=True)
```

La présence d'un indicateur de valeur manquante permet au modèle de conserver l'information selon laquelle la donnée n'était pas disponible.

---

# 13. Découpage temporel recommandé

Le dataset couvre 2000–2025.

Pour l'évaluation ML du projet :

| Sous-ensemble | Période | Rôle |
|---|---|---|
| **Train** | 2000–2018 | apprentissage |
| **Validation** | 2019–2021 | comparaison des modèles / seuil |
| **Test** | 2022–2024 | évaluation finale |
| **2025** | scoring | données disponibles à T, sans T+1 observable |

Le split doit rester chronologique.

> Un split aléatoire mélangerait passé et futur et ne représenterait pas correctement l'utilisation réelle du système.

---

# 14. Export et stockage

## Format actuel

Le dataset fourni est au format :

```text
CSV
```

Le CSV reste pertinent pour la compatibilité et le partage.

## Format complémentaire recommandé

Pour un stockage Data pérenne, un export **Parquet** est recommandé en complément :

```text
dataset_ml_features.csv
dataset_ml_features.parquet
```

Le Parquet permet notamment de mieux préserver les types et de réduire la taille de stockage.

## Emplacement recommandé

```text
data/
└── feature_engineering_outputs/
    ├── dataset_ml_features.csv
    ├── dataset_ml_features.parquet
    ├── audit_feature_engineering.csv
    └── data_quality_feature_engineering.csv
```

---

# 15. Contrôle après export

Le fichier exporté doit être relu et comparé au DataFrame source.

```python
from pathlib import Path
import pandas as pd

path = Path("../data/feature_engineering_outputs/dataset_ml_features.csv")

df_check = pd.read_csv(path)

assert df_check.shape == (86234, 20)
assert df_check.duplicated(["coo_id", "coa_id", "year"]).sum() == 0
assert df_check["year"].min() == 2000
assert df_check["year"].max() == 2025

print("Export relu et contrôlé avec succès.")
```

Ces assertions correspondent à la version documentée ici. Si le pipeline évolue, les valeurs attendues doivent être mises à jour et historisées.

---

# 16. Traçabilité et versionning

Une convention explicite est recommandée pour les versions diffusées :

```text
dataset_ml_features_v1_YYYYMMDD.csv
dataset_ml_features_v1_YYYYMMDD.parquet
```

Dans le pipeline interne du repository, un nom stable peut être conservé :

```text
data/feature_engineering_outputs/dataset_ml_features.csv
```

Le versionnement du code et de la documentation doit être assuré avec Git. Pour des datasets devenant volumineux, DVC ou un stockage objet versionné peut être envisagé.

---

# 17. Changelog

## v1.0 — Dataset documenté

- construction de la granularité corridor origine × asile × année ;
- conservation des volumes `applied` ;
- création des lags T-1 et T-2 ;
- création des indicateurs de croissance, variation et accélération ;
- création de `two_consecutive_increases` ;
- création des agrégats origine / asile ;
- création des parts relatives du corridor ;
- enrichissement IDMC décalé ;
- création de `applied_t1` pour la construction ultérieure de la cible ;
- ajout des noms de pays pour les restitutions ;
- contrôle de l'unicité de la clé métier ;
- documentation des valeurs manquantes.

---

# 18. Limites et précautions d'interprétation

### Couverture IDMC

`idmc_total_origin_lag1` est manquant pour **64,10 %** des lignes. Cette variable ne doit donc pas être interprétée comme une information universellement disponible.

### Historique des corridors

L'absence de lag ne signifie pas nécessairement qu'aucune demande n'existait auparavant. Elle peut refléter l'absence d'un historique exploitable dans la table à la granularité retenue.

### Valeurs extrêmes

Les volumes extrêmes ne sont pas supprimés automatiquement. Ils peuvent correspondre à des situations réelles importantes pour l'Early Warning.

### Année 2025

`applied_t1` n'est pas disponible pour le scoring 2025 → 2026. Ces lignes ne doivent pas être utilisées comme observations labellisées pour évaluer le modèle.

### Score ML

Le dataset ne contient pas encore le score final de risque. Celui-ci est produit par le pipeline Machine Learning. Il constitue un outil de priorisation et non une certitude de crise.

---

# 19. Checklist de validation de la livraison

## Dataset

- [x] Dataset final exporté en CSV
- [x] 86 234 lignes contrôlées
- [x] 20 colonnes documentées
- [x] Période 2000–2025 vérifiée
- [x] Clé `coo_id × coa_id × year` unique
- [x] Doublons stricts contrôlés
- [x] Valeurs manquantes quantifiées
- [x] Variables temporelles documentées
- [x] `applied_t1` identifié comme information future

## Documentation

- [x] Informations générales
- [x] Sources documentées
- [x] Data Dictionary
- [x] Transformations expliquées
- [x] Data Quality documentée
- [x] Target Leakage documenté
- [x] Limites explicitées
- [x] Stratégie d'export décrite
- [x] Traçabilité et versionning décrits

## Reproductibilité

- [x] Granularité explicitée
- [x] Clé métier explicitée
- [x] Pipeline de transformation décrit
- [x] Contrôle post-export fourni
- [x] Split temporel documenté

---

# 20. Questions de validation avant réutilisation

Avant toute nouvelle utilisation du dataset, quatre questions doivent être posées :

1. **Reproductibilité** — le dataset peut-il être reconstruit à partir des notebooks et des sources documentées ?
2. **Temporalité** — toutes les features utilisées pour une prédiction à T sont-elles réellement disponibles à T ?
3. **Qualité** — les taux de valeurs manquantes et la couverture des sources ont-ils changé ?
4. **Usage métier** — la définition de l'escalade et les seuils de priorisation sont-ils toujours cohérents avec le besoin analyste ?

---

# 21. Conclusion

Le dataset `dataset_ml_features` constitue le **contrat de données entre le Feature Engineering et les étapes analytiques / Machine Learning**.

Sa valeur ne repose pas uniquement sur le nombre de features produites. Elle repose surtout sur quatre garanties :

```text
Granularité maîtrisée
        +
Traçabilité des transformations
        +
Respect strict de la temporalité
        +
Qualité mesurée et documentée
```

La présence de valeurs manquantes est explicitée plutôt que masquée, les anomalies ne sont pas supprimées silencieusement et l'information future `applied_t1` est clairement séparée des variables prédictives.

Cette documentation doit évoluer avec le dataset. Toute modification de granularité, de définition d'une feature, de source, de période ou de règle de cible doit entraîner une mise à jour du Data Dictionary et du changelog.
