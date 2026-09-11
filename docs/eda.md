## EDA des demandes d'asile UNHCR & IDMC

### 1. Objectif

L'EDA vise à comprendre les dynamiques historiques des demandes d'asile
avant toute modélisation et à vérifier la faisabilité de la question
prédictive : **peut-on prédire qu'un segment connaîtra une hausse des
demandes supérieure à 15 % à T+1 ?**

Elle couvre la qualité des données, les évolutions temporelles, les
origines, pays d'asile, corridors origine → accueil, décisions,
protection et contexte IDMC.

### 2. Périmètre et grain

Le dataset consolidé couvre **2000--2025** et contient **120 597
observations**. Le grain prédictif est :
`coo_id × coa_id × procedure_type × app_type × dec_level × app_pc × year`.

Un corridor correspond au flux **pays d'origine → pays d'asile**.

### 3. Data Quality

Aucune anomalie métier n'est supprimée silencieusement. Les contrôles
portent sur la complétude, cohérence, validité, exactitude, actualité et
unicité.

Les variables de solutions sont très incomplètes : `returned_idps` est
presque entièrement manquante, `returned_refugees` environ **96,8 %**,
`resettlement` **90,7 %**, `naturalisation` **89,8 %**.
`idmc_total_origin` présente environ **59,7 %** de valeurs manquantes.

### 4. Principaux constats

Le volume annuel atteint **3 848 894 demandes en 2023**, puis **3 421
776 en 2024** et **3 343 203 en 2025**, soit environ **−11,1 %**, puis
**−2,3 %**.

`applied` est fortement asymétrique : médiane ≈ **19**, moyenne =
**337,7**, P95 = **1 046**, P99 = **5 330**, maximum = **404 142**.
`log1p(applied)` est utilisé uniquement pour améliorer la visualisation.

Les analyses géographiques montrent qu'une croissance relative doit
toujours être rapprochée du **volume** et de la **variation absolue**.
Une forte croissance sur un faible volume initial ne représente pas le
même enjeu qu'une hausse plus modérée portant sur plusieurs dizaines de
milliers de demandes.

### 5. Décisions et protection

Sur la période, le dataset comptabilise environ **7,76 M** de décisions
reconnaissant le statut de réfugié, **3,19 M** d'autres formes de
protection, **12,48 M** de rejets, **10,13 M** de clôtures et **33,58
M** de décisions totales.

Ces volumes représentent des **décisions**, pas nécessairement des
personnes uniques.

Deux taux sont distingués :
`refugee_recognition_rate = decisions_recognized / decisions_total` et
`protection_rate = (decisions_recognized + decisions_other) / decisions_total`.

### 6. IDMC

Sur les observations disponibles, la corrélation de Spearman entre
`idmc_total_origin` et les demandes d'asile agrégées par origine-année
est d'environ **0,52**. Il s'agit d'une association statistique, pas
d'une preuve de causalité.

### 7. Cible prédictive

La cible `hausse_critique_demandes_t1` vaut `1` si les demandes du même
segment augmentent de **plus de 15 % à T+1**, `0` sinon, et reste
manquante lorsque T+1 n'est pas observable.

Sur **120 597 lignes**, **80 032 (66,36 %)** sont labellisables et **40
565 (33,64 %)** ne disposent pas d'une cible T+1 observable.

Parmi les observations labellisables : classe 0 = **48 424 (60,51 %)** ;
classe 1 = **31 608 (39,49 %)**. La baseline naïve de classe majoritaire
est donc **60,51 % d'accuracy**.

### 8. Corrélations

Aucune variable numérique isolée n'est fortement corrélée à la cible ;
`applied` est autour de **−0,13**. En revanche, certaines features sont
fortement corrélées entre elles : `applied` / `applied_lag1` = **0,86**,
`applied` / `decisions_total` = **0,87**, `refugee_recognition_rate` /
`protection_rate` ≈ **0,90**.

La prédiction devra donc rechercher la valeur dans une combinaison de
facteurs temporels, géographiques, catégoriels et contextuels.

### 9. Décision

L'EDA valide le passage au Feature Engineering sous réserve de :
respecter strictement la chronologie, construire les lags sur T−1/T−2
exacts, éviter le target leakage, écarter en V1 les variables trop
incomplètes, vérifier la disponibilité réelle des décisions/IDMC et
utiliser un **split chronologique** pour la modélisation.
