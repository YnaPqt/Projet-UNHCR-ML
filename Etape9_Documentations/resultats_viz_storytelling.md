# Documentation — Résultats de la visualisation et du storytelling

## Early Warning des demandes d’asile — Préparation à la modélisation Machine Learning

---

## 1. Objectif de l’analyse

Cette phase de visualisation et de storytelling précède volontairement la modélisation Machine Learning.

L’objectif est de comprendre les données et d’identifier les signaux historiques potentiellement utiles pour répondre à la question métier suivante :

> **Quels signaux disponibles à l’année T permettent d’identifier les corridors origine → pays d’asile susceptibles de connaître une hausse significative des demandes d’asile à T+1 ?**

L’unité d’analyse est le **corridor–année** :

**pays d’origine (`coo`) × pays d’asile (`coa`) × année (`year`)**.

Cette analyse est exploratoire. Les relations observées sont des **associations statistiques dans le dataset** et ne permettent pas, à elles seules, d’établir des relations causales.

---

## 2. Périmètre et qualité générale des données

Le dataset utilisé pour cette analyse contient :

- **86 234 corridor-années** ;
- une période allant de **2000 à 2025** ;
- **aucun doublon** sur la clé `(coo_id, coa_id, year)` ;
- aucune valeur négative dans `applied` ;
- aucune valeur manquante dans `applied`.

Ces contrôles confirment que la granularité attendue — un corridor par année — est respectée dans le fichier analysé.

### Point temporel important

La variable `applied_t1` représente le nombre de demandes observées l’année suivante.

Pour les observations de **2025**, T+1 n’est pas disponible dans le dataset. Ces observations ne doivent donc pas être considérées comme des cas « sans alerte ».

Elles sont simplement **non labellisées** pour la cible à T+1.

---

# 3. Acte 1 — Un phénomène fortement variable dans le temps

## 3.1 Évolution récente du volume total

Les demandes d’asile présentent des variations importantes d’une année à l’autre.

Quelques résultats observés dans le dataset :

| Année | Demandes | Évolution annuelle |
|---:|---:|---:|
| 2019 | 2 245 518 | +7,4 % |
| 2020 | 1 269 579 | -43,5 % |
| 2021 | 1 724 859 | +35,9 % |
| 2022 | 2 904 909 | +68,4 % |
| 2023 | 3 848 894 | +32,5 % |
| 2024 | 3 421 776 | -11,1 % |
| 2025 | 3 343 203 | -2,3 % |

### Insight

Le volume global ne suit pas une progression régulière.

La succession de fortes baisses et de fortes augmentations montre qu’une simple extrapolation de la tendance précédente serait insuffisante pour représenter toute la dynamique observée.

### Limite d’interprétation

Le dataset permet de **mesurer** ces changements, mais pas d’en identifier directement les causes.

Cette analyse ne permet donc pas d’affirmer pourquoi une année donnée augmente ou diminue sans introduire d’autres sources de données.

---

# 4. Acte 2 — Le phénomène est également très hétérogène géographiquement

## 4.1 Principaux pays d’origine en volume cumulé

Parmi les volumes cumulés les plus importants observés dans le dataset figurent notamment :

| Pays d’origine | Demandes cumulées |
|---|---:|
| Afghanistan | ≈ 2,75 M |
| Venezuela | ≈ 2,39 M |
| Syrian Arab Rep. | ≈ 2,34 M |
| Iraq | ≈ 1,65 M |
| Unknown | ≈ 1,50 M |
| Sudan | ≈ 1,44 M |

La catégorie `Unknown` doit être interprétée comme un problème ou une limite d’identification géographique et non comme un pays ou une région réelle.

## 4.2 Principaux pays d’asile en volume cumulé

Les volumes cumulés les plus élevés apparaissent notamment pour :

| Pays d’asile | Demandes cumulées |
|---|---:|
| United States of America | ≈ 6,25 M |
| Germany | ≈ 4,89 M |
| France | ≈ 3,13 M |
| United Kingdom | ≈ 1,85 M |
| South Africa | ≈ 1,55 M |

### Insight

Les demandes ne sont pas uniformément réparties entre les pays.

Un total mondial masque donc une forte hétérogénéité entre les routes migratoires observées.

Cela soutient le choix du **corridor origine → pays d’asile** comme unité d’analyse pour le système Early Warning.

---

# 5. Acte 3 — Définition opérationnelle d’une alerte

L’objectif du projet n’est pas uniquement de repérer les corridors ayant un volume élevé.

Il s’agit d’identifier les corridors susceptibles de connaître une **hausse significative l’année suivante**.

La cible est définie par la règle suivante :

```text
target_escalade = 1

si :

applied_t1 >= applied × 1,30

ET

applied_t1 - applied >= 100
```

Autrement dit, une alerte nécessite simultanément :

1. une augmentation relative d’au moins **30 %** ;
2. une augmentation absolue d’au moins **100 demandes**.

### Pourquoi utiliser deux conditions ?

La condition relative détecte une accélération importante.

La condition absolue évite qu’une très forte hausse en pourcentage sur un corridor extrêmement petit soit automatiquement considérée comme une escalade importante.

Cette définition est une **règle métier du projet**. Elle ne constitue pas une vérité universelle sur les déplacements ou les demandes d’asile.

---

# 6. Acte 4 — Les situations d’alerte sont rares

Parmi les observations pour lesquelles T+1 est disponible :

- **82 267** corridor-années sont labellisées ;
- **6 467** sont classées en alerte ;
- soit environ **7,86 %** de la population labellisée.

La classe négative représente donc environ **92,14 %** des observations.

### Insight

Le futur problème ML est un problème de **classification déséquilibrée**.

Une accuracy élevée ne suffira pas à démontrer qu’un modèle Early Warning fonctionne correctement.

Par exemple, un modèle favorisant systématiquement la classe majoritaire pourrait obtenir une accuracy apparemment élevée tout en détectant très peu de véritables alertes.

### Conséquence pour la modélisation

L’évaluation devra notamment considérer :

- le **recall** de la classe `1` ;
- la **precision** ;
- le **F1-score** ;
- la **PR-AUC** ;
- la matrice de confusion ;
- éventuellement la balanced accuracy comme métrique complémentaire.

Dans un système d’alerte, une attention particulière devra être portée aux **faux négatifs**, c’est-à-dire aux véritables escalades non détectées.

---

# 7. Acte 5 — Le volume actuel du corridor contient un signal important

Le taux d’alerte à T+1 varie fortement selon le volume de demandes observé à T.

| Volume à T | Taux d’alerte à T+1 |
|---|---:|
| 1–10 | ≈ 0,8 % |
| 11–50 | ≈ 2,9 % |
| 51–100 | ≈ 9,1 % |
| 101–500 | ≈ 19,9 % |
| 501–1 000 | ≈ 26,5 % |
| 1 001–5 000 | ≈ 24,5 % |
| > 5 000 | ≈ 21,1 % |

### Insight principal

Le taux d’alerte augmente fortement lorsque l’on passe des très petits corridors aux corridors de taille intermédiaire ou importante.

Cependant, la relation n’est **pas strictement linéaire**.

Le taux atteint environ 26,5 % pour la classe `501–1 000`, puis diminue légèrement dans les catégories supérieures.

Il serait donc incorrect de conclure :

> « Plus le volume est élevé, plus le risque augmente systématiquement. »

### Point méthodologique essentiel

Cette relation est en partie influencée par la définition de la cible.

Puisqu’une alerte exige une augmentation absolue d’au moins 100 demandes, les très petits corridors ont mécaniquement plus de difficulté à satisfaire cette condition.

`applied` reste donc une variable potentiellement importante, mais son association avec la cible doit être interprétée conjointement avec la règle de labellisation.

---

# 8. Acte 6 — La croissance récente apporte un signal supplémentaire

Le taux d’alerte futur varie également selon `growth_past_1`.

| Croissance passée | Taux d’alerte futur |
|---|---:|
| ≤ -50 % | ≈ 7,3 % |
| -50 à -10 % | ≈ 7,2 % |
| -10 à 0 % | ≈ 5,2 % |
| 0 à 10 % | ≈ 12,1 % |
| 10 à 50 % | ≈ 9,8 % |
| 50 à 100 % | ≈ 11,3 % |
| > 100 % | ≈ 15,1 % |

Le taux d’alerte global est d’environ **7,86 %**.

### Insight

Les corridors ayant connu certaines hausses récentes présentent une fréquence d’alerte future supérieure à la moyenne.

La catégorie supérieure à +100 % atteint notamment environ **15,1 %**.

Cependant, la relation n’est pas parfaitement monotone.

Par exemple, la catégorie `0 à 10 %` présente un taux d’alerte supérieur à la catégorie `10 à 50 %`.

### Conclusion

`growth_past_1` contient de l’information, mais une règle fondée uniquement sur la croissance passée ne semble pas suffisante.

Ce résultat constitue un argument en faveur d’un modèle capable de combiner plusieurs signaux.

---

# 9. Acte 7 — La persistance des hausses semble informative

La variable `two_consecutive_increases` permet d’examiner si une hausse répétée sur plusieurs périodes est associée à une nouvelle hausse significative à T+1.

Résultats observés :

- sans deux hausses consécutives : taux d’alerte ≈ **8,6 %** ;
- avec deux hausses consécutives : taux d’alerte ≈ **15,3 %**.

Dans les observations disponibles pour cette variable, la fréquence d’alerte est donc environ **1,8 fois plus élevée** lorsqu’un corridor présente deux hausses consécutives.

### Insight

La dynamique temporelle semble apporter davantage d’information que la seule photographie du volume courant.

Une hausse persistante peut constituer un signal utile pour la future classification.

Cela soutient l’utilisation de variables telles que :

- `applied_lag1` ;
- `applied_lag2` ;
- `growth_past_1` ;
- `absolute_change_past_1` ;
- `acceleration` ;
- `two_consecutive_increases`.

### Précaution

Il s’agit d’une **association observée**, et non de la preuve que deux hausses successives causent une future escalade.

---

# 10. Acte 8 — Le contexte régional apporte également de l’information

Le taux d’alerte varie selon la région d’origine.

Parmi les groupes observés, certaines régions présentent des taux supérieurs au taux global de 7,86 %, notamment :

- `SOUTHERN ASIA` : ≈ **11,2 %** ;
- `SOUTH AMERICA` : ≈ **9,5 %** ;
- `CENTRAL AMERICA` : ≈ **9,5 %** ;
- `EASTERN AFRICA` : ≈ **9,2 %**.

La catégorie `UNKNOWN` présente un taux encore plus élevé, mais elle ne doit pas être interprétée comme une véritable région.

### Insight

La fréquence historique des alertes n’est pas identique dans tous les contextes géographiques du dataset.

Les variables géographiques peuvent donc contenir une information utile au modèle.

### Limite

Cette observation ne permet pas de conclure qu’une région « cause » une escalade.

Il faudra également surveiller le risque qu’un modèle apprenne excessivement les identités historiques des pays ou régions au lieu d’apprendre des dynamiques généralisables.

---

# 11. Acte 9 — La disponibilité des données constitue une limite importante

Plusieurs features historiques présentent des valeurs manquantes.

| Variable | Valeurs manquantes |
|---|---:|
| `idmc_total_origin_lag1` | ≈ 64,1 % |
| `acceleration` | ≈ 33,9 % |
| `two_consecutive_increases` | ≈ 33,9 % |
| `applied_lag2` | ≈ 28,3 % |
| `applied_lag1` | ≈ 22,4 % |
| `growth_past_1` | ≈ 22,4 % |
| `absolute_change_past_1` | ≈ 22,4 % |

### Interprétation

Pour les variables temporelles, une partie des valeurs manquantes peut être cohérente avec l’absence d’un historique suffisant pour certains corridors.

Par exemple, le calcul d’un `lag2` nécessite de disposer d’une observation antérieure correspondante.

Cependant, l’analyse actuelle ne permet pas d’affirmer que **toutes** les valeurs manquantes proviennent uniquement de cette situation.

### Cas particulier d’IDMC

`idmc_total_origin_lag1` présente environ **64,1 % de valeurs manquantes**.

Il s’agit d’un niveau de missingness suffisamment important pour nécessiter une décision explicite avant la modélisation.

Il faudra notamment vérifier :

- la couverture temporelle ;
- la couverture par pays ;
- la signification réelle d’une valeur manquante ;
- si une imputation est justifiable ;
- si un indicateur de missingness est utile ;
- ou si cette variable doit être exclue de certains modèles/tests.

---

# 12. L’histoire générale racontée par les données

Les visualisations permettent maintenant de construire une histoire cohérente.

Les demandes d’asile observées dans le dataset présentent une **forte variabilité temporelle** et une **forte hétérogénéité géographique**.

Mais un système Early Warning ne cherche pas simplement à identifier les pays ou corridors ayant les volumes les plus importants. Son objectif est de détecter suffisamment tôt les corridors susceptibles de connaître une **augmentation significative l’année suivante**.

Ces événements sont relativement rares : environ **7,86 %** des corridor-années labellisées satisfont la définition retenue de l’escalade.

Plusieurs signaux apparaissent dans les données :

1. **le volume actuel du corridor est fortement associé au taux d’alerte**, mais cette relation n’est pas linéaire et est partiellement liée à la définition de la cible ;
2. **la croissance récente apporte de l’information**, mais elle ne constitue pas à elle seule une règle de décision suffisante ;
3. **la persistance des hausses semble particulièrement informative**, avec un taux d’alerte plus élevé lorsque deux augmentations successives ont déjà été observées ;
4. **le contexte géographique est associé à des fréquences d’alerte différentes** ;
5. plusieurs variables historiques présentent toutefois une **couverture incomplète**, ce qui devra être traité explicitement.

L’information utile semble donc répartie entre plusieurs dimensions :

**niveau actuel + historique + dynamique récente + persistance + contexte géographique.**

---

# 13. Pourquoi passer au Machine Learning ?

L’EDA ne montre pas une variable unique permettant de séparer simplement les futures alertes des situations normales.

Au contraire, les résultats suggèrent que plusieurs signaux complémentaires doivent être considérés simultanément.

La question de modélisation devient donc :

> **Peut-on combiner les informations disponibles à l’année T pour estimer la probabilité qu’un corridor connaisse une hausse significative des demandes d’asile à T+1 ?**

Le Machine Learning est utilisé ici pour rechercher une combinaison de ces signaux, et non pour remplacer l’analyse exploratoire.

---

# 14. Conséquences méthodologiques pour le notebook Machine Learning

Les résultats de cette analyse imposent plusieurs règles pour la phase suivante.

## 14.1 Respecter la temporalité

Le problème est temporel :

**informations à T → prédiction de T+1**

Le découpage Train / Validation / Test devra donc être **chronologique**, et non aléatoire.

Un split aléatoire risquerait de mélanger passé et futur et de produire une évaluation trop optimiste.

---

## 14.2 Éviter toute fuite de données

Les variables décrivant directement T+1 ne doivent jamais être utilisées comme features.

En particulier :

```text
applied_t1
target_escalade
```

et toute autre variable calculée à partir d’informations futures doivent être exclues de `X`.

`applied_t1` sert uniquement à construire le label pendant l’entraînement et l’évaluation historique.

---

## 14.3 Contrôler la cible avant l’entraînement

Avant de lancer les modèles, le notebook ML devra vérifier :

- la distribution de la cible ;
- le nombre de positifs et négatifs ;
- sa distribution dans Train / Validation / Test ;
- l’absence de labels non observables ;
- l’absence de fuite temporelle.

---

## 14.4 Traiter explicitement les valeurs manquantes

Les missing values ne doivent pas être supprimées ou imputées automatiquement sans justification.

Le traitement devra dépendre de leur origine et du modèle utilisé.

Le cas `idmc_total_origin_lag1` devra notamment faire l’objet d’une décision spécifique.

---

## 14.5 Commencer par une baseline

Avant les modèles complexes, une baseline doit établir le niveau minimal de référence.

Elle permettra de vérifier si les modèles apprennent réellement quelque chose au-delà de la classe majoritaire.

---

## 14.6 Comparer plusieurs familles de modèles avant optimisation

Une séquence cohérente serait :

1. **Baseline** ;
2. **Logistic Regression** ;
3. **Random Forest** ;
4. **XGBoost** ou autre modèle de boosting adapté.

Les modèles doivent d’abord être entraînés avec des paramètres raisonnables, **sans tuning intensif**.

Les performances sont ensuite comparées sur le jeu de validation.

---

## 14.7 N’optimiser que les meilleurs modèles

Après comparaison initiale :

- sélectionner les deux modèles les plus prometteurs sur la validation ;
- effectuer une optimisation ciblée ;
- comparer à nouveau les résultats sur la validation ;
- choisir le modèle final ;
- seulement ensuite effectuer l’évaluation finale sur le jeu de test.

Le jeu de test ne doit pas servir à choisir les hyperparamètres.

---

## 14.8 Choisir des métriques adaptées au problème métier

Compte tenu du déséquilibre de la cible, l’évaluation devra notamment inclure :

- Recall ;
- Precision ;
- F1-score ;
- PR-AUC ;
- ROC-AUC en complément ;
- Balanced Accuracy ;
- matrice de confusion.

La métrique prioritaire devra être choisie en fonction du coût métier relatif :

- d’une **alerte manquée** ;
- d’une **fausse alerte**.

---

# 15. Hypothèses à tester pendant la modélisation

L’EDA conduit à plusieurs hypothèses de travail, qui devront être testées plutôt que considérées comme acquises.

### H1 — Le volume courant apporte un signal prédictif

`applied` est associé au taux d’alerte, mais sa relation avec la cible semble non linéaire.

### H2 — Les variables temporelles améliorent la détection

Les lags, la croissance, l’accélération et la persistance pourraient apporter une information complémentaire au volume courant.

### H3 — Les informations géographiques améliorent la discrimination

Les régions et éventuellement les identifiants de pays pourraient apporter un signal, mais leur capacité à généraliser devra être contrôlée.

### H4 — IDMC peut apporter un signal externe supplémentaire

Cette hypothèse ne pourra être correctement évaluée qu’après avoir traité son importante couverture manquante.

### H5 — Les modèles non linéaires pourraient mieux représenter certaines interactions

L’EDA montre plusieurs relations non monotones. Cette hypothèse justifie la comparaison entre une régression logistique et des modèles basés sur les arbres, sans présumer à l’avance lequel sera supérieur.

---

# 16. Conclusion

La phase de visualisation et de storytelling ne permet pas encore de conclure qu’un modèle prédictif sera suffisamment performant pour une utilisation opérationnelle.

Elle permet cependant d’établir plusieurs éléments essentiels avant la modélisation :

- la cible est **rare et déséquilibrée** ;
- le problème est **temporel** ;
- le volume actuel apporte un signal important mais insuffisant ;
- les dynamiques passées et leur persistance apportent des informations complémentaires ;
- le contexte géographique est associé à des différences de fréquence d’alerte ;
- certaines variables présentent une couverture incomplète importante ;
- aucun indicateur isolé observé dans cette EDA ne constitue à lui seul une règle d’alerte satisfaisante.

La prochaine étape consiste donc à construire un pipeline Machine Learning rigoureux permettant de déterminer si ces différents signaux peuvent être combinés pour anticiper les escalades à T+1, tout en respectant strictement la temporalité et en évitant toute fuite de données.
