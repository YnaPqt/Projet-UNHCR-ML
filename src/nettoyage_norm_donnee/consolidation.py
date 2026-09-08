"""
Consolidation des données
===================================

Objectif
--------
Construire une table analytique unique au grain :

    1 ligne = 1 année × 1 pays d'origine

Table centrale :
    IDMC

Sources agrégées :
    - demandes d'asile
    - décisions d'asile
    - solutions

Enrichissement :
    - référentiel pays

Important
---------
- IDMC reste la table de référence.
- Les autres sources sont agrégées au grain year × coo_id.
- Toutes les jointures sont des LEFT JOIN.
- Aucun NaN n'est remplacé automatiquement par 0.
- Aucune cible ML n'est créée ici.
- Aucun lag, croissance ou rolling feature n'est créé ici.
"""

from pathlib import Path
import logging

import numpy as np
import pandas as pd


# =============================================================================
# 1. CONFIGURATION
# =============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parents[1]

NORMALIZED_DIR = BASE_DIR / "data" / "normalized"
CONSOLIDATED_DIR = BASE_DIR / "data" / "consolidated"
PROCESSED_DIR = BASE_DIR / "data" / "processed"


FILES = {
    "idmc": NORMALIZED_DIR / "idmc_normalized.csv",
    "demandes": NORMALIZED_DIR / "demandes_normalized.csv",
    "decisions": NORMALIZED_DIR / "decisions_normalized.csv",
    "solutions": NORMALIZED_DIR / "solutions_normalized.csv",
    "pays": NORMALIZED_DIR / "pays_normalized.csv",
}


# =============================================================================
# 2. LOGGING
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


# =============================================================================
# 3. AUDIT
# =============================================================================

audit_records = []


def add_audit(
    source,
    rule,
    status,
    rows_before=None,
    rows_after=None,
    message=None,
):
    audit_records.append(
        {
            "source": source,
            "rule": rule,
            "status": status,
            "rows_before": rows_before,
            "rows_after": rows_after,
            "message": message,
        }
    )


# =============================================================================
# 4. OUTILS GÉNÉRAUX
# =============================================================================

def check_directories():
    """
    Vérifie les répertoires nécessaires.
    """

    if not NORMALIZED_DIR.exists():
        raise FileNotFoundError(
            f"Dossier normalized introuvable : {NORMALIZED_DIR}"
        )

    CONSOLIDATED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def load_dataset(path, dataset_name):
    """
    Charge un fichier CSV normalisé.
    """

    if not path.exists():
        raise FileNotFoundError(
            f"Fichier introuvable pour '{dataset_name}' : {path}"
        )

    df = pd.read_csv(
        path,
        low_memory=False,
    )

    logger.info(
        "%s chargé : %s lignes | %s colonnes",
        dataset_name,
        len(df),
        len(df.columns),
    )

    return df


def require_columns(df, columns, dataset_name):
    """
    Vérifie que toutes les colonnes attendues existent.
    """

    missing = [
        col
        for col in columns
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"{dataset_name} : colonnes manquantes : {missing}"
        )


def check_unique_grain(df, keys, dataset_name):
    """
    Vérifie qu'une table est unique au grain demandé.
    """

    duplicate_mask = df.duplicated(
        subset=keys,
        keep=False,
    )

    duplicate_count = int(
        duplicate_mask.sum()
    )

    if duplicate_count == 0:

        logger.info(
            "%s : grain unique %s",
            dataset_name,
            keys,
        )

        return True


    duplicates = (
        df.loc[duplicate_mask]
        .sort_values(keys)
    )

    duplicates.to_csv(
        PROCESSED_DIR
        / f"{dataset_name}_grain_duplicates.csv",
        index=False,
    )

    add_audit(
        source=dataset_name,
        rule="CHECK_UNIQUE_GRAIN",
        status="WARNING",
        message=(
            f"{duplicate_count} ligne(s) non uniques "
            f"au grain {keys}"
        ),
    )

    logger.warning(
        "%s : %s ligne(s) non uniques au grain %s",
        dataset_name,
        duplicate_count,
        keys,
    )

    return False


# =============================================================================
# 5. TABLE CENTRALE IDMC
# =============================================================================

def prepare_idmc(idmc):
    """
    Prépare la table centrale IDMC.

    Grain attendu :
        year × coo_id
    """

    required = [
        "year",
        "coo_id",
        "total",
    ]

    require_columns(
        idmc,
        required,
        "idmc",
    )


    idmc_base = (
        idmc[
            required
        ]
        .rename(
            columns={
                "total": "idmc_total"
            }
        )
        .copy()
    )


    unique = check_unique_grain(
        idmc_base,
        [
            "year",
            "coo_id",
        ],
        "idmc",
    )


    if not unique:
        raise ValueError(
            "IDMC n'est pas unique au grain "
            "year × coo_id. "
            "Aucune agrégation automatique n'est appliquée."
        )


    return idmc_base


# =============================================================================
# 6. AGRÉGATION DES DEMANDES D'ASILE
# =============================================================================

def prepare_demandes(demandes):
    """
    Agrège les demandes d'asile au grain :

        year × coo_id

    Interprétation :
        total des demandes d'asile provenant
        d'un pays d'origine donné sur une année.
    """

    required = [
        "year",
        "coo_id",
        "applied",
    ]

    require_columns(
        demandes,
        required,
        "demandes",
    )


    demandes_origin = (
        demandes
        .groupby(
            [
                "year",
                "coo_id",
            ],
            as_index=False,
            dropna=False,
        )
        .agg(
            asylum_applications=(
                "applied",
                "sum",
            ),
            demandes_source_rows=(
                "applied",
                "size",
            ),
        )
    )


    check_unique_grain(
        demandes_origin,
        [
            "year",
            "coo_id",
        ],
        "demandes_aggregated",
    )


    return demandes_origin


# =============================================================================
# 7. AGRÉGATION DES DÉCISIONS D'ASILE
# =============================================================================

def prepare_decisions(decisions):
    """
    Agrège les décisions d'asile au grain :

        year × coo_id
    """

    required = [
        "year",
        "coo_id",
        "dec_recognized",
        "dec_other",
        "dec_rejected",
        "dec_closed",
        "dec_total",
    ]

    require_columns(
        decisions,
        required,
        "decisions",
    )


    decisions_origin = (
        decisions
        .groupby(
            [
                "year",
                "coo_id",
            ],
            as_index=False,
            dropna=False,
        )
        .agg(
            decisions_recognized=(
                "dec_recognized",
                "sum",
            ),
            decisions_other=(
                "dec_other",
                "sum",
            ),
            decisions_rejected=(
                "dec_rejected",
                "sum",
            ),
            decisions_closed=(
                "dec_closed",
                "sum",
            ),
            decisions_total=(
                "dec_total",
                "sum",
            ),
            decisions_source_rows=(
                "dec_total",
                "size",
            ),
        )
    )


    # -------------------------------------------------------------------------
    # Taux de reconnaissance
    # -------------------------------------------------------------------------

    decisions_origin[
        "recognition_rate"
    ] = np.where(
        decisions_origin[
            "decisions_total"
        ] > 0,

        decisions_origin[
            "decisions_recognized"
        ]
        /
        decisions_origin[
            "decisions_total"
        ],

        np.nan,
    )


    check_unique_grain(
        decisions_origin,
        [
            "year",
            "coo_id",
        ],
        "decisions_aggregated",
    )


    return decisions_origin


# =============================================================================
# 8. AGRÉGATION DES SOLUTIONS
# =============================================================================

def prepare_solutions(solutions):
    """
    Agrège les solutions au grain :

        year × coo_id

    Les mesures restent séparées.
    Aucun 'solutions_total' n'est créé.
    """

    required = [
        "year",
        "coo_id",
        "returned_refugees",
        "resettlement",
        "naturalisation",
        "returned_idps",
    ]

    require_columns(
        solutions,
        required,
        "solutions",
    )


    solutions_origin = (
        solutions
        .groupby(
            [
                "year",
                "coo_id",
            ],
            as_index=False,
            dropna=False,
        )
        .agg(
            returned_refugees=(
                "returned_refugees",
                "sum",
            ),
            resettlement=(
                "resettlement",
                "sum",
            ),
            naturalisation=(
                "naturalisation",
                "sum",
            ),
            returned_idps=(
                "returned_idps",
                "sum",
            ),
            solutions_source_rows=(
                "returned_idps",
                "size",
            ),
        )
    )


    check_unique_grain(
        solutions_origin,
        [
            "year",
            "coo_id",
        ],
        "solutions_aggregated",
    )


    return solutions_origin


# =============================================================================
# 9. RÉFÉRENTIEL PAYS
# =============================================================================

def prepare_country_dimension(pays):
    """
    Prépare le référentiel pays.

    Jointure future :
        consolidated.coo_id = pays.id
    """

    required = [
        "id",
        "iso",
    ]

    require_columns(
        pays,
        required,
        "pays",
    )


    # -------------------------------------------------------------------------
    # L'id pays doit être unique dans le référentiel
    # -------------------------------------------------------------------------

    duplicate_mask = (
        pays["id"].notna()
        & pays["id"].duplicated(
            keep=False
        )
    )


    if duplicate_mask.any():

        conflicts = (
            pays.loc[
                duplicate_mask
            ]
            .sort_values(
                "id"
            )
        )


        conflicts.to_csv(
            PROCESSED_DIR
            / "pays_id_conflicts.csv",
            index=False,
        )


        raise ValueError(
            "Le référentiel pays contient "
            "plusieurs lignes pour un même id."
        )


    optional_columns = [
        "name",
        "namefr",
        "region",
        "regionfr",
        "majorarea",
        "majorareafr",
    ]


    selected_columns = [
        col
        for col in (
            required
            + optional_columns
        )
        if col in pays.columns
    ]


    country_dim = (
        pays[
            selected_columns
        ]
        .copy()
        .rename(
            columns={
                "id": "coo_id",
                "iso": "country_iso",
                "name": "country_name",
                "namefr": "country_name_fr",
                "region": "country_region",
                "regionfr": "country_region_fr",
                "majorarea": "country_major_area",
                "majorareafr": "country_major_area_fr",
            }
        )
    )


    return country_dim


# =============================================================================
# 10. LEFT JOIN CONTRÔLÉ
# =============================================================================

def controlled_left_join(
    base,
    source,
    source_name,
    keys,
    validate,
):
    """
    LEFT JOIN avec contrôle du nombre de lignes.

    Une source d'enrichissement ne doit jamais
    multiplier les lignes de la table IDMC.
    """

    rows_before = len(
        base
    )


    result = base.merge(
        source,
        on=keys,
        how="left",
        validate=validate,
    )


    rows_after = len(
        result
    )


    if rows_after != rows_before:

        raise ValueError(
            f"{source_name} : le nombre de lignes "
            f"est passé de {rows_before} à {rows_after}."
        )


    add_audit(
        source=source_name,
        rule="LEFT_JOIN",
        status="OK",
        rows_before=rows_before,
        rows_after=rows_after,
        message=f"validate={validate}",
    )


    logger.info(
        "%s : LEFT JOIN OK | %s lignes",
        source_name,
        rows_after,
    )


    return result


# =============================================================================
# 11. FLAGS DE DISPONIBILITÉ
# =============================================================================

def add_availability_flags(df):
    """
    Un NaN après jointure ne signifie pas automatiquement zéro.

    Ces indicateurs permettent de distinguer :
    - donnée présente ;
    - donnée absente.
    """

    df = df.copy()


    availability_mapping = {
        "asylum_applications":
        "has_asylum_data",

        "decisions_total":
        "has_decisions_data",

        "returned_idps":
        "has_solutions_data",
    }


    for measure, flag in availability_mapping.items():

        if measure in df.columns:

            df[flag] = (
                df[measure]
                .notna()
                .astype("Int8")
            )


    return df


# =============================================================================
# 12. CONTRÔLES FINAUX
# =============================================================================

def final_quality_checks(
    consolidated,
    idmc_base,
):
    """
    Contrôles obligatoires après consolidation.
    """

    # -------------------------------------------------------------------------
    # 1. Aucune ligne IDMC perdue
    # -------------------------------------------------------------------------

    if len(consolidated) != len(idmc_base):

        raise ValueError(
            "Le nombre de lignes final "
            "diffère de la table IDMC."
        )


    # -------------------------------------------------------------------------
    # 2. Grain toujours unique
    # -------------------------------------------------------------------------

    duplicates = (
        consolidated
        .duplicated(
            [
                "year",
                "coo_id",
            ]
        )
        .sum()
    )


    if duplicates > 0:

        raise ValueError(
            f"{duplicates} doublon(s) détecté(s) "
            "au grain year × coo_id."
        )


    # -------------------------------------------------------------------------
    # 3. Contrôle pays non référencés
    # -------------------------------------------------------------------------

    if "country_iso" in consolidated.columns:

        missing_country = (
            consolidated[
                "coo_id"
            ].notna()
            &
            consolidated[
                "country_iso"
            ].isna()
        )


        count = int(
            missing_country.sum()
        )


        if count > 0:

            consolidated.loc[
                missing_country
            ].to_csv(
                PROCESSED_DIR
                / "unmatched_country_ids.csv",
                index=False,
            )


            add_audit(
                source="pays",
                rule="UNMATCHED_COUNTRY_ID",
                status="WARNING",
                message=(
                    f"{count} ligne(s) IDMC "
                    "sans correspondance dans le référentiel pays"
                ),
            )


    logger.info(
        "Contrôles finaux de consolidation : OK"
    )


# =============================================================================
# 13. PIPELINE PRINCIPAL
# =============================================================================

def main():

    logger.info(
        "=== Consolidation : démarrage ==="
    )


    check_directories()


    # -------------------------------------------------------------------------
    # Chargement
    # -------------------------------------------------------------------------

    idmc = load_dataset(
        FILES["idmc"],
        "idmc",
    )

    demandes = load_dataset(
        FILES["demandes"],
        "demandes",
    )

    decisions = load_dataset(
        FILES["decisions"],
        "decisions",
    )

    solutions = load_dataset(
        FILES["solutions"],
        "solutions",
    )

    pays = load_dataset(
        FILES["pays"],
        "pays",
    )


    # -------------------------------------------------------------------------
    # Préparation
    # -------------------------------------------------------------------------

    idmc_base = prepare_idmc(
        idmc
    )

    demandes_origin = prepare_demandes(
        demandes
    )

    decisions_origin = prepare_decisions(
        decisions
    )

    solutions_origin = prepare_solutions(
        solutions
    )

    country_dim = prepare_country_dimension(
        pays
    )


    # -------------------------------------------------------------------------
    # Table centrale
    # -------------------------------------------------------------------------

    consolidated = (
        idmc_base.copy()
    )


    # -------------------------------------------------------------------------
    # Jointure demandes
    # -------------------------------------------------------------------------

    consolidated = controlled_left_join(
        base=consolidated,
        source=demandes_origin,
        source_name="demandes",
        keys=[
            "year",
            "coo_id",
        ],
        validate="one_to_one",
    )


    # -------------------------------------------------------------------------
    # Jointure décisions
    # -------------------------------------------------------------------------

    consolidated = controlled_left_join(
        base=consolidated,
        source=decisions_origin,
        source_name="decisions",
        keys=[
            "year",
            "coo_id",
        ],
        validate="one_to_one",
    )


    # -------------------------------------------------------------------------
    # Jointure solutions
    # -------------------------------------------------------------------------

    consolidated = controlled_left_join(
        base=consolidated,
        source=solutions_origin,
        source_name="solutions",
        keys=[
            "year",
            "coo_id",
        ],
        validate="one_to_one",
    )


    # -------------------------------------------------------------------------
    # Jointure référentiel pays
    #
    # Plusieurs années pour un même pays côté IDMC :
    # many_to_one.
    # -------------------------------------------------------------------------

    consolidated = controlled_left_join(
        base=consolidated,
        source=country_dim,
        source_name="pays",
        keys=[
            "coo_id",
        ],
        validate="many_to_one",
    )


    # -------------------------------------------------------------------------
    # Flags de disponibilité
    # -------------------------------------------------------------------------

    consolidated = add_availability_flags(
        consolidated
    )


    # -------------------------------------------------------------------------
    # Contrôles finaux
    # -------------------------------------------------------------------------

    final_quality_checks(
        consolidated,
        idmc_base,
    )


    # -------------------------------------------------------------------------
    # Tri
    # -------------------------------------------------------------------------

    consolidated = (
        consolidated
        .sort_values(
            [
                "coo_id",
                "year",
            ]
        )
        .reset_index(
            drop=True
        )
    )


    # -------------------------------------------------------------------------
    # Export table consolidée
    # -------------------------------------------------------------------------

    output_path = (
        CONSOLIDATED_DIR
        / "dataset_consolidated.csv"
    )


    consolidated.to_csv(
        output_path,
        index=False,
    )


    # -------------------------------------------------------------------------
    # Export audit
    # -------------------------------------------------------------------------

    audit_columns = [
        "source",
        "rule",
        "status",
        "rows_before",
        "rows_after",
        "message",
    ]


    audit_df = pd.DataFrame(
        audit_records,
        columns=audit_columns,
    )


    audit_df.to_csv(
        PROCESSED_DIR
        / "consolidation_audit_log.csv",
        index=False,
    )


    # -------------------------------------------------------------------------
    # Résumé
    # -------------------------------------------------------------------------

    summary = pd.DataFrame(
        [
            {
                "rows":
                len(consolidated),

                "columns":
                len(
                    consolidated.columns
                ),

                "countries":
                consolidated[
                    "coo_id"
                ].nunique(
                    dropna=True
                ),

                "min_year":
                consolidated[
                    "year"
                ].min(),

                "max_year":
                consolidated[
                    "year"
                ].max(),

                "duplicate_year_country":
                int(
                    consolidated
                    .duplicated(
                        [
                            "year",
                            "coo_id",
                        ]
                    )
                    .sum()
                ),

                "idmc_missing":
                int(
                    consolidated[
                        "idmc_total"
                    ]
                    .isna()
                    .sum()
                ),

                "asylum_data_available_pct":
                round(
                    consolidated[
                        "has_asylum_data"
                    ]
                    .mean()
                    * 100,
                    2,
                ),

                "decisions_data_available_pct":
                round(
                    consolidated[
                        "has_decisions_data"
                    ]
                    .mean()
                    * 100,
                    2,
                ),

                "solutions_data_available_pct":
                round(
                    consolidated[
                        "has_solutions_data"
                    ]
                    .mean()
                    * 100,
                    2,
                ),
            }
        ]
    )


    summary.to_csv(
        PROCESSED_DIR
        / "consolidation_summary.csv",
        index=False,
    )


    logger.info(
        "Dataset consolidé créé : %s",
        output_path,
    )

    logger.info(
        "=== Consolidation : terminée ==="
    )


if __name__ == "__main__":
    main()