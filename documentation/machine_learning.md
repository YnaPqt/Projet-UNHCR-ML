# Documentation — Machine Learning : scoring d’alerte Early Warning

## 1. Objectif

Cette étape correspond à la phase de Machine Learning du projet, après le nettoyage, la normalisation, la consolidation, l’analyse exploratoire et le Feature Engineering.

L’objectif est d’utiliser les informations disponibles à l’année **T** pour estimer le risque qu’un corridor **pays d’origine → pays d’asile** connaisse une hausse importante des demandes d’asile à **T+1**.

Le modèle n’est pas conçu pour prendre une décision automatiquement. Il sert à **prioriser les corridors à examiner par les analystes**.

> **Le modèle priorise. L’analyste interprète. L’humain décide.**

## 2. Dataset utilisé

Le notebook utilise le fichier `dataset_ml_features.csv`.

Le dataset contient **86 234 observations**, couvre la période **2000–2025** et conserve un grain correspondant à **un corridor (`coo_id`, `coa_id`) × une année (`year`)**.

Les contrôles préalables donnent :

| Contrôle | Résultat |
|---|---:|
| Doublons corridor–année | 0 |
| Valeurs négatives de `applied` | 0 |
| Valeurs manquantes de `applied` | 0 |
| Valeurs manquantes de `applied_t1` | 3 967 |

Les observations sans `applied_t1` ne peuvent pas être utilisées pour entraîner ou évaluer le modèle, car l’information future nécessaire à la construction de la cible n’est pas disponible.

### Point de vigilance sur `app_pc`

La variable `applied` correspond au volume présent dans les données sources. `app_pc` apporte une information descriptive sur le type de comptage (`P` ou `C`), mais n’est pas utilisée comme feature du modèle.

Lors de la préparation des données, les volumes sont agrégés au grain corridor × année. Ce point doit rester surveillé en amont afin de vérifier qu’une même population n’est pas comptabilisée deux fois lorsque plusieurs modalités de comptage existent.

## 3. Construction de la cible

La cible cherche à identifier une **escalade des demandes d’asile à T+1**.

Une observation est considérée comme une escalade lorsque deux conditions sont simultanément respectées :

- augmentation relative d’au moins **30 %** ;
- augmentation absolue d’au moins **100 demandes**.

```text
target_escalade = 1
si applied_t1 >= applied × 1,30
ET applied_t1 - applied >= 100
```

Lorsque `applied_t1` est absent, la cible reste manquante. Une observation dont le futur n’est pas disponible ne doit pas être assimilée à une absence d’escalade.

Après construction de la cible :

- **82 267 observations** sont labellisées ;
- **3 967 observations** restent sans label T+1.

| Classe | Nombre | Part |
|---|---:|---:|
| Pas d’escalade | 75 800 | 92,14 % |
| Escalade | 6 467 | 7,86 % |

## 4. Choix des métriques

L’accuracy n’est pas utilisée comme métrique principale. Avec plus de 92 % d’observations dans la classe 0, un modèle prédisant presque toujours « pas d’escalade » pourrait obtenir une accuracy élevée sans être utile.

Les métriques suivies sont :

- **Recall** : proportion des vraies escalades détectées ;
- **Precision** : proportion des alertes qui correspondent réellement à une escalade ;
- **F1-score** : compromis entre Precision et Recall ;
- **PR-AUC** : métrique principale de comparaison ;
- **ROC-AUC** : mesure complémentaire ;
- **Balanced Accuracy** : équilibre de performance entre les deux classes ;
- **matrice de confusion** : lecture directe des faux positifs et faux négatifs.

Dans le cadre d’un outil Early Warning, le Recall est particulièrement important car un faux négatif correspond à une escalade non détectée.

## 5. Split chronologique

Le problème étant temporel, aucun split aléatoire n’est utilisé.

| Ensemble | Période | Nombre de lignes | Taux d’escalade |
|---|---|---:|---:|
| Train | 2000–2018 | 59 649 | 7,45 % |
| Validation | 2019–2021 | 10 564 | 9,35 % |
| Test | 2022–2024 | 12 054 | 8,60 % |

L’année 2025 n’est pas utilisée dans le Test car T+1 n’est pas encore disponible.

- **Train** : apprentissage et tuning ;
- **Validation** : comparaison des modèles et analyse du seuil ;
- **Test** : évaluation finale.

## 6. Prévention du data leakage

Seules les informations disponibles à T ou avant T sont utilisées comme features.

Les variables explicitement interdites sont :

- `applied_t1` ;
- `absolute_change_t1` ;
- `target_escalade`.

Le modèle utilise **17 features**, réparties entre niveau courant, historique, dynamique temporelle, contexte des flux, informations géographiques et IDMC.

## 7. Valeurs manquantes et prétraitement

Les variables historiques présentent des valeurs manquantes naturelles lorsqu’un corridor ne dispose pas encore d’un historique suffisant.

| Feature | Valeurs manquantes |
|---|---:|
| `idmc_total_origin_lag1` | 71,68 % |
| `acceleration` | 36,22 % |
| `two_consecutive_increases` | 36,22 % |
| `applied_lag2` | 30,97 % |
| `growth_past_1` | 23,77 % |
| `absolute_change_past_1` | 23,77 % |
| `applied_lag1` | 23,77 % |

Pour les variables numériques : imputation par médiane, indicateurs de valeurs manquantes et standardisation.

Pour les variables catégorielles : remplacement par `MISSING`, One-Hot Encoding et `handle_unknown="ignore"`.

Toutes les transformations sont intégrées dans un `Pipeline` appris uniquement sur le Train.

## 8. Gestion du déséquilibre

Dans le Train :

- classe 0 : **55 207 observations** ;
- classe 1 : **4 442 observations** ;
- taux positif : **7,45 %**.

La stratégie choisie consiste à pondérer la classe minoritaire :

- Régression Logistique : `class_weight="balanced"` ;
- Random Forest : `class_weight="balanced"` ;
- XGBoost : `scale_pos_weight = 12,43`.

SMOTE n’est pas utilisé à ce stade afin de conserver un pipeline temporel simple et interprétable.

## 9. Modèles comparés

Quatre modèles sont d’abord entraînés : Dummy Classifier, Régression Logistique, Random Forest et XGBoost.

### Résultats initiaux sur Validation

| Modèle | Precision | Recall | F1 | PR-AUC | ROC-AUC | Balanced Accuracy |
|---|---:|---:|---:|---:|---:|---:|
| Random Forest | 0,237 | 0,827 | 0,368 | **0,259** | 0,826 | 0,776 |
| XGBoost | 0,241 | 0,790 | 0,369 | **0,257** | 0,820 | 0,767 |
| Régression Logistique | 0,184 | 0,684 | 0,290 | 0,193 | 0,741 | 0,686 |
| Dummy Baseline | 0,000 | 0,000 | 0,000 | 0,094 | 0,500 | 0,500 |

Random Forest et XGBoost sont retenus pour l’optimisation.

## 10. Tuning temporel

Une validation croisée temporelle à **3 plis expansifs** est utilisée :

- Train jusqu’en 2012 → Validation 2013–2014 ;
- Train jusqu’en 2014 → Validation 2015–2016 ;
- Train jusqu’en 2016 → Validation 2017–2018.

| Fold | Train | Validation |
|---|---:|---:|
| 1 | 37 972 | 6 954 |
| 2 | 44 926 | 7 182 |
| 3 | 52 108 | 7 541 |

Le choix de 3 plis plutôt que `cv=5` est volontaire : la priorité est de respecter l’ordre temporel et de conserver des fenêtres suffisamment longues et interprétables.

### Meilleurs hyperparamètres

**Random Forest**

```text
max_depth = 15
min_samples_leaf = 10
n_estimators = 200
```

**XGBoost**

```text
learning_rate = 0.03
max_depth = 5
n_estimators = 150
```

PR-AUC moyenne en validation croisée interne : Random Forest **0,2915**, XGBoost **0,2881**.

## 11. Comparaison après tuning

| Modèle | Precision | Recall | F1 | PR-AUC | ROC-AUC | Balanced Accuracy |
|---|---:|---:|---:|---:|---:|---:|
| Random Forest | 0,241 | 0,810 | 0,372 | **0,261** | 0,827 | 0,774 |
| XGBoost | 0,235 | 0,816 | 0,365 | 0,250 | 0,819 | 0,771 |

Le **Random Forest** est retenu comme modèle final.

Le tuning améliore légèrement la PR-AUC du Random Forest, de **0,259 à 0,261**. Le gain est donc limité.

### Écart Train / Validation

| Modèle | PR-AUC Train | PR-AUC Validation | Écart |
|---|---:|---:|---:|
| Random Forest | 0,407 | 0,261 | 0,146 |
| XGBoost | 0,378 | 0,250 | 0,128 |

Pour Random Forest, l’écart rapporté au volume de Validation représente un ordre de grandeur d’environ **1 537 lignes**. Ce calcul est seulement un indicateur de lecture et ne correspond pas directement à un nombre d’erreurs de classification.

## 12. Choix du seuil

Le seuil est étudié uniquement sur la Validation avec le **F2-score**.

Le meilleur seuil trouvé est **0,50**.

Ce point doit être dit explicitement : **0,50 est également le seuil par défaut**. Le réglage du seuil n’apporte donc aucun gain supplémentaire dans cette expérience.

Une limite méthodologique reste présente : le modèle final et le seuil sont choisis sur la même Validation 2019–2021. Pour une mise en production, une fenêtre temporelle dédiée au calibrage du seuil ou une validation temporelle imbriquée serait préférable.

## 13. Évaluation finale sur Test

Le Test couvre la période **2022–2024**.

| Métrique | Résultat |
|---|---:|
| Precision | **0,215** |
| Recall | **0,828** |
| F1 | 0,341 |
| PR-AUC | **0,249** |
| ROC-AUC | **0,825** |
| Balanced Accuracy | **0,771** |

Le Recall de **82,8 %** signifie qu’environ 83 escalades réelles sur 100 sont détectées.

Il reste **178 faux négatifs** sur le Test.

La Precision de **21,5 %** signifie que le modèle génère aussi de nombreux faux positifs. Cela confirme son rôle d’outil de tri plutôt que de système de décision automatique.

## 14. Importance des features

La contribution des variables est étudiée avec la **Permutation Importance** sur la Validation.

| Feature | Importance moyenne |
|---|---:|
| `applied` | 0,0110 |
| `applied_lag1` | 0,0076 |
| `applied_lag2` | 0,0025 |
| `origin_applied_total_t` | 0,0024 |
| `acceleration` | 0,0019 |
| `asylum_applied_total_t` | 0,0019 |
| `segment_share_asylum_t` | 0,0017 |
| `growth_past_1` | 0,0012 |
| `coo_name` | 0,0011 |
| `idmc_total_origin_lag1` | 0,0005 |

L’importance prédictive ne constitue pas une preuve de causalité.

## 15. Retour sur les hypothèses

| Hypothèse | Conclusion |
|---|---|
| H1 — Le volume courant apporte un signal prédictif | **Soutenue** : `applied` est la feature la plus importante. |
| H2 — Les variables temporelles améliorent la détection | **Soutenue** : les lags, la croissance et l’accélération apportent un signal. |
| H3 — La géographie améliore la discrimination | **Faiblement soutenue** : contribution limitée face aux volumes et à la dynamique. |
| H4 — IDMC apporte un signal supplémentaire | **Peu soutenue** avec les données actuelles ; couverture très incomplète. |
| H5 — Les modèles non linéaires captent mieux les interactions | **Soutenue** : Random Forest et XGBoost dépassent la Régression Logistique. |

## 16. Sauvegarde du modèle

Le pipeline final est sauvegardé sous :

`../model/best_model_random_forest.joblib`

Le fichier contient le prétraitement et le modèle entraîné.

Une vérification de portabilité recharge le fichier avec `joblib` puis applique directement le pipeline à des lignes non prétraitées provenant de `X_test`.

Cette vérification montre que le pipeline peut être réutilisé sur des données ayant déjà le même schéma de features que `dataset_ml_features.csv`. Elle ne constitue pas encore une prédiction directement à partir des fichiers bruts issus des API.

## 17. Transformation en outil de priorisation

Le modèle final est utilisé comme **outil d’aide à la priorisation pour analystes**.

Le score répond à la question :

> **Quels corridors dois-je examiner en premier ?**

Il ne répond pas seul à :

> **Que va-t-il réellement se passer ?**

La décision finale doit être complétée par le contexte politique, les conflits, les déplacements internes, les événements récents, les données terrain et l’expertise des analystes.

## 18. Scoring des corridors 2025

L’année **2025** est utilisée comme année de scoring pour produire une file de priorisation destinée à l’analyse de **T+1 = 2026**.

`applied_t1` n’intervient jamais dans le calcul.

Résultats :

- **3 967 corridors scorés** ;
- score minimum : **5,3** ;
- score médian : **24,9** ;
- score maximum : **86,4**.

Le score de 0 à 100 est un **score de priorisation**, et non une certitude de crise ni une probabilité parfaitement calibrée.

### Niveaux de priorité

| Score | Priorité | Action proposée |
|---:|---|---|
| 75–100 | Critique | Analyse prioritaire |
| 55–74 | Élevée | À examiner |
| 30–54 | Attention | Surveillance renforcée |
| 0–29 | Faible | Suivi standard |

La file complète est exportée dans :

`../data/processed/priorisation_corridors_2025.csv`

## 19. Principaux enseignements

### Le modèle apporte un signal réel

La PR-AUC passe de **0,094 pour la Dummy Baseline à 0,261 pour le Random Forest optimisé sur Validation**.

### La dynamique des demandes est plus informative que la géographie

Les variables les plus utiles sont principalement le volume actuel, l’historique des demandes et leur dynamique récente.

### Le Random Forest généralise correctement

La PR-AUC passe de **0,261 sur Validation à 0,249 sur Test**, tandis que la ROC-AUC reste pratiquement stable, de **0,827 à 0,825**.

### Le principal compromis reste les faux positifs

Le Recall est élevé (**82,8 %**), mais la Precision reste faible (**21,5 %**). Le modèle est donc plus adapté à un rôle de **priorisation** qu’à une prise de décision automatique.

## 20. Limites

1. **Choix du modèle et du seuil sur la même Validation** : la Validation 2019–2021 sert aux deux décisions.
2. **Aucun gain lié au réglage du seuil** : le meilleur seuil F2 reste 0,50.
3. **Validation croisée à trois plis** : choix volontaire lié au caractère temporel.
4. **Comptage `app_pc` / `app_type` à surveiller en amont** afin d’éviter un éventuel double comptage.
5. **Couverture IDMC incomplète** : 71,68 % de valeurs manquantes pour `idmc_total_origin_lag1` dans le Train.
6. **Score non calibré comme probabilité métier** : il sert à classer les corridors.
7. **Prototype, pas système de production** : les performances historiques ne suffisent pas pour valider un usage opérationnel.

## 21. Pipeline final

```text
Dataset validé
      ↓
Construction du label
      ↓
Analyse du déséquilibre
      ↓
Split chronologique Train / Validation / Test
      ↓
Contrôle du data leakage
      ↓
Prétraitement
      ↓
Dummy + Logistic Regression + Random Forest + XGBoost
      ↓
Comparaison sur Validation
      ↓
Sélection Random Forest / XGBoost
      ↓
Tuning avec validation temporelle
      ↓
Random Forest final
      ↓
Analyse du seuil
      ↓
Évaluation finale sur Test
      ↓
Permutation Importance
      ↓
Analyse H1–H5
      ↓
Sauvegarde du pipeline
      ↓
Scoring 2025
      ↓
Priorisation des corridors pour 2026
      ↓
Analyse humaine
```

## 22. Conclusion

Cette phase montre qu’il est possible d’exploiter l’historique des demandes d’asile pour produire un signal Early Warning utile à la priorisation.

Le Random Forest final obtient sur le Test :

- **Recall : 82,8 %** ;
- **Precision : 21,5 %** ;
- **PR-AUC : 0,249** ;
- **ROC-AUC : 0,825**.

Ces résultats ne justifient pas une automatisation de la décision. En revanche, ils permettent de construire une **file de priorisation** qui aide les analystes à concentrer leur attention sur les corridors présentant les signaux les plus importants.

> **Priorisation quantitative par le modèle + validation contextuelle par l’analyste.**
