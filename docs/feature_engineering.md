# Documentation --- Feature Engineering des demandes d'asile

### 1. Objectif

Transformer les données explorées dans l'EDA en un Feature Set
reproductible et compatible avec un scoring réel. La règle centrale est
: **toute feature utilisée pour prédire T+1 doit être disponible à T ou
avant T**.

### 2. Grain

Le segment est défini par :
`coo_id × coa_id × procedure_type × app_type × dec_level × app_pc`.

Tous les calculs temporels sont réalisés sur le **même segment**.

### 3. Lags temporels stricts

`applied_lag1` correspond à la valeur exacte à **T−1** et `applied_lag2`
à **T−2**.

Un simple `shift(1)` peut confondre l'observation précédente avec
l'année précédente. Si un segment existe en 2019 puis en 2021 sans
observation en 2020, 2019 ne doit pas devenir le `lag1` de 2021. Le lag
T−1 reste donc `NaN`.

Cette règle évite de créer artificiellement de fausses évolutions
temporelles.

### 4. Features de dynamique passée

Les principales features créées sont : - `absolute_change_past_1` :
variation absolue entre T−1 et T ; - `absolute_change_past_2` :
variation absolue entre T−2 et T−1 ; - `growth_past_1` : croissance
relative entre T−1 et T ; - `growth_past_2` : croissance relative entre
T−2 et T−1 ; - `two_consecutive_increases` : présence de deux hausses
consécutives ; - `applied_mean_3y` : moyenne sur T, T−1 et T−2 ; -
`applied_std_3y` : variabilité sur ces trois années.

Ces features permettent de distinguer un **choc ponctuel** d'une
**dynamique persistante**.

### 5. Contexte retardé

Les décisions d'asile et les données IDMC peuvent ne pas être
consolidées au moment exact du scoring à T. Pour une V1 conservatrice,
leurs versions **T−1** sont privilégiées : `decisions_total_lag1`,
`decisions_recognized_lag1`, `protection_rate_lag1`,
`idmc_total_origin_lag1`, etc.

Le contexte retardé désigne donc des informations complémentaires
utilisées avec une année de décalage afin de réduire le risque de
leakage temporel.

### 6. Cible T+1

`hausse_critique_demandes_t1 = 1` si la croissance des demandes du même
segment à T+1 est supérieure à **15 %**, `0` si elle est inférieure ou
égale à 15 %, et `NA` si T+1 n'est pas observable.

Résultat : **120 597** lignes totales, **80 032** labellisables, **40
565** sans cible T+1, soit **66,36 %** de labellisation.

Les lignes non labellisables sont conservées pour audit mais ne sont pas
utilisées pour l'apprentissage supervisé.

### 7. Sélection des features

Le Feature Set V1 comprend trois familles : - **profil du segment** :
origine, accueil, procédure, type de demande, niveau de décision ; -
**dynamique historique** : volume actuel, lags, croissances, variations
et persistance ; - **contexte retardé** : décisions et IDMC à T−1.

### 8. Journal de sélection

Chaque colonne reçoit une décision traçable : - `KEEP` : retenue pour la
V1 ; - `DROP_TECHNICAL` : identifiant ou métadonnée technique ; -
`DROP_LEAKAGE` : information future ou cible ; - `DROP_MISSINGNESS` :
couverture trop faible ; - `DROP_REDUNDANT` : information déjà
représentée ; - `DROP_T0_UNCERTAIN` : disponibilité à T non garantie ; -
`DROP_LOW_VALUE` : faible valeur attendue pour la V1 ; - `DROP_UNUSED` :
non retenue actuellement.

`DROP` signifie **exclusion du dataset ML**, pas suppression du dataset
source.

### 9. X et y

`X` contient les variables utilisées par le modèle pour prédire. `y`
contient la cible à apprendre.

Conceptuellement : `X_T → modèle → prédiction de y_T+1`.

Aucune information de T+1 ne doit apparaître dans `X`.

### 10. Contrôles anti-leakage et qualité

Les champs `year_t1`, `applied_t1`, `growth_t1` et la cible sont
explicitement interdits dans `X`. Un `assert` arrête l'exécution si l'un
d'eux est détecté.

Le taux de valeurs manquantes est calculé pour chaque feature. Une
valeur manquante n'est pas automatiquement supprimée ou imputée : pour
un lag, elle peut signifier qu'un historique continu n'existe pas.

Les colonnes constantes sont également recherchées. Une variable ayant
une seule valeur sur toutes les observations n'apporte aucun pouvoir
discriminant et peut être exclue du Feature Set, avec traçabilité.

### 11. Livrables

Le Feature Engineering prévoit : - `dataset_ml_features.csv` : features
et cible ; - `feature_selection_log.csv` : journal de sélection ; -
`rows_unlabelled_for_supervised_ml.csv` : lignes sans cible T+1
conservées pour audit.

### 12. Décision pour la suite

La prochaine étape est la modélisation avec **split chronologique**,
preprocessing appris uniquement sur le train, baseline naïve, puis
comparaison des modèles.

La baseline de classe majoritaire est d'environ **60,51 % d'accuracy**.
L'évaluation devra également suivre **Recall, Precision, F1-score,
PR-AUC et matrice de confusion**, en fonction du coût opérationnel des
faux positifs et faux négatifs.
