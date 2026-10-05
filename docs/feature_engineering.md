# Documentation du Feature Engineering — Early Warning

## 1. Objectif

Le Feature Engineering prépare un jeu de données au niveau **corridor × année** afin de permettre à un modèle de Machine Learning d'identifier les corridors susceptibles de connaître une **hausse significative des demandes des demandes d'asile à T+1**.

L'unité d'analyse est :

> **`coo_id × coa_id × year`**

où :

- `coo_id` = pays d'origine ;
- `coa_id` = pays d'asile ;
- `year` = année d'observation T.

Le Feature Engineering ne cherche pas à prédire directement le nombre exact de demandes à T+1. Il prépare les informations disponibles à T pour construire ensuite une cible d'Early Warning.

---

## 2. Principe temporel

Une règle fondamentale est appliquée :

> **Une feature utilisée par le modèle doit être calculable à la date T, avant l'observation de T+1.**

La variable `applied_t1` sert uniquement à construire la cible supervisée. Elle **ne doit jamais être utilisée comme feature du modèle**.

Pour les observations de 2025, T+1 correspondrait à 2026. Comme 2026 n'est pas disponible dans les données, ces lignes restent non labellisées.

---

# 3. Définition de la cible métier

La définition retenue pour l'Early Warning est :

> **hausse significative des demandes = augmentation d'au moins 30 % ET augmentation d'au moins 100 demandes entre T et T+1.**

Formellement :

```text
applied_t1 >= applied × 1,30
ET
(applied_t1 - applied) >= 100
```

### Exemples

| T | T+1 | Variation | Variation absolue | Escalade |
|---:|---:|---:|---:|:---:|
| 10 | 15 | +50 % | +5 | Non |
| 100 | 130 | +30 % | +30 | Non |
| 100 | 200 | +100 % | +100 | Oui |
| 1 000 | 1 300 | +30 % | +300 | Oui |
| 1 000 | 1 250 | +25 % | +250 | Non |

Cette règle permet d'éviter qu'une très forte croissance relative sur un très petit volume soit considérée automatiquement comme une alerte.

---

# 4. Variables de dynamique du corridor

## 4.1 `applied`

### Définition métier

Nombre de demandes d'asile observées pour le corridor pendant l'année T.

### Définition technique

Agrégation des demandes au niveau :

```text
coo_id × coa_id × year
```

Les éventuelles dimensions procédurales présentes dans les données sources sont donc agrégées pour obtenir une vision globale du corridor.

### Rôle

C'est la **mesure de niveau courant** du corridor.

Elle permet au modèle de distinguer, par exemple :

- un corridor à 10 demandes ;
- un corridor à 1 000 demandes.

### Temporalité

Disponible à T.

### Leakage

Aucun leakage : la variable est connue avant la prédiction de T+1.

---

## 4.2 `applied_lag1`

### Définition métier

Nombre de demandes observées sur le même corridor l'année précédente.

```text
applied_lag1 = applied(T-1)
```

### Rôle

Permet de mesurer le niveau historique immédiatement antérieur.

Elle sert notamment à comprendre si le niveau actuel représente une rupture par rapport à l'année précédente.

### Valeurs manquantes

La première année disponible pour un corridor ne possède pas nécessairement d'observation T-1.

Dans ce cas :

```text
applied_lag1 = NA
```

Le manque d'historique n'est pas transformé silencieusement en zéro.

### Leakage

Aucun : T-1 est antérieur à T.

---

## 4.3 `applied_lag2`

### Définition métier

Nombre de demandes observées sur le même corridor deux années auparavant.

```text
applied_lag2 = applied(T-2)
```

### Rôle

Permet d'apporter une profondeur historique supplémentaire.

Cette variable aide à distinguer une évolution ponctuelle d'une dynamique qui s'inscrit dans plusieurs années.

### Valeurs manquantes

Les corridors ne disposant pas de deux années d'historique conservent :

```text
applied_lag2 = NA
```

### Leakage

Aucun.

---

## 4.4 `growth_past_1`

### Définition métier

Taux de croissance des demandes entre T-1 et T.

### Formule

```text
growth_past_1 =
    (applied(T) - applied(T-1))
    / applied(T-1)
```

### Rôle

Mesure la dynamique récente du corridor.

Elle permet de distinguer un corridor stable d'un corridor déjà en forte progression à T.

### Attention aux petits dénominateurs

Un passage de :

```text
2 → 10
```

produit une croissance de +400 %.

La variable doit donc être interprétée conjointement avec les volumes absolus.

### Valeurs manquantes

Elle est non calculable lorsque l'historique T-1 est absent ou lorsque le calcul n'est pas défini.

### Leakage

Aucun : elle utilise uniquement T et T-1.

---

## 4.5 `absolute_change_past_1`

### Définition métier

Variation absolue du nombre de demandes entre T-1 et T.

### Formule

```text
absolute_change_past_1 =
    applied(T) - applied(T-1)
```

### Rôle

Complète `growth_past_1`.

Elle permet d'éviter qu'une forte croissance relative sur un très petit volume soit considérée comme équivalente à une hausse importante en volume.

### Exemple

```text
10 → 20
```

donne :

```text
+100 %
+10 demandes
```

alors que :

```text
1 000 → 1 500
```

donne :

```text
+50 %
+500 demandes
```

La seconde évolution est beaucoup plus importante en volume absolu.

### Leakage

Aucun.

---

## 4.6 `acceleration`

### Définition métier

Indicateur permettant de caractériser l'évolution de la dynamique du corridor.

Il compare la variation récente à la variation observée précédemment.

### Rôle

Cette variable cherche à distinguer :

- une croissance stable ;
- une accélération ;
- un ralentissement.

Elle apporte donc une dimension de **dynamique** complémentaire au simple niveau de demandes.

### Valeurs manquantes

Elle nécessite davantage d'historique. Les observations pour lesquelles cet historique est insuffisant conservent une valeur manquante.

### Leakage

La construction doit utiliser uniquement des informations disponibles au plus tard à T.

---

## 4.7 `two_consecutive_increases`

### Définition métier

Indicateur binaire permettant de savoir si le corridor a connu **deux hausses consécutives** sur son historique disponible.

### Valeurs

| Valeur | Signification |
|---:|---|
| `1` | Deux hausses consécutives observées |
| `0` | Pas deux hausses consécutives |
| `<NA>` | Historique insuffisant |

Le type pandas utilisé dans le Feature Engineering est :

```text
Int8
```

### Pourquoi conserver `NA` ?

`0` et `NA` ne signifient pas la même chose.

- `0` = nous avons suffisamment d'historique et il n'y a pas deux hausses consécutives.
- `NA` = nous n'avons pas suffisamment d'historique pour conclure.

Cette distinction est conservée dans le Feature Engineering.

### Leakage

Aucun si l'indicateur est calculé uniquement à partir de T et des années antérieures.

---

# 5. Variables de pression du corridor

## 5.1 `origin_applied_total_t`

### Définition métier

Nombre total de demandes associées au pays d'origine à l'année T, tous pays d'asile confondus.

### Rôle

Permet de replacer un corridor dans la pression globale observée pour son pays d'origine.

Exemple :

> Un corridor peut être stable individuellement alors que l'ensemble des demandes provenant du pays d'origine augmente fortement.

Cette information peut donc constituer un signal contextuel.

### Temporalité

Calculée à T.

### Leakage

Aucun si le calcul est réalisé uniquement à partir des données disponibles à T.

---

## 5.2 `asylum_applied_total_t`

### Définition métier

Nombre total de demandes reçues par le pays d'asile à l'année T, tous pays d'origine confondus.

### Rôle

Mesure la pression globale du côté du pays d'asile.

Elle permet de distinguer :

- une hausse spécifique à un corridor ;
- une hausse plus générale affectant le pays d'asile.

### Temporalité

Disponible à T.

### Leakage

Aucun.

---

## 5.3 `segment_share_origin_t`

### Définition métier

Part du corridor dans l'ensemble des demandes provenant du même pays d'origine à T.

### Formule conceptuelle

```text
segment_share_origin_t =
    demandes du corridor à T
    /
    demandes totales de l'origine à T
```

### Rôle

Mesure le poids relatif du corridor dans les flux de son pays d'origine.

### Interprétation

Une valeur élevée signifie que le corridor représente une part importante des demandes associées à cette origine.

### Leakage

Aucun si toutes les composantes sont calculées à T.

---

## 5.4 `segment_share_asylum_t`

### Définition métier

Part du corridor dans l'ensemble des demandes reçues par le pays d'asile à T.

### Formule conceptuelle

```text
segment_share_asylum_t =
    demandes du corridor à T
    /
    demandes totales du pays d'asile à T
```

### Rôle

Mesure le poids du corridor dans la pression globale du pays d'asile.

### Leakage

Aucun si calculé uniquement à T.

---

# 6. Variables de contexte

## 6.1 `coo_id`

Identifiant du pays d'origine.

### Rôle

Permet au modèle de différencier les comportements historiques propres aux différents pays d'origine.

### Traitement ML

Cette variable doit être considérée comme **catégorielle**, et non comme une variable numérique continue.

Le code numérique d'un pays ne doit pas être interprété comme une grandeur.

---

## 6.2 `coa_id`

Identifiant du pays d'asile.

### Rôle

Permet de représenter les différences structurelles entre pays d'accueil.

### Traitement ML

Variable catégorielle.

---

## 6.3 `origin_region`

Région géographique du pays d'origine.

### Rôle

Fournit un niveau de contexte géographique plus agrégé que `coo_id`.

Elle peut permettre au modèle de généraliser à des catégories géographiques plutôt qu'à des pays individuels.

### Traitement ML

Variable catégorielle.

---

## 6.4 `asylum_region`

Région géographique du pays d'asile.

### Rôle

Fournit un contexte géographique agrégé côté pays d'accueil.

### Traitement ML

Variable catégorielle.

---

## 6.5 `year`

Année d'observation T.

### Rôle

Permet de capturer une partie des évolutions temporelles globales.

Elle est également indispensable pour réaliser un **split temporel** et éviter de mélanger passé et futur.

### Point de vigilance

`year` ne doit pas être utilisé comme simple identifiant technique. Son utilisation comme feature devra être validée dans le notebook ML selon la stratégie de modélisation retenue.

---

# 7. Variable externe : IDMC

## `idmc_total_origin_lag1`

### Définition métier

Indicateur IDMC disponible avec un décalage d'un an par rapport à l'année d'observation.

L'objectif est de respecter la contrainte :

> **ne pas utiliser une information future au moment de la prédiction.**

### Rôle

Fournit un signal externe relatif à la situation du pays d'origine, susceptible d'apporter un contexte complémentaire aux seules demandes d'asile.

### Valeurs manquantes

La variable présente une proportion importante de valeurs manquantes.

Ces valeurs ne sont **pas supprimées** dans le Feature Engineering.

### Traitement ML recommandé

Le traitement de l'imputation doit être réalisé **après le split temporel**, dans le pipeline ML.

Il est également pertinent de conserver un indicateur :

```python
idmc_missing = idmc_total_origin_lag1.isna().astype("int8")
```

afin de distinguer :

- une valeur IDMC faible ;
- une absence de donnée IDMC.

### Leakage

La version retenue est décalée afin de garantir que l'information est disponible avant ou au moment de la prédiction.

---

# 8. Variables volontairement exclues du modèle

## `applied_t1`

Cette variable correspond au nombre de demandes observées en T+1.

Elle est indispensable pour construire la cible, mais **interdite comme feature**.

Pourquoi ?

Parce qu'au moment où le modèle produit son alerte en T, `applied_t1` n'est pas encore connu.

L'utiliser créerait une **fuite de cible (target leakage)**.

---

## `growth_t1`

Taux de croissance entre T et T+1.

Même raison : il dépend directement de l'information future.

Il est utilisé uniquement pour analyser ou construire la cible.

---

## `absolute_change_t1`

Variation absolue entre T et T+1.

Elle dépend également de T+1 et ne doit donc pas entrer dans les variables explicatives.

---

## `criticality`

Cette variable ne fait pas partie du Feature Engineering retenu pour la prédiction.

Elle pourrait éventuellement intervenir plus tard dans une couche métier distincte destinée à différencier :

> **probabilité d'escalade**

et

> **impact opérationnel de l'escalade**.

Il ne faut pas mélanger ces deux notions dans le premier modèle.

---

## `risk_score`

Le `risk_score` n'existe pas encore à cette étape.

Il sera calculé **après la prédiction et la calibration du modèle**, à partir de la probabilité d'escalade.

---

## `alert_level`

Même logique : les niveaux `Normal`, `Attention`, `High`, `Critical` sont une **couche produit**, pas une feature d'entrée du modèle.

---

# 9. Variables supprimées du périmètre

Deux variables initialement envisagées ont volontairement été retirées :

### `applied_mean_3y`

Moyenne des demandes sur les trois années considérées.

Elle apportait un contexte de niveau historique, mais son caractère indispensable n'a pas été démontré.

### `historical_ratio`

Ratio entre le niveau courant et la moyenne historique.

Elle est également retirée afin de conserver un Feature Engineering plus parcimonieux.

> Principe retenu : **une variable doit avoir une justification métier claire et apporter une information utile au modèle ; nous n'ajoutons pas de variables uniquement parce qu'elles sont techniquement disponibles.**

---

# 10. Synthèse du périmètre final

| Groupe | Feature | Rôle |
|---|---|---|
| Niveau courant | `applied` | Niveau des demandes à T |
| Historique | `applied_lag1` | Niveau à T-1 |
| Historique | `applied_lag2` | Niveau à T-2 |
| Dynamique | `growth_past_1` | Croissance récente |
| Dynamique | `absolute_change_past_1` | Variation absolue récente |
| Dynamique | `acceleration` | Évolution de la dynamique |
| Dynamique | `two_consecutive_increases` | Signal de hausse persistante |
| Pression origine | `origin_applied_total_t` | Pression globale de l'origine |
| Pression asile | `asylum_applied_total_t` | Pression globale du pays d'asile |
| Poids corridor | `segment_share_origin_t` | Poids du corridor côté origine |
| Poids corridor | `segment_share_asylum_t` | Poids du corridor côté asile |
| Contexte | `coo_id` | Pays d'origine |
| Contexte | `coa_id` | Pays d'asile |
| Contexte | `origin_region` | Région d'origine |
| Contexte | `asylum_region` | Région d'asile |
| Temps | `year` | Année T |
| Externe | `idmc_total_origin_lag1` | Contexte IDMC disponible avec décalage |

---

# 11. Contrôles Data Quality

Le Feature Engineering applique les principes suivants :

- conservation des anomalies au lieu d'une suppression silencieuse ;
- contrôle des années ;
- contrôle des valeurs `applied` ;
- contrôle des doublons sur `coo_id × coa_id × year` ;
- contrôle des conflits de référentiel ;
- jointures temporelles explicites ;
- conservation des valeurs manquantes lorsqu'elles portent une information d'historique insuffisant ;
- aucune utilisation de T+1 dans les features explicatives.

---

# 12. Principe de préparation pour le Machine Learning

Le Feature Engineering produit donc une table **à T**.

Le notebook ML devra ensuite :

1. construire la cible **hausse significative des demandes** à partir de `applied` et `applied_t1` ;
2. exclure 2025 de l'apprentissage puisque T+1 n'est pas disponible ;
3. effectuer le **split temporel avant toute imputation statistique** ;
4. apprendre les imputations uniquement sur le train ;
5. établir une baseline naïve ;
6. entraîner les modèles ;
7. comparer leurs performances avec des métriques adaptées à l'alerte ;
8. calibrer les probabilités ;
9. transformer la probabilité en Risk Score ;
10. définir les niveaux d'alerte selon la performance et la capacité opérationnelle.

---

## Conclusion

Le Feature Engineering retenu est volontairement **parcimonieux** : chaque variable conservée doit représenter soit le **niveau**, la **dynamique**, la **pression contextuelle**, le **contexte géographique**, ou une **information externe disponible à T**.

Les variables futures (`applied_t1`, `growth_t1`, `absolute_change_t1`) restent exclusivement destinées à la construction de la cible et ne doivent jamais alimenter le modèle.
