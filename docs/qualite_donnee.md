# Phase 2 --- Vérification de la qualité des données pour le Machine Learning

## 1. Objectif de la phase

Cette phase vise à vérifier que les données utilisées pour le cas
d'usage prédictif sont suffisamment fiables, cohérentes et
temporellement exploitables avant toute construction de features ou
entraînement de modèle.

### Question prédictive

> **Peut-on prédire si un pays connaîtra une augmentation critique (\>
> 15 %) de son stock de déplacés internes (IDPs) pour l'année suivante
> ?**

Le fichier **IDMC** constitue la source centrale pour la construction de
la cible. Les autres sources --- **demandes d'asile, décisions d'asile,
solutions, démographie et référentiel pays** --- sont considérées comme
des sources explicatives candidates.

L'objectif de la Data Quality n'est pas de rendre artificiellement les
données « parfaites », mais de déterminer quelles observations et
quelles variables sont **fiables et utilisables pour le ML sans
introduire de biais, de double comptage ou de fuite de cible**.

------------------------------------------------------------------------

## 2. Périmètre des données

Les jeux de données retenus sont :

  -----------------------------------------------------------------------
  Dataset                             Rôle envisagé dans le ML
  ----------------------------------- -----------------------------------
  `data_idmc_depuis_2000.csv`         Source principale : stock IDP,
                                      historique et construction de la
                                      cible

  `demandes_asile_depuis_2000.csv`    Variables explicatives candidates
                                      liées aux demandes d'asile

  `decisions_asile_depuis_2000.csv`   Variables explicatives candidates
                                      liées aux décisions d'asile

  `data_solutions_depuis_2000.csv`    Variables explicatives candidates :
                                      retours, réinstallation,
                                      naturalisation

  `demographie_depuis_2000.csv`       Variables contextuelles candidates,
                                      sous réserve de validation du
                                      périmètre

  Référentiel `pays`                  Normalisation des pays, ISO,
                                      régions et contrôles référentiels
  -----------------------------------------------------------------------

Les données UNRWA sont exclues du périmètre du projet.

------------------------------------------------------------------------

## 3. Principes de qualité appliqués

La vérification repose sur les dimensions suivantes :

-   **Complétude** : quantification des valeurs absentes.
-   **Cohérence** : homogénéité des codes, identifiants, formats et
    relations entre colonnes.
-   **Validité** : conformité des années, types et mesures numériques.
-   **Unicité** : absence de doublons selon les clés métier.
-   **Exactitude / Accuracy** : cohérence métier des valeurs et
    agrégats.
-   **Actualité / Timeliness** : couverture et continuité temporelles.
-   **Éligibilité ML** : disponibilité des variables au moment réel de
    la prédiction et absence de target leakage.

### Règle de conservation

Une observation suspecte n'est jamais supprimée silencieusement.

Les anomalies sont : 1. détectées ; 2. quantifiées ; 3. analysées ; 4.
documentées ; 5. conservées tant qu'une règle métier ne justifie pas
explicitement leur exclusion du dataset ML.

Une valeur absente ne doit notamment pas être transformée
automatiquement en zéro.

------------------------------------------------------------------------

# 4. Contrôles réalisés

## 4.1 Structure des datasets

Pour chaque fichier, les éléments suivants sont contrôlés :

-   nombre de lignes et de colonnes ;
-   noms des colonnes ;
-   types de données ;
-   aperçu des observations ;
-   présence des variables nécessaires au cas d'usage.

### Importance pour le ML

Une erreur de structure peut modifier le grain d'analyse ou conduire à
utiliser une variable avec un type incorrect. Le contrôle structurel
constitue donc un prérequis avant l'analyse statistique.

------------------------------------------------------------------------

## 4.2 Complétude

Le nombre et le pourcentage de valeurs manquantes sont mesurés pour
chaque variable.

Une distinction est maintenue entre :

-   valeur réellement absente ;
-   valeur numérique `0` ;
-   `UKN` : modalité **Unknown** ;
-   `STA` : modalité correspondant aux personnes apatrides.

### Importance pour le ML

Une feature fortement incomplète peut réduire le nombre d'observations
exploitables ou nécessiter une stratégie spécifique. Pour la variable
`total` IDMC, une absence peut empêcher directement la construction de
la cible.

`UKN` ne doit pas être assimilé à une erreur technique. Il s'agit d'une
modalité métier valide. Cependant, `coo_iso = UKN` peut devenir non
exploitable pour un modèle dont le grain est explicitement le pays
d'origine.

------------------------------------------------------------------------

## 4.3 Validité des années

Les années sont contrôlées pour identifier :

-   valeurs non numériques ;
-   bornes temporelles observées ;
-   années absentes ;
-   ruptures dans les séries par pays.

### Importance pour le ML

Le modèle est temporel. Une année incorrecte peut fausser :

-   les lags ;
-   les taux de croissance ;
-   les moyennes mobiles ;
-   la construction de la cible T+1 ;
-   le découpage train / validation / test.

------------------------------------------------------------------------

## 4.4 Validité des variables numériques

Les principales mesures sont contrôlées :

-   IDMC : `total` ;
-   demandes : `applied` ;
-   décisions : `dec_recognized`, `dec_other`, `dec_rejected`,
    `dec_closed`, `dec_total` ;
-   solutions : `returned_refugees`, `resettlement`, `naturalisation`,
    `returned_idps` ;
-   démographie : totaux et répartitions démographiques.

Les contrôles portent notamment sur :

-   erreurs de conversion numérique ;
-   valeurs négatives ;
-   valeurs nulles ;
-   valeurs extrêmes.

### Importance pour le ML

Un nombre de personnes négatif est incohérent avec le phénomène étudié.
À l'inverse, une valeur extrêmement élevée n'est pas automatiquement une
erreur : dans un contexte de crise humanitaire, un pic peut constituer
précisément le signal que le modèle doit apprendre.

**Un outlier statistique n'est donc pas supprimé automatiquement.**

------------------------------------------------------------------------

# 5. Contrôle de l'unicité

Les doublons sont recherchés à partir des clés métier candidates de
chaque source.

## Résultat

> **Aucun doublon n'a été détecté dans les fichiers analysés selon les
> clés métier retenues.**

### Décision

**GO --- contrôle d'unicité validé.**

Aucune suppression de ligne n'est nécessaire au titre des doublons.

### Importance pour le ML

Les doublons peuvent artificiellement augmenter les volumes lors des
agrégations et des jointures. Leur absence réduit le risque de double
comptage avant la construction du dataset d'apprentissage.

------------------------------------------------------------------------

# 6. Accuracy et cohérence métier

## 6.1 IDMC : cohérence de la variable `total`

La colonne `total` constitue la variable centrale du projet puisqu'elle
sert à mesurer l'évolution du stock de déplacés internes.

Les contrôles portent sur :

-   valeurs manquantes ;
-   valeurs négatives ;
-   valeurs nulles ;
-   distribution ;
-   valeurs extrêmes ;
-   ruptures temporelles.

### Importance pour le ML

Une erreur dans une feature peut dégrader un modèle. Une erreur dans la
variable utilisée pour construire la **target** modifie directement la
vérité terrain que le modèle doit apprendre.

La qualité de `total` est donc prioritaire.

------------------------------------------------------------------------

## 6.2 Décisions d'asile

Une vérification de cohérence peut comparer `dec_total` aux composantes
:

-   `dec_recognized` ;
-   `dec_other` ;
-   `dec_rejected` ;
-   `dec_closed`.

Toute différence doit être investiguée et non corrigée automatiquement.

### Importance pour le ML

Ces données pourraient servir à construire des variables telles que le
taux de reconnaissance. Une incohérence dans le dénominateur créerait
une feature incorrecte.

Avant toute agrégation, le rôle de `procedure_type`, `dec_level` et
`dec_pc` doit également être clarifié afin d'éviter de compter plusieurs
fois une même réalité administrative.

------------------------------------------------------------------------

## 6.3 Demandes d'asile

La variable principale candidate est `applied`.

Pour la rapprocher de l'IDMC, les demandes pourront être étudiées par
**pays d'origine**, puis éventuellement agrégées sur les différents pays
d'asile.

Avant cette agrégation, les dimensions :

-   `procedure_type` ;
-   `app_type` ;
-   `dec_level` ;
-   `app_pc`

doivent être comprises afin de prévenir tout double comptage.

### Importance pour le ML

L'hypothèse à tester est que les demandes d'asile disponibles à T
apportent une information supplémentaire pour anticiper une hausse IDMC
à T+1.

Cette relation est une **hypothèse prédictive à mesurer**, et non une
relation causale supposée.

------------------------------------------------------------------------

## 6.4 Solutions

Les variables suivantes sont conservées séparément :

-   `returned_refugees` ;
-   `resettlement` ;
-   `naturalisation` ;
-   `returned_idps`.

Elles ne doivent pas être additionnées automatiquement dans un
indicateur unique.

### Importance pour le ML

Ces mesures représentent des phénomènes différents. `returned_idps` est
notamment particulièrement pertinent pour le phénomène des déplacements
internes, mais son utilité prédictive devra être mesurée.

------------------------------------------------------------------------

## 6.5 Démographie

La cohérence interne des totaux démographiques doit être vérifiée,
notamment entre les totaux féminins, masculins et globaux.

Le périmètre exact de la variable démographique `total` doit cependant
être validé avant de l'utiliser comme dénominateur d'un taux IDMC.

### Importance pour le ML

Un ratio tel que :

`IDMC / population`

n'a de sens que si le dénominateur représente réellement la population
correspondant au concept recherché. Un ratio mathématiquement correct
mais sémantiquement faux introduirait une feature trompeuse.

------------------------------------------------------------------------

# 7. Timeliness --- Continuité temporelle IDMC

La continuité temporelle a été analysée entre deux observations
successives d'un même pays d'origine.

## Résultats observés

-   **850 transitions** analysées ;
-   **835 transitions**, soit **98,2 %**, sont espacées exactement d'un
    an ;
-   **15 transitions**, soit **1,8 %**, présentent un intervalle
    supérieur à un an ;
-   l'intervalle maximal observé est de **9 ans**.

L'analyse des cas concernés montre que ces ruptures peuvent correspondre
à des périodes sans observation IDMC pour le pays considéré.

## Décision Data Quality

Les observations sont **conservées**.

Les années intermédiaires ne sont :

-   ni créées artificiellement ;
-   ni imputées ;
-   ni remplacées par zéro.

Une absence d'observation signifie **« donnée non observée »**, et non
**« zéro déplacé interne »**.

### Importance pour le ML

Cette décision est critique pour les variables temporelles.

Exemple :

``` text
2019 → 100 000 IDPs
2020 → aucune observation
2021 → 130 000 IDPs
```

La variation entre 2019 et 2021 ne doit pas être interprétée comme une
croissance annuelle 2020--2021.

Par conséquent, une croissance annuelle, un lag annuel ou une target T+1
ne sont valides que lorsque :

``` text
année suivante = année courante + 1
```

## Statut

  Contrôle                                  Résultat Décision
  ---------------------------------- --------------- ---------------------
  Transitions analysées                          850 ---
  Gap = 1 an                            835 (98,2 %) GO
  Gap \> 1 an                             15 (1,8 %) Conservé et signalé
  Gap maximal                                  9 ans Conservé
  Imputation des années absentes                   0 Aucune imputation
  Croissance annuelle sur gap \> 1     Non autorisée Règle ML

------------------------------------------------------------------------

# 8. Référentiel géographique `countries`

Le référentiel pays est utilisé pour contrôler et enrichir :

-   `coo_id` ;
-   `coa_id` ;
-   codes ISO ;
-   noms des pays ;
-   régions ;
-   grandes régions.

Les identifiants présents dans les datasets doivent être comparés au
référentiel afin d'identifier les éventuels comptes géographiques
orphelins.

### Règle de jointure

Les enrichissements géographiques seront réalisés avec des **LEFT JOIN**
afin de ne perdre aucune observation métier.

Les observations non raccordées seront journalisées pour analyse.

### Importance pour le ML

Le modèle est construit par pays d'origine. Une incohérence
d'identifiant peut :

-   fusionner deux séries différentes ;
-   fragmenter la série d'un même pays ;
-   empêcher l'affectation à une région ;
-   créer des lags incorrects.

------------------------------------------------------------------------

# 9. Préparation de la cible ML

## 9.1 Grain cible

Le grain visé est :

> **1 observation = 1 pays d'origine × 1 année**

Avant toute agrégation IDMC, il faut confirmer que les éventuelles
lignes sous-jacentes sont additives afin de ne pas créer de double
comptage.

------------------------------------------------------------------------

## 9.2 Définition de la cible

Pour un pays `p` et une année `t` :

``` text
croissance_IDMC_t+1 =
(IDMC_t+1 - IDMC_t) / IDMC_t
```

La cible binaire est :

``` text
hausse_critique_suivante = 1
si croissance_IDMC_t+1 > 15 %

hausse_critique_suivante = 0
sinon
```

La cible n'est calculée que lorsque T et T+1 sont deux années réellement
consécutives.

------------------------------------------------------------------------

## 9.3 Cas `IDMC_t = 0`

Lorsque le stock à T est nul, le taux de croissance classique n'est pas
défini.

Ces observations ne doivent pas être supprimées silencieusement.

Elles doivent être identifiées séparément, car un passage :

``` text
0 → valeur positive
```

peut correspondre à une **émergence de déplacement** plutôt qu'à une
croissance classique.

Une règle métier spécifique sera définie avant la modélisation.

------------------------------------------------------------------------

# 10. Contrôle du déséquilibre de la cible

Après construction de `hausse_critique_suivante`, la proportion des
classes `0` et `1` doit être mesurée.

### Importance pour le ML

Si, par exemple, 90 % des observations appartiennent à la classe `0`, un
modèle prédisant toujours `0` obtiendrait 90 % d'accuracy tout en étant
incapable de détecter les crises.

La **baseline naïve** sera donc obligatoire.

Pour l'évaluation du modèle, les métriques prioritaires seront notamment
:

-   Recall de la classe 1 ;
-   Precision de la classe 1 ;
-   F1-score ;
-   PR-AUC ;
-   matrice de confusion ;
-   nombre de faux négatifs.

L'arbitrage Precision / Recall devra être aligné sur le coût
opérationnel d'une alerte injustifiée par rapport au coût d'une hausse
critique non détectée.

------------------------------------------------------------------------

# 11. Contrôle du Target Leakage

Chaque variable explicative candidate doit être évaluée selon sa
disponibilité réelle au moment de la prédiction.

Principe :

> **Pour prédire T+1, aucune feature ne peut utiliser une information
> qui n'était pas disponible à T au moment de produire la prédiction.**

Exemples :

  Variable                Usage envisagé
  ----------------------- --------------------------------------------
  `IDMC_t`                Feature candidate
  `IDMC_t-1`              Feature candidate
  croissance historique   Feature candidate
  demandes d'asile à T    Candidate, disponibilité réelle à vérifier
  décisions à T           Candidate, disponibilité réelle à vérifier
  solutions à T           Candidate, disponibilité réelle à vérifier
  démographie à T         Candidate, disponibilité réelle à vérifier
  `IDMC_t+1`              Target uniquement
  décisions T+1           Interdit comme feature

### Importance pour le ML

Une variable disponible uniquement après la période prédite peut
produire d'excellentes performances pendant l'expérimentation, mais ces
performances seraient impossibles à reproduire en production.

La qualité statistique d'une feature ne suffit donc pas : elle doit
également être **disponible à T=0**.

------------------------------------------------------------------------

# 12. Contrôle des futures jointures

Les sources ne seront pas jointes directement dans leur granularité
brute.

Chaque source devra d'abord être ramenée au grain compatible avec le
dataset ML, notamment :

``` text
année × pays d’origine
```

Après chaque jointure, les contrôles suivants seront obligatoires :

-   nombre de lignes avant ;
-   nombre de lignes après ;
-   unicité de la clé ;
-   nombre de correspondances ;
-   nombre de non-correspondances ;
-   absence de multiplication artificielle des observations.

Les jointures seront réalisées en **LEFT JOIN** pour préserver les
observations du dataset principal.

### Importance pour le ML

Une jointure many-to-many non maîtrisée peut multiplier les volumes et
produire des features artificielles sans générer d'erreur technique
visible.

------------------------------------------------------------------------

# 13. Scorecard Data Quality ML

À la fin de la phase, le tableau de synthèse est utilisé comme outil de
décision.

  -----------------------------------------------------------------------
  Contrôle                Résultat actuel         Décision
  ----------------------- ----------------------- -----------------------
  Doublons selon clés     Aucun détecté           **GO**
  métier                                          

  Continuité IDMC à 1 an  835 / 850 = 98,2 %      **GO**

  Gaps IDMC \> 1 an       15 / 850 = 1,8 %        Conservés, non imputés

  Gap maximal IDMC        9 ans                   Conservé et documenté

  Imputation des années   Aucune                  **GO**
  absentes                                        

  Croissance annuelle sur Interdite               Règle validée
  gap \> 1                                        

  Validité `total` IDMC   À consolider            À valider

  Bases `IDMC_t = 0`      À mesurer               Règle à définir

  `UKN` / `STA`           Modalités métier à      Traitement ML à
                          conserver               documenter

  Référentiel pays        À consolider            À valider

  Cohérence décisions     À consolider            À valider

  Agrégation demandes     Sémantique à valider    À valider

  Solutions               Variables conservées    À valider
                          séparément              

  Démographie             Périmètre du `total` à  À valider
                          confirmer               

  Disponibilité T=0       À documenter par        **Bloquant avant ML**
                          feature                 

  Target \> 15 %          À construire après      À valider
                          validation              
  -----------------------------------------------------------------------

------------------------------------------------------------------------

# 14. Critères de sortie de la Phase 2

La phase Data Quality sera considérée comme terminée lorsque les
conditions suivantes seront satisfaites :

1.  le grain IDMC `pays d’origine × année` est validé ;
2.  la variable `total` utilisée pour construire la cible est
    suffisamment fiable ;
3.  les gaps temporels sont identifiés et ne sont pas imputés
    artificiellement ;
4.  seules les années consécutives sont utilisées pour calculer une
    variation annuelle ou une cible T+1 ;
5.  le cas `IDMC_t = 0` possède une règle explicite ;
6.  les identifiants pays sont raccordés ou les rejets sont documentés ;
7.  les agrégations des demandes et décisions sont sémantiquement
    validées ;
8.  aucune jointure ne multiplie artificiellement les observations ;
9.  les valeurs extrêmes ont été investiguées sans suppression
    automatique ;
10. toutes les features retenues sont réellement disponibles à T ;
11. la distribution de la cible est connue ;
12. les règles de qualité et exceptions sont documentées.

------------------------------------------------------------------------

# 15. Passage vers la Phase 3

Une fois ces contrôles validés, le pipeline pourra passer à la
construction du dataset ML :

``` text
Données brutes
    ↓
Contrôles Data Quality
    ↓
IDMC au grain pays × année
    ↓
Construction des variables historiques
    ↓
Construction de la target T+1 > 15 %
    ↓
Agrégation des demandes d’asile
    ↓
Agrégation des décisions
    ↓
Ajout des solutions
    ↓
Ajout éventuel de la démographie
    ↓
Enrichissement géographique countries
    ↓
LEFT JOIN contrôlés
    ↓
Contrôle anti-leakage
    ↓
Dataset ML final
    ↓
Split temporel
    ↓
Baseline naïve
    ↓
Modèles de classification
```

## Conclusion

La Phase 2 ne consiste pas uniquement à rechercher des cellules vides ou
des doublons. Elle vise à garantir que la **vérité terrain**, les séries
temporelles et les futures variables explicatives représentent
correctement le phénomène métier au moment où la prédiction devra être
produite.

Les contrôles déjà réalisés apportent deux résultats favorables :
**aucun doublon n'a été détecté selon les clés métier retenues**, et
**98,2 % des 850 transitions IDMC sont annuelles**. Les 15 ruptures
temporelles supérieures à un an sont conservées sans imputation,
conformément au principe de non-suppression et afin de ne pas
transformer une absence d'observation en valeur métier artificielle.

La priorité avant le passage à la modélisation est désormais de
finaliser la qualité de `total`, la construction de la cible \> 15 %, la
sémantique des agrégations des sources explicatives et leur
disponibilité réelle à T.
