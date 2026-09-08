## Nettoyage, normalisation et consolidation

## 1. Objectif

Cette phase prépare les données avant l’analyse exploratoire et la modélisation prédictive.

La question métier cible est :

> **Peut-on prédire si un pays connaîtra une augmentation critique (> 15 %) de son stock de déplacés internes (IDPs) pour l’année suivante ?**

Le grain analytique retenu est :

> **1 ligne = 1 année × 1 pays d’origine**

La table centrale est **IDMC**. Les autres sources viennent l’enrichir avec des variables explicatives potentielles.

---

## 2. Périmètre

| Dataset | Rôle |
|---|---|
| `data_idmc_depuis_2000.csv` | Table centrale : stock annuel de déplacés internes |
| `demandes_asile_depuis_2000.csv` | Demandes d’asile |
| `decisions_asile_depuis_2000.csv` | Décisions d’asile |
| `data_solutions_depuis_2000.csv` | Retours, réinstallation, naturalisation, retours d’IDPs |
| `demographie_depuis_2000.csv` | Données démographiques disponibles pour analyses futures |
| `countries.csv` | Référentiel pays et régions |

Le dataset UNRWA est exclu du périmètre.

---

# 3. Principes de gouvernance

### 3.1 Non-suppression silencieuse

Aucune ligne suspecte ou anormale n’est supprimée sans justification.

Les anomalies sont :
- conservées lorsque leur interprétation n’est pas certaine ;
- journalisées ;
- exportées pour investigation si nécessaire.

Seuls les doublons techniques stricts peuvent être retirés, avec traçabilité.

### 3.2 Codes métier spéciaux

Les codes suivants sont conservés :
- `UKN` : Unknown / Inconnu ;
- `STA` : Stateless / Apatride.

Ils ne sont pas considérés comme des erreurs techniques.

### 3.3 Pas d’imputation arbitraire

Une absence de donnée n’est pas automatiquement transformée en `0`.

```text
NaN ≠ 0
```

Un `NaN` après jointure signifie qu’aucune valeur correspondante n’a été trouvée dans la source jointe.

### 3.4 Préservation de la table IDMC

Toutes les consolidations utilisent des `LEFT JOIN` depuis IDMC afin de préserver toutes les observations de la table centrale.

---

# 4. Étape 1 — Nettoyage

## 4.1 Objectif

Le nettoyage corrige les problèmes techniques élémentaires sans modifier la signification métier des données.

Cette étape ne réalise :
- aucune jointure ;
- aucune agrégation métier ;
- aucune création de cible ;
- aucun feature engineering.

## 4.2 Noms de colonnes

Les noms de colonnes sont nettoyés pour supprimer les espaces parasites.

Exemple :

```python
df.columns = (
    df.columns
    .str.strip()
    .str.replace(" ", "_")
)
```

## 4.3 Valeurs textuelles

Les textes sont nettoyés par suppression des espaces en début et fin de chaîne.

Les chaînes vides sont converties en valeurs manquantes explicites.

```python
df[col] = (
    df[col]
    .astype("string")
    .str.strip()
    .replace("", pd.NA)
)
```

La mise en majuscules des codes est réalisée pendant la normalisation, pas pendant le nettoyage.

## 4.4 Année

La colonne `year` est convertie en numérique.

Les valeurs non numériques, non entières ou hors plage attendue sont auditées mais non supprimées automatiquement.

Le périmètre documentaire actuel couvre les années **2000 à 2025**.

## 4.5 Identifiants

Les colonnes `coo_id`, `coa_id` et `id` sont converties en type entier nullable `Int64`.

Les valeurs techniquement invalides sont journalisées.

## 4.6 Variables quantitatives

Les colonnes d’effectifs sont converties en valeurs numériques.

Exemples :
- `total`
- `applied`
- `dec_total`
- `dec_recognized`
- `returned_idps`
- `returned_refugees`
- `resettlement`
- `naturalisation`

Les valeurs négatives sont considérées comme suspectes et auditées.

## 4.7 Doublons

La distinction suivante est maintenue :

```text
doublon technique strict
≠
clé métier répétée
≠
anomalie métier confirmée
```

Un doublon technique strict peut être écarté après export et traçabilité.

Une répétition de clé métier n’est jamais supprimée automatiquement.

## 4.8 Valeurs manquantes

Un résumé des valeurs manquantes est produit pour chaque dataset afin de mesurer la complétude.

---

# 5. Étape 2 — Normalisation

## 5.1 Objectif

La normalisation rend les formats cohérents entre les différentes sources avant consolidation.

Elle s’applique uniquement aux données déjà nettoyées.

## 5.2 Espaces multiples

Les espaces multiples sont remplacés par un espace simple.

```text
"Democratic   Republic" → "Democratic Republic"
```

## 5.3 Codes

Les colonnes de codes sont converties en majuscules, notamment :

```text
coo
coo_iso
coa
coa_iso
procedure_type
app_type
dec_level
app_pc
dec_pc
code
iso
iso2
```

Exemples :

```text
fra → FRA
ukn → UKN
sta → STA
```

`UKN` et `STA` restent des modalités valides.

## 5.4 Noms et libellés

Les noms de pays et libellés sont conservés sous une forme lisible.

Les futures jointures reposent en priorité sur :
- `coo_id`
- `coa_id`
- `id`

et non sur les noms de pays.

## 5.5 Types

Les identifiants et années sont harmonisés :

```text
year   → Int64
coo_id → Int64
coa_id → Int64
id     → Int64
```

## 5.6 Contrôle ISO

Les codes ISO sont contrôlés syntaxiquement sur trois lettres.

Exemples attendus :

```text
FRA
DEU
SYR
UKN
STA
```

Les codes hors format sont conservés mais journalisés.

## 5.7 Référentiel pays

Le référentiel pays est contrôlé en priorité sur l’unicité de `id`.

Des contrôles complémentaires peuvent être réalisés sur `code`, `iso` et `iso2`.

Aucune ligne n’est sélectionnée arbitrairement en cas de conflit.

---

# 6. Étape 3 — Consolidation

## 6.1 Objectif

La consolidation construit une table analytique unique au grain :

> **`year × coo_id`**

IDMC reste la table centrale.

---

# 7. Préparation de la table IDMC

Les colonnes centrales sont :

```text
year
coo_id
total
```

La colonne `total` est renommée :

```text
idmc_total
```

Le grain `year × coo_id` doit être unique.

Si plusieurs lignes existent à ce grain, aucune agrégation automatique n’est effectuée sans validation.

---

# 8. Agrégation des demandes d’asile

Les demandes d’asile sont ramenées au grain :

```text
year × coo_id
```

L’objectif est d’obtenir le nombre total de demandes d’asile associées à un pays d’origine pendant une année.

```python
demandes_origin = (
    demandes
    .groupby(
        ["year", "coo_id"],
        as_index=False,
        dropna=False
    )
    .agg(
        asylum_applications=("applied", "sum")
    )
)
```

Le pays d’asile (`coa_id`) existe dans la source mais ne fait pas partie du grain final du modèle.

---

# 9. Agrégation des décisions d’asile

Les décisions sont agrégées au même grain :

```text
year × coo_id
```

Variables principales :

```text
decisions_recognized
decisions_other
decisions_rejected
decisions_closed
decisions_total
```

Le taux de reconnaissance est calculé uniquement lorsque `decisions_total > 0` :

```text
recognition_rate =
decisions_recognized / decisions_total
```

Sinon la valeur reste manquante.

---

# 10. Agrégation des solutions

Les solutions sont agrégées au grain :

```text
year × coo_id
```

Les mesures restent séparées :

```text
returned_refugees
resettlement
naturalisation
returned_idps
```

Aucune variable générique `solutions_total` n’est créée, car ces phénomènes ne sont pas considérés comme équivalents.

---

# 11. Démographie

La démographie reste disponible pour les analyses futures.

Elle n’est pas intégrée automatiquement à la table consolidée tant que la signification exacte de la colonne `total` n’est pas nécessaire et validée pour la question prédictive.

---

# 12. Référentiel pays

Le référentiel pays est joint à partir de :

```text
coo_id = id
```

Il peut enrichir la table avec :

```text
country_iso
country_name
country_region
country_major_area
```

La relation attendue est :

```python
validate="many_to_one"
```

car plusieurs années peuvent correspondre à un même pays côté IDMC, tandis que le référentiel doit contenir une seule ligne par `id`.

---

# 13. Stratégie de jointure

La consolidation suit la logique :

```text
IDMC
  LEFT JOIN demandes
  LEFT JOIN décisions
  LEFT JOIN solutions
  LEFT JOIN référentiel pays
```

Les jointures temporelles utilisent :

```text
year
coo_id
```

Le référentiel pays utilise uniquement :

```text
coo_id
```

---

# 14. Contrôles après chaque jointure

Après chaque `LEFT JOIN`, le nombre de lignes est contrôlé.

Règle :

```text
nombre de lignes après jointure
=
nombre de lignes avant jointure
```

Une augmentation du nombre de lignes indique généralement que la table jointe n’est pas unique au grain attendu.

Le pipeline doit alors s’arrêter plutôt que produire silencieusement un dataset incorrect.

---

# 15. Valeurs manquantes après consolidation

Les valeurs manquantes ne sont pas remplacées automatiquement.

Exemple :

```text
asylum_applications = NaN
```

signifie qu’aucune valeur correspondante n’a été trouvée dans la source des demandes d’asile.

Cela ne permet pas de conclure automatiquement qu’il y a eu zéro demande.

Des variables de disponibilité sont ajoutées :

```text
has_asylum_data
has_decisions_data
has_solutions_data
```

---

# 16. Structure attendue de la table consolidée

La table finale doit contenir approximativement :

```text
year
coo_id
idmc_total
asylum_applications
decisions_recognized
decisions_other
decisions_rejected
decisions_closed
decisions_total
recognition_rate
returned_refugees
resettlement
naturalisation
returned_idps
country_iso
country_name
country_region
country_major_area
has_asylum_data
has_decisions_data
has_solutions_data
```

La règle centrale reste :

> **une ligne = une année × un pays d’origine**

---

# 17. Ce qui n’est pas encore réalisé

Cette phase ne construit pas encore :

```text
growth_t
lag_1
lag_2
rolling_mean
rolling_std
year_t1
total_t1
growth_t1
hausse_critique_suivante
```

Ces variables appartiennent aux étapes ultérieures.

La cible sera construite après l’analyse exploratoire et la validation du comportement temporel.

---

# 18. Contrôles temporels déjà établis sur IDMC

L’analyse précédente a identifié :

- **850 transitions** entre deux observations successives d’un même pays ;
- **835 transitions**, soit **98,2 %**, avec un écart d’un an ;
- **15 transitions**, soit **1,8 %**, avec un écart supérieur à un an ;
- un écart maximal de **9 ans**.

Conséquence :

> les années manquantes ne sont pas imputées artificiellement et une croissance annuelle ne doit être calculée que lorsqu’une véritable année `T+1` existe.

---

# 19. Lien avec la question prédictive

La consolidation prépare les variables explicatives potentielles disponibles à l’année `T`.

Principe :

```text
Informations connues à T
        ↓
Prédiction
        ↓
Hausse critique IDMC à T+1
```

Variables candidates :

```text
idmc_total
asylum_applications
decisions_total
decisions_recognized
recognition_rate
returned_idps
returned_refugees
resettlement
naturalisation
country_region
```

L’EDA devra déterminer :
- la couverture réelle de chaque variable ;
- leurs distributions ;
- leurs valeurs extrêmes ;
- leur évolution temporelle ;
- leurs relations avec `idmc_total` ;
- leur utilité potentielle pour la prédiction.

---

# 20. Prévention du target leakage

Aucune information de l’année `T+1` ne pourra être utilisée comme variable explicative pour prédire `T+1`.

Les variables suivantes serviront uniquement à construire la cible :

```text
year_t1
total_t1
growth_t1
hausse_critique_suivante
```

Elles ne devront jamais être présentes dans les features `X`.

Principe :

> **toute feature doit être disponible au moment de la prédiction, à T=0.**

---

# 21. Organisation des fichiers

```text
data/
│
├── raw/
├── cleaned/
├── normalized/
├── consolidated/
│   └── dataset_consolidated.csv
└── processed/
    ├── nettoyage_audit_log.csv
    ├── normalization_audit_log.csv
    ├── consolidation_audit_log.csv
    ├── consolidation_summary.csv
    └── fichiers d’anomalies éventuels
```

Les noms exacts des fichiers d’audit peuvent varier selon l’implémentation, mais la traçabilité doit être conservée.

---

# 22. Critères de validation avant EDA

| Contrôle | Critère attendu |
|---|---|
| Grain IDMC | unique sur `year × coo_id` |
| Doublons techniques | identifiés et tracés |
| Types | harmonisés |
| Codes pays | normalisés |
| UKN / STA | conservés |
| Jointures | `LEFT JOIN` |
| Nombre de lignes | inchangé après chaque enrichissement |
| Référentiel pays | relation `many_to_one` |
| Valeurs manquantes | conservées et mesurées |
| Agrégations | au grain `year × coo_id` |
| Cible ML | non créée à ce stade |
| Features temporelles | non créées à ce stade |

---

# 23. Prochaine étape — Analyse exploratoire

L’analyse exploratoire devra ensuite :

1. mesurer la couverture temporelle et géographique ;
2. mesurer la disponibilité de chaque source après consolidation ;
3. analyser les distributions et valeurs extrêmes ;
4. analyser l’évolution temporelle de `idmc_total` ;
5. étudier les relations entre IDMC, demandes d’asile, décisions et solutions ;
6. vérifier les corrélations et redondances ;
7. identifier les transformations utiles avant feature engineering ;
8. confirmer la faisabilité de la cible `T+1`.

L’EDA doit précéder la construction définitive du dataset ML afin que les choix de modélisation reposent sur les propriétés observées des données.
