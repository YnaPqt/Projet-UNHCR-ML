# 📘 Dictionnaire des données

Ce dictionnaire décrit les principales variables présentes dans la table finale, leur rôle et leur signification métier.

---

## 1. Identifiants techniques et temporalité

| Colonne | Description |
|---|---|
| `_row_id` | Identifiant unique de chaque ligne dans la table finale. |
| `_demand_row_id` | Clé d'identification reliant la ligne à la table source des demandes d'asile. |
| `year` | Année d'enregistrement de la donnée. |

---

## 2. Origine de la population — Origin

| Colonne | Description |
|---|---|
| `coo_id` | Identifiant numérique interne du HCR pour le pays d'origine (*Country of Origin*). |
| `coo` | Code à 3 lettres interne du HCR pour le pays d'origine. |
| `coo_iso` / `origin_iso` | Code ISO3 officiel du pays d'origine, par exemple `SYR` ou `AFG`. |
| `origin_iso2` | Code ISO2 officiel du pays d'origine, par exemple `SY` ou `AF`. |
| `coo_name` / `origin_country` | Nom du pays d'origine en anglais. |
| `origin_country_fr` | Nom du pays d'origine en français. |
| `origin_region` / `origin_region_fr` | Région géographique d'origine en anglais / français, par exemple *Western Africa* / *Afrique de l'Ouest*. |
| `origin_major_area` / `origin_major_area_fr` | Continent ou grande zone géographique d'origine en anglais / français, par exemple *Africa* / *Afrique*. |

---

## 3. Pays d'asile / d'accueil — Asylum

| Colonne | Description |
|---|---|
| `coa_id` | Identifiant numérique interne du HCR pour le pays d'asile (*Country of Asylum*). |
| `coa` | Code à 3 lettres interne du HCR pour le pays d'asile. |
| `coa_iso` / `asylum_iso` | Code ISO3 officiel du pays d'asile. |
| `asylum_iso2` | Code ISO2 officiel du pays d'asile. |
| `coa_name` / `asylum_country` | Nom du pays d'asile en anglais. |
| `asylum_country_fr` | Nom du pays d'asile en français. |
| `asylum_region` / `asylum_region_fr` | Région géographique d'accueil en anglais / français. |
| `asylum_major_area` / `asylum_major_area_fr` | Continent ou grande zone géographique d'accueil en anglais / français. |

---

## 4. Demandes d'asile — Applications

| Colonne | Description |
|---|---|
| `procedure_type` | Étape de la procédure de demande d'asile, par exemple `N` pour une nouvelle demande, `R` pour une demande réitérée et `A` pour un appel. |
| `app_type` / `app_pc` | Indique si le comptage s'effectue en personnes individuelles (`P`) ou en dossiers/cas familiaux (`C`). |
| `applied` | Nombre total de demandes d'asile déposées au cours de la période. |
| `has_asylum_application_data` | Indicateur booléen (`1/0` ou `TRUE/FALSE`) précisant si des données de demandes d'asile sont présentes pour la ligne. |

---

## 5. Décisions d'asile — Decisions

| Colonne | Description |
|---|---|
| `dec_level` | Niveau de l'instance décisionnelle, par exemple `FI` pour première instance, `AR` pour réexamen administratif ou `JR` pour contrôle judiciaire. |
| `decisions_recognized` | Nombre de décisions positives accordant le statut officiel de réfugié. |
| `decisions_other` | Nombre de décisions accordant une autre forme de protection internationale, comme la protection subsidiaire (`SP`) ou temporaire (`TP`). |
| `decisions_rejected` | Nombre de décisions négatives correspondant à des rejets de demandes d'asile. |
| `decisions_closed` | Nombre de dossiers fermés ou classés sans décision au fond, par exemple à la suite d'un abandon ou d'un retrait. |
| `decisions_total` | Nombre total de décisions rendues : `decisions_recognized + decisions_other + decisions_rejected + decisions_closed`. |
| `decisions_source_rows` | Nombre de lignes sources agrégées pour calculer les chiffres de décisions. |
| `recognition_rate` | Taux de reconnaissance : part des décisions positives accordant une protection par rapport au total des décisions. |
| `rejection_rate` | Taux de rejet : part des décisions négatives par rapport au total des décisions. |
| `has_decisions_data` | Indicateur booléen précisant si des données de décisions d'asile sont disponibles pour la ligne. |

---

## 6. Solutions durables — Solutions

| Colonne | Description |
|---|---|
| `returned_refugees` | Nombre de réfugiés rapatriés volontairement dans leur pays d'origine au cours de l'année (`RET`). |
| `resettlement` | Nombre de réfugiés réinstallés dans un pays tiers (`RST`). |
| `naturalisation` | Nombre de réfugiés ayant obtenu la nationalité de leur pays d'accueil (`NAT`), utilisé comme indicateur d'intégration locale. |
| `returned_idps` | Nombre de personnes déplacées internes retournées dans leur région d'origine au cours de l'année (`RDP`). |
| `solutions_source_rows` | Nombre de lignes sources agrégées pour les données de solutions. |
| `has_solutions_data` | Indicateur booléen précisant si des données de solutions sont disponibles pour la ligne. |

---

## 7. Déplacements internes — IDMC / Internal Displacement

| Colonne | Description |
|---|---|
| `idmc_total_origin` | Stock total de personnes déplacées à l'intérieur de leur propre pays en raison de conflits ou de violences, selon les données de l'IDMC. |
| `has_idmc_data` | Indicateur booléen précisant si des données IDMC sont disponibles pour la ligne. |