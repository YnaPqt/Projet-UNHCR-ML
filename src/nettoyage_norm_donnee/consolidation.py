from pathlib import Path
import logging

import numpy as np
import pandas as pd


# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parents[1]

NORMALIZED_DIR = BASE_DIR / "data" / "normalized"
CONSOLIDATED_DIR = BASE_DIR / "data" / "consolidated"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

CONSOLIDATED_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


FILES = {
    "demandes": NORMALIZED_DIR / "demandes_normalized.csv",
    "decisions": NORMALIZED_DIR / "decisions_normalized.csv",
    "solutions": NORMALIZED_DIR / "solutions_normalized.csv",
    "idmc": NORMALIZED_DIR / "idmc_normalized.csv",
    "pays": NORMALIZED_DIR / "pays_normalized.csv",
}


OUTPUT_DETAIL = (
    CONSOLIDATED_DIR
    / "dataset_demandes_consolide_detail.csv"
)

OUTPUT_COUNTRY_YEAR = (
    CONSOLIDATED_DIR
    / "dataset_pays_asile_annee.csv"
)

AUDIT_FILE = (
    PROCESSED_DIR
    / "consolidation_demandes_audit.csv"
)


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


# =============================================================================
# AUDIT
# =============================================================================

AUDIT_COLUMNS = [
    "dataset",
    "check",
    "status",
    "count",
    "details",
]

audit_log = []


def add_audit(
    dataset,
    check,
    status,
    count=None,
    details=None,
):
    audit_log.append(
        {
            "dataset": dataset,
            "check": check,
            "status": status,
            "count": count,
            "details": details,
        }
    )


# =============================================================================
# OUTILS
# =============================================================================

def sum_preserve_na(series):
    """
    Somme en conservant NaN lorsque toutes les valeurs du groupe sont NaN.
    Évite de transformer artificiellement une absence d'information en 0.
    """
    return series.sum(min_count=1)


def load_csv(path, name):
    """
    Charge un fichier CSV normalisé.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"Fichier introuvable pour '{name}' : {path}"
        )

    df = pd.read_csv(
        path,
        low_memory=False,
    )

    logger.info(
        "%s chargé : %s lignes | %s colonnes",
        name,
        len(df),
        len(df.columns),
    )

    return df


def require_columns(df, columns, name):
    """
    Vérifie la présence des colonnes obligatoires.
    """
    missing = [
        col
        for col in columns
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"{name} : colonnes manquantes : {missing}"
        )


def check_unique(
    df,
    keys,
    name,
    export_name=None,
):
    """
    Vérifie si un grain métier est unique.
    Les lignes répétées ne sont pas supprimées automatiquement.
    """
    duplicated = df.duplicated(
        subset=keys,
        keep=False,
    )

    count = int(
        duplicated.sum()
    )

    if count == 0:
        add_audit(
            dataset=name,
            check="unique_grain",
            status="OK",
            count=0,
            details=str(keys),
        )

        return True

    add_audit(
        dataset=name,
        check="unique_grain",
        status="WARNING",
        count=count,
        details=str(keys),
    )

    if export_name:
        (
            df.loc[duplicated]
            .sort_values(keys)
            .to_csv(
                PROCESSED_DIR / export_name,
                index=False,
            )
        )

    return False


def left_join_controlled(
    left,
    right,
    on,
    name,
    validate,
):
    """
    LEFT JOIN sécurisé avec contrôle du nombre de lignes.
    """
    before = len(left)

    merged = left.merge(
        right,
        on=on,
        how="left",
        validate=validate,
    )

    after = len(merged)

    if before != after:
        raise ValueError(
            f"{name} : changement du nombre de lignes "
            f"({before} -> {after})"
        )

    add_audit(
        dataset=name,
        check="left_join_row_count",
        status="OK",
        count=after,
        details=f"join={on}, validate={validate}",
    )

    return merged


# =============================================================================
# DEMANDES — TABLE CENTRALE
# =============================================================================

def prepare_demandes(df):
    """
    Conserve les demandes au grain détaillé.

    Grain métier :
        year
        + coo_id
        + coa_id
        + procedure_type
        + app_type
        + dec_level
        + app_pc

    app_pc est conservé dans la clé car il distingue réellement
    certaines observations dans la source demandes.

    Aucune agrégation automatique n'est réalisée.
    """
    required = [
        "year",
        "coo_id",
        "coa_id",
        "procedure_type",
        "app_type",
        "dec_level",
        "app_pc",
        "applied",
    ]

    require_columns(
        df,
        required,
        "demandes",
    )

    demandes = df.copy()

    # Identifiant technique de ligne
    demandes["_demand_row_id"] = np.arange(
        len(demandes)
    )

    candidate_key = [
        "year",
        "coo_id",
        "coa_id",
        "procedure_type",
        "app_type",
        "dec_level",
        "app_pc",
    ]

    is_unique = check_unique(
        demandes,
        candidate_key,
        "demandes",
        "demandes_repeated_business_grain.csv",
    )

    if not is_unique:
        logger.warning(
            "Le grain candidat des demandes n'est pas unique. "
            "Les lignes sont conservées sans agrégation automatique."
        )

    demandes["has_asylum_application_data"] = 1

    return demandes


# =============================================================================
# DECISIONS
# =============================================================================

def prepare_decisions(df):
    """
    Agrège les décisions au grain commun avec les demandes :

        year
        + coo_id
        + coa_id
        + procedure_type
        + dec_level

    app_type n'existe pas dans decisions, donc il ne peut pas faire partie
    de la clé de jointure.
    """
    required = [
        "year",
        "coo_id",
        "coa_id",
        "procedure_type",
        "dec_level",
        "dec_recognized",
        "dec_other",
        "dec_rejected",
        "dec_closed",
        "dec_total",
    ]

    require_columns(
        df,
        required,
        "decisions",
    )

    group_keys = [
        "year",
        "coo_id",
        "coa_id",
        "procedure_type",
        "dec_level",
    ]

    decisions_agg = (
        df
        .groupby(
            group_keys,
            dropna=False,
            as_index=False,
        )
        .agg(
            decisions_recognized=(
                "dec_recognized",
                sum_preserve_na,
            ),
            decisions_other=(
                "dec_other",
                sum_preserve_na,
            ),
            decisions_rejected=(
                "dec_rejected",
                sum_preserve_na,
            ),
            decisions_closed=(
                "dec_closed",
                sum_preserve_na,
            ),
            decisions_total=(
                "dec_total",
                sum_preserve_na,
            ),
            decisions_source_rows=(
                "dec_total",
                "size",
            ),
        )
    )

    decisions_agg["recognition_rate"] = np.where(
        decisions_agg["decisions_total"].gt(0),
        (
            decisions_agg["decisions_recognized"]
            / decisions_agg["decisions_total"]
        ),
        np.nan,
    )

    decisions_agg["rejection_rate"] = np.where(
        decisions_agg["decisions_total"].gt(0),
        (
            decisions_agg["decisions_rejected"]
            / decisions_agg["decisions_total"]
        ),
        np.nan,
    )

    decisions_agg["has_decisions_data"] = 1

    check_unique(
        decisions_agg,
        group_keys,
        "decisions_aggregated",
    )

    return decisions_agg


# =============================================================================
# SOLUTIONS
# =============================================================================

def prepare_solutions(df):
    """
    Agrège les solutions au grain :

        year
        + coo_id
        + coa_id

    Les mesures restent séparées.
    """
    required = [
        "year",
        "coo_id",
        "coa_id",
        "returned_refugees",
        "resettlement",
        "naturalisation",
        "returned_idps",
    ]

    require_columns(
        df,
        required,
        "solutions",
    )

    group_keys = [
        "year",
        "coo_id",
        "coa_id",
    ]

    solutions_agg = (
        df
        .groupby(
            group_keys,
            dropna=False,
            as_index=False,
        )
        .agg(
            returned_refugees=(
                "returned_refugees",
                sum_preserve_na,
            ),
            resettlement=(
                "resettlement",
                sum_preserve_na,
            ),
            naturalisation=(
                "naturalisation",
                sum_preserve_na,
            ),
            returned_idps=(
                "returned_idps",
                sum_preserve_na,
            ),
            solutions_source_rows=(
                "returned_refugees",
                "size",
            ),
        )
    )

    solutions_agg["has_solutions_data"] = 1

    check_unique(
        solutions_agg,
        group_keys,
        "solutions_aggregated",
    )

    return solutions_agg


# =============================================================================
# REFERENTIEL PAYS
# =============================================================================

def prepare_country_dimension(df):
    """
    Prépare le référentiel pays.
    """
    require_columns(
        df,
        [
            "id",
            "iso",
        ],
        "pays",
    )

    if df["id"].duplicated().any():
        duplicates = df.loc[
            df["id"].duplicated(
                keep=False
            )
        ]

        duplicates.to_csv(
            PROCESSED_DIR
            / "countries_duplicate_id.csv",
            index=False,
        )

        raise ValueError(
            "Le référentiel pays contient plusieurs lignes pour un même id."
        )

    candidate_columns = [
        "id",
        "iso",
        "iso2",
        "name",
        "nameFr",
        "region",
        "regionFr",
        "majorArea",
        "majorAreaFr",
    ]

    available_columns = [
        col
        for col in candidate_columns
        if col in df.columns
    ]

    countries = (
        df[available_columns]
        .drop_duplicates("id")
        .copy()
    )

    return countries


def build_origin_dimension(countries):
    """
    Dimension du pays d'origine.
    """
    rename_map = {
        "id": "coo_id",
        "iso": "origin_iso",
        "iso2": "origin_iso2",
        "name": "origin_country",
        "nameFr": "origin_country_fr",
        "region": "origin_region",
        "regionFr": "origin_region_fr",
        "majorArea": "origin_major_area",
        "majorAreaFr": "origin_major_area_fr",
    }

    return countries.rename(
        columns=rename_map
    )


def build_asylum_dimension(countries):
    """
    Dimension du pays d'asile.
    """
    rename_map = {
        "id": "coa_id",
        "iso": "asylum_iso",
        "iso2": "asylum_iso2",
        "name": "asylum_country",
        "nameFr": "asylum_country_fr",
        "region": "asylum_region",
        "regionFr": "asylum_region_fr",
        "majorArea": "asylum_major_area",
        "majorAreaFr": "asylum_major_area_fr",
    }

    return countries.rename(
        columns=rename_map
    )


# =============================================================================
# IDMC — ENRICHISSEMENT OPTIONNEL
# =============================================================================

def prepare_idmc_context(df):
    """
    Prépare IDMC comme information contextuelle sur le pays d'origine.

    L'ajout n'est autorisé que si IDMC est unique au grain :
        year × coo_id

    Sinon, aucune agrégation automatique n'est réalisée.
    """
    required = [
        "year",
        "coo_id",
        "total",
    ]

    require_columns(
        df,
        required,
        "idmc",
    )

    key = [
        "year",
        "coo_id",
    ]

    repeated = df.duplicated(
        subset=key,
        keep=False,
    )

    if repeated.any():
        (
            df.loc[repeated]
            .sort_values(key)
            .to_csv(
                PROCESSED_DIR
                / "idmc_multiple_rows_year_origin.csv",
                index=False,
            )
        )

        add_audit(
            dataset="idmc",
            check="year_origin_grain",
            status="WARNING",
            count=int(repeated.sum()),
            details=(
                "IDMC non unique sur year × coo_id. "
                "Enrichissement ignoré."
            ),
        )

        logger.warning(
            "IDMC non unique sur year × coo_id : "
            "l'enrichissement IDMC est ignoré."
        )

        return None

    result = (
        df[
            [
                "year",
                "coo_id",
                "total",
            ]
        ]
        .rename(
            columns={
                "total": "idmc_total_origin"
            }
        )
        .copy()
    )

    result["has_idmc_data"] = 1

    return result


# =============================================================================
# CONSOLIDATION DETAILLEE
# =============================================================================

def build_detailed_dataset(
    demandes,
    decisions,
    solutions,
    origin_dim,
    asylum_dim,
    idmc_context=None,
):
    """
    Construit le dataset consolidé détaillé.

    Le nombre de lignes final doit rester identique
    au nombre de lignes de demandes.
    """
    result = demandes.copy()

    # -------------------------------------------------------------------------
    # Décisions
    # -------------------------------------------------------------------------

    decision_keys = [
        "year",
        "coo_id",
        "coa_id",
        "procedure_type",
        "dec_level",
    ]

    result = left_join_controlled(
        left=result,
        right=decisions,
        on=decision_keys,
        name="join_decisions",
        validate="many_to_one",
    )

    # -------------------------------------------------------------------------
    # Solutions
    # -------------------------------------------------------------------------

    solution_keys = [
        "year",
        "coo_id",
        "coa_id",
    ]

    result = left_join_controlled(
        left=result,
        right=solutions,
        on=solution_keys,
        name="join_solutions",
        validate="many_to_one",
    )

    # -------------------------------------------------------------------------
    # Pays d'origine
    # -------------------------------------------------------------------------

    result = left_join_controlled(
        left=result,
        right=origin_dim,
        on=["coo_id"],
        name="join_origin_country",
        validate="many_to_one",
    )

    # -------------------------------------------------------------------------
    # Pays d'asile
    # -------------------------------------------------------------------------

    result = left_join_controlled(
        left=result,
        right=asylum_dim,
        on=["coa_id"],
        name="join_asylum_country",
        validate="many_to_one",
    )

    # -------------------------------------------------------------------------
    # IDMC pays d'origine
    # -------------------------------------------------------------------------

    if idmc_context is not None:
        result = left_join_controlled(
            left=result,
            right=idmc_context,
            on=[
                "year",
                "coo_id",
            ],
            name="join_idmc_context",
            validate="many_to_one",
        )

    # -------------------------------------------------------------------------
    # Flags de présence des sources
    # -------------------------------------------------------------------------

    source_flags = [
        "has_decisions_data",
        "has_solutions_data",
        "has_idmc_data",
    ]

    for flag in source_flags:
        if flag in result.columns:
            result[flag] = (
                result[flag]
                .fillna(0)
                .astype("Int8")
            )

    return result


# =============================================================================
# DATASET BUSINESS : PAYS D'ASILE × ANNEE
# =============================================================================

def build_asylum_country_year(
    demandes,
    asylum_dim,
):
    """
    Produit le dataset analytique au grain :

        year × coa_id

    Règle de gouvernance :
    - coa_id = identifiant technique / métier du pays d'asile ;
    - coa = code pays issu de la source demandes (code source, pas forcément ISO3) ;
    - coa_iso = code ISO3 présent dans la source demandes ;
    - asylum_country = libellé standardisé du référentiel pays ;
    - asylum_iso = code ISO3 standardisé du référentiel pays.

    Les informations géographiques ne sont jamais agrégées par first()
    sans contrôle préalable de leur unicité.
    """

    required = [
        "year",
        "coa_id",
        "coo_id",
        "applied",
    ]

    require_columns(
        demandes,
        required,
        "demandes_for_country_year",
    )

    # -------------------------------------------------------------------------
    # 1. Agrégation des mesures au grain year × coa_id
    # -------------------------------------------------------------------------

    result = (
        demandes
        .groupby(
            [
                "year",
                "coa_id",
            ],
            dropna=False,
            as_index=False,
        )
        .agg(
            asylum_applications=(
                "applied",
                sum_preserve_na,
            ),
            origin_countries=(
                "coo_id",
                "nunique",
            ),
            demand_rows=(
                "applied",
                "size",
            ),
        )
    )

    # -------------------------------------------------------------------------
    # 2. Contrôle et ajout des codes/libellés présents dans la source demandes
    # -------------------------------------------------------------------------

    source_geo_candidates = [
        "coa",
        "coa_iso",
        "coa_name",
    ]

    source_geo_cols = [
        col
        for col in source_geo_candidates
        if col in demandes.columns
    ]

    if source_geo_cols:
        source_geo = (
            demandes[
                ["coa_id"] + source_geo_cols
            ]
            .drop_duplicates()
            .copy()
        )

        # Un coa_id ne doit pas correspondre à plusieurs codes/libellés source.
        source_mapping_check = (
            source_geo
            .groupby(
                "coa_id",
                dropna=False,
            )[source_geo_cols]
            .nunique(
                dropna=False
            )
        )

        inconsistent_source_mapping = (
            source_mapping_check.gt(1).any(axis=1)
        )

        if inconsistent_source_mapping.any():
            bad_ids = (
                inconsistent_source_mapping[
                    inconsistent_source_mapping
                ]
                .index
                .tolist()
            )

            (
                source_geo[
                    source_geo["coa_id"].isin(bad_ids)
                ]
                .sort_values("coa_id")
                .to_csv(
                    PROCESSED_DIR
                    / "audit_asylum_source_mapping_inconsistent.csv",
                    index=False,
                )
            )

            raise ValueError(
                "Incohérence dans la source demandes : "
                "un même coa_id correspond à plusieurs valeurs "
                f"parmi {source_geo_cols}. "
                "Voir audit_asylum_source_mapping_inconsistent.csv"
            )

        source_geo = (
            source_geo
            .drop_duplicates("coa_id")
        )

        result = left_join_controlled(
            left=result,
            right=source_geo,
            on=["coa_id"],
            name="join_asylum_country_year_source_codes",
            validate="many_to_one",
        )

    # -------------------------------------------------------------------------
    # 3. Ajout de la dimension pays standardisée
    # -------------------------------------------------------------------------

    result = left_join_controlled(
        left=result,
        right=asylum_dim,
        on=["coa_id"],
        name="join_asylum_country_year_dimension",
        validate="many_to_one",
    )

    # -------------------------------------------------------------------------
    # 4. Contrôles de cohérence source <-> référentiel
    # -------------------------------------------------------------------------

    # coa_iso et asylum_iso doivent être identiques quand les deux sont renseignés.
    if {
        "coa_iso",
        "asylum_iso",
    }.issubset(result.columns):

        iso_mismatch = (
            result["coa_iso"].notna()
            & result["asylum_iso"].notna()
            & result["coa_iso"].ne(result["asylum_iso"])
        )

        mismatch_count = int(
            iso_mismatch.sum()
        )

        add_audit(
            dataset="asylum_country_year",
            check="coa_iso_vs_asylum_iso",
            status="OK" if mismatch_count == 0 else "WARNING",
            count=mismatch_count,
            details=(
                "Comparaison du code ISO3 source demandes "
                "avec le code ISO3 du référentiel pays."
            ),
        )

        if mismatch_count > 0:
            (
                result.loc[
                    iso_mismatch,
                    [
                        "year",
                        "coa_id",
                        "coa",
                        "coa_iso",
                        "asylum_iso",
                        "coa_name",
                        "asylum_country",
                    ],
                ]
                .to_csv(
                    PROCESSED_DIR
                    / "audit_asylum_iso_mismatch.csv",
                    index=False,
                )
            )

    # coa_name et asylum_country doivent être identiques quand les deux existent.
    if {
        "coa_name",
        "asylum_country",
    }.issubset(result.columns):

        name_mismatch = (
            result["coa_name"].notna()
            & result["asylum_country"].notna()
            & result["coa_name"].str.strip().ne(
                result["asylum_country"].str.strip()
            )
        )

        mismatch_count = int(
            name_mismatch.sum()
        )

        add_audit(
            dataset="asylum_country_year",
            check="coa_name_vs_asylum_country",
            status="OK" if mismatch_count == 0 else "WARNING",
            count=mismatch_count,
            details=(
                "Comparaison du libellé pays source demandes "
                "avec le libellé du référentiel pays."
            ),
        )

        if mismatch_count > 0:
            (
                result.loc[
                    name_mismatch,
                    [
                        "year",
                        "coa_id",
                        "coa",
                        "coa_iso",
                        "coa_name",
                        "asylum_iso",
                        "asylum_country",
                    ],
                ]
                .to_csv(
                    PROCESSED_DIR
                    / "audit_asylum_country_name_mismatch.csv",
                    index=False,
                )
            )

    # -------------------------------------------------------------------------
    # 5. Contrôle d'unicité du dataset final
    # -------------------------------------------------------------------------

    check_unique(
        result,
        [
            "year",
            "coa_id",
        ],
        "asylum_country_year",
        "asylum_country_year_duplicate_grain.csv",
    )

    # -------------------------------------------------------------------------
    # 6. Ordre explicite des colonnes
    # -------------------------------------------------------------------------

    preferred_order = [
        "year",
        "coa_id",

        # Informations source demandes
        "coa",
        "coa_iso",
        "coa_name",

        # Informations standardisées référentiel
        "asylum_iso",
        "asylum_iso2",
        "asylum_country",
        "asylum_country_fr",
        "asylum_region",
        "asylum_region_fr",
        "asylum_major_area",
        "asylum_major_area_fr",

        # Mesures métier
        "asylum_applications",
        "origin_countries",
        "demand_rows",
    ]

    ordered = [
        col
        for col in preferred_order
        if col in result.columns
    ]

    remaining = [
        col
        for col in result.columns
        if col not in ordered
    ]

    result = result[
        ordered + remaining
    ]

    return result



# =============================================================================
# MAIN
# =============================================================================

def main():

    logger.info(
        "=== Consolidation centrée sur les demandes d'asile ==="
    )

    # =========================================================================
    # 1. Chargement
    # =========================================================================

    demandes_raw = load_csv(
        FILES["demandes"],
        "demandes",
    )

    decisions_raw = load_csv(
        FILES["decisions"],
        "decisions",
    )

    solutions_raw = load_csv(
        FILES["solutions"],
        "solutions",
    )

    pays_raw = load_csv(
        FILES["pays"],
        "pays",
    )

    idmc_raw = None

    if FILES["idmc"].exists():
        idmc_raw = load_csv(
            FILES["idmc"],
            "idmc",
        )
    else:
        logger.warning(
            "Fichier IDMC absent : "
            "la consolidation continuera sans IDMC."
        )

    # =========================================================================
    # 2. Préparation
    # =========================================================================

    demandes = prepare_demandes(
        demandes_raw
    )

    decisions = prepare_decisions(
        decisions_raw
    )

    solutions = prepare_solutions(
        solutions_raw
    )

    countries = prepare_country_dimension(
        pays_raw
    )

    origin_dim = build_origin_dimension(
        countries
    )

    asylum_dim = build_asylum_dimension(
        countries
    )

    idmc_context = None

    if idmc_raw is not None:
        idmc_context = prepare_idmc_context(
            idmc_raw
        )

    # =========================================================================
    # 3. Dataset consolidé détaillé
    # =========================================================================

    detailed = build_detailed_dataset(
        demandes=demandes,
        decisions=decisions,
        solutions=solutions,
        origin_dim=origin_dim,
        asylum_dim=asylum_dim,
        idmc_context=idmc_context,
    )

    # Vérification critique :
    # la consolidation ne doit pas multiplier les lignes.
    if len(detailed) != len(demandes):
        raise ValueError(
            "Le dataset détaillé n'a pas conservé "
            "le nombre de lignes de demandes."
        )

    add_audit(
        dataset="consolidation",
        check="detailed_row_count",
        status="OK",
        count=len(detailed),
        details=(
            "Nombre de lignes identique à la table demandes."
        ),
    )

    # =========================================================================
    # 4. Dataset analytique pays d'asile × année
    # =========================================================================

    asylum_country_year = build_asylum_country_year(
        demandes=demandes,
        asylum_dim=asylum_dim,
    )

    # =========================================================================
    # 5. Exports
    # =========================================================================

    detailed.to_csv(
        OUTPUT_DETAIL,
        index=False,
    )

    asylum_country_year.to_csv(
        OUTPUT_COUNTRY_YEAR,
        index=False,
    )


    # =========================================================================
    # 6. Audit
    # =========================================================================

    audit_df = pd.DataFrame(
        audit_log,
        columns=AUDIT_COLUMNS,
    )

    audit_df.to_csv(
        AUDIT_FILE,
        index=False,
    )

    # =========================================================================
    # 7. Logs finaux
    # =========================================================================

    logger.info(
        "Demandes source           : %s lignes",
        len(demandes_raw),
    )

    logger.info(
        "Dataset consolidé détaillé : %s lignes",
        len(detailed),
    )

    logger.info(
        "Pays d'asile × année       : %s lignes",
        len(asylum_country_year),
    )

    logger.info(
        "Pays d'origine distincts   : %s",
        detailed["coo_id"].nunique(
            dropna=True
        ),
    )

    logger.info(
        "Pays d'asile distincts     : %s",
        detailed["coa_id"].nunique(
            dropna=True
        ),
    )

    logger.info(
        "Période                    : %s - %s",
        detailed["year"].min(),
        detailed["year"].max(),
    )

    logger.info(
        "Dataset détaillé exporté   : %s",
        OUTPUT_DETAIL,
    )

    logger.info(
        "Dataset pays/année exporté : %s",
        OUTPUT_COUNTRY_YEAR,
    )

    logger.info(
        "Audit exporté              : %s",
        AUDIT_FILE,
    )


    logger.info(
        "=== Consolidation terminée ==="
    )


if __name__ == "__main__":
    main()