"""
Nettoyage des données

Objectifs :
- ne jamais modifier les fichiers RAW ;
- conserver les anomalies métier ;
- supprimer uniquement les doublons strictement identiques ;
- tracer les anomalies et transformations ;
- exporter les données nettoyées dans data/cleaned ;
- exporter les rapports de contrôle dans data/processed.

Périmètre :
- IDMC
- Demandes d'asile
- Décisions d'asile
- Solutions
- Démographie
- Référentiel pays

Important :
- aucune consolidation ici ;
- aucune jointure ici ;
- aucune création de cible ici ;
- aucune imputation statistique ici.
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

RAW_DIR = BASE_DIR / "data" / "raw"
CLEAN_DIR = BASE_DIR / "data" / "cleaned"
PROCESSED_DIR = BASE_DIR / "data" / "processed"


FILES = {
    "idmc": RAW_DIR / "data_idmc_depuis_2000.csv",
    "demandes": RAW_DIR / "demandes_asile_depuis_2000.csv",
    "decisions": RAW_DIR / "decisions_asile_depuis_2000.csv",
    "solutions": RAW_DIR / "data_solutions_depuis_2000.csv",
    "demographie": RAW_DIR / "demographie_depuis_2000.csv",
    "pays": RAW_DIR / "countries.csv",
}


# Colonnes numériques pertinentes
NUMERIC_COLUMNS = {
    "idmc": [
        "total",
    ],

    "demandes": [
        "applied",
    ],

    "decisions": [
        "dec_recognized",
        "dec_other",
        "dec_rejected",
        "dec_closed",
        "dec_total",
    ],

    "solutions": [
        "returned_refugees",
        "resettlement",
        "naturalisation",
        "returned_idps",
    ],

    "demographie": [
        "f_0_4",
        "f_5_11",
        "f_12_17",
        "f_18_59",
        "f_60",
        "f_other",
        "f_total",
        "m_0_4",
        "m_5_11",
        "m_12_17",
        "m_18_59",
        "m_60",
        "m_other",
        "m_total",
        "total",
    ],
}


ID_COLUMNS = [
    "coo_id",
    "coa_id",
    "id",
]


MIN_YEAR = 2000
MAX_YEAR = 2025


# =============================================================================
# 2. LOGGING
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


# =============================================================================
# 3. JOURNAL D'AUDIT
# =============================================================================

audit_records = []


def add_audit(
    dataset,
    row_id,
    column,
    dimension,
    rule,
    value,
    severity,
    action,
):
    audit_records.append(
        {
            "dataset": dataset,
            "row_id": row_id,
            "column": column,
            "dimension_quality": dimension,
            "rule": rule,
            "observed_value": value,
            "severity": severity,
            "action": action,
        }
    )


# =============================================================================
# 4. VÉRIFICATION DES DOSSIERS
# =============================================================================

def check_directories():

    for directory in [
        RAW_DIR,
        CLEAN_DIR,
        PROCESSED_DIR,
    ]:
        if not directory.exists():
            raise FileNotFoundError(
                f"Dossier introuvable : {directory}"
            )

    logger.info(
        "Architecture des dossiers vérifiée."
    )


# =============================================================================
# 5. CHARGEMENT
# =============================================================================

def load_dataset(
    path,
    dataset_name,
):

    if not path.exists():
        raise FileNotFoundError(
            f"Fichier introuvable pour "
            f"'{dataset_name}' : {path}"
        )

    df = pd.read_csv(
        path,
        low_memory=False,
    )

    # Traçabilité vers la ligne RAW
    df.insert(
        0,
        "_row_id",
        np.arange(len(df)),
    )

    logger.info(
        "%s chargé : %s lignes | %s colonnes",
        dataset_name,
        len(df),
        len(df.columns),
    )

    return df


def load_all_datasets():

    return {
        name: load_dataset(
            path,
            name,
        )
        for name, path in FILES.items()
    }


# =============================================================================
# 6. NOMS DE COLONNES
# =============================================================================

def clean_column_names(df):

    df = df.copy()

    df.columns = [
        str(col)
        .strip()
        .replace(" ", "_")
        for col in df.columns
    ]

    return df


# =============================================================================
# 7. COLONNES TEXTE
# =============================================================================

def clean_text_columns(
    df,
    dataset_name,
):
    """
    Nettoyage uniquement :
    - suppression des espaces avant/après ;
    - chaîne vide -> pd.NA.

    La mise en majuscules systématique sera traitée
    dans l'étape de normalisation.
    """

    df = df.copy()

    text_columns = df.select_dtypes(
        include=[
            "object",
            "string",
        ]
    ).columns

    for col in text_columns:

        values = (
            df[col]
            .astype("string")
            .str.strip()
        )

        empty_mask = (
            values.eq("")
            .fillna(False)
        )

        for idx in df.index[empty_mask]:

            add_audit(
                dataset=dataset_name,
                row_id=df.loc[idx, "_row_id"],
                column=col,
                dimension="COMPLETENESS",
                rule="EMPTY_STRING",
                value="",
                severity="INFO",
                action="Converted to NA",
            )

        df[col] = values.replace(
            "",
            pd.NA,
        )

    return df


# =============================================================================
# 8. ANNÉES
# =============================================================================

def clean_year(
    df,
    dataset_name,
):

    if "year" not in df.columns:
        return df

    df = df.copy()

    original = df["year"]

    numeric = pd.to_numeric(
        original,
        errors="coerce",
    )


    # Valeur non numérique
    invalid_mask = (
        original.notna()
        & numeric.isna()
    )

    for idx in df.index[invalid_mask]:

        add_audit(
            dataset=dataset_name,
            row_id=df.loc[idx, "_row_id"],
            column="year",
            dimension="VALIDITY",
            rule="INVALID_YEAR",
            value=original.loc[idx],
            severity="ERROR",
            action="Converted to NA; row preserved",
        )


    # Année décimale
    decimal_mask = (
        numeric.notna()
        & (numeric % 1 != 0)
    )

    for idx in df.index[decimal_mask]:

        add_audit(
            dataset=dataset_name,
            row_id=df.loc[idx, "_row_id"],
            column="year",
            dimension="VALIDITY",
            rule="NON_INTEGER_YEAR",
            value=numeric.loc[idx],
            severity="ERROR",
            action="Converted to NA; row preserved",
        )

    numeric.loc[
        decimal_mask
    ] = np.nan


    # Année hors périmètre
    out_of_range_mask = (
        numeric.notna()
        & (
            (numeric < MIN_YEAR)
            | (numeric > MAX_YEAR)
        )
    )

    for idx in df.index[out_of_range_mask]:

        add_audit(
            dataset=dataset_name,
            row_id=df.loc[idx, "_row_id"],
            column="year",
            dimension="VALIDITY",
            rule="YEAR_OUT_OF_RANGE",
            value=numeric.loc[idx],
            severity="WARNING",
            action="Preserved for investigation",
        )


    df["year"] = numeric.astype(
        "Int64"
    )

    return df


# =============================================================================
# 9. IDENTIFIANTS
# =============================================================================

def clean_identifiers(
    df,
    dataset_name,
):

    df = df.copy()

    for col in ID_COLUMNS:

        if col not in df.columns:
            continue

        original = df[col]

        numeric = pd.to_numeric(
            original,
            errors="coerce",
        )


        invalid_mask = (
            original.notna()
            & numeric.isna()
        )

        decimal_mask = (
            numeric.notna()
            & (numeric % 1 != 0)
        )


        for idx in df.index[invalid_mask]:

            add_audit(
                dataset=dataset_name,
                row_id=df.loc[idx, "_row_id"],
                column=col,
                dimension="VALIDITY",
                rule="INVALID_IDENTIFIER",
                value=original.loc[idx],
                severity="ERROR",
                action="Converted to NA; row preserved",
            )


        for idx in df.index[decimal_mask]:

            add_audit(
                dataset=dataset_name,
                row_id=df.loc[idx, "_row_id"],
                column=col,
                dimension="VALIDITY",
                rule="NON_INTEGER_IDENTIFIER",
                value=numeric.loc[idx],
                severity="ERROR",
                action="Converted to NA; row preserved",
            )


        numeric.loc[
            decimal_mask
        ] = np.nan


        df[col] = numeric.astype(
            "Int64"
        )

    return df


# =============================================================================
# 10. VARIABLES NUMÉRIQUES
# =============================================================================

def clean_numeric_columns(
    df,
    dataset_name,
):

    df = df.copy()

    columns = NUMERIC_COLUMNS.get(
        dataset_name,
        [],
    )

    for col in columns:

        if col not in df.columns:
            continue

        original = df[col]

        numeric = pd.to_numeric(
            original,
            errors="coerce",
        )


        invalid_mask = (
            original.notna()
            & numeric.isna()
        )


        for idx in df.index[invalid_mask]:

            add_audit(
                dataset=dataset_name,
                row_id=df.loc[idx, "_row_id"],
                column=col,
                dimension="VALIDITY",
                rule="INVALID_NUMERIC_VALUE",
                value=original.loc[idx],
                severity="ERROR",
                action="Converted to NA; row preserved",
            )


        negative_mask = (
            numeric < 0
        ).fillna(False)


        for idx in df.index[negative_mask]:

            add_audit(
                dataset=dataset_name,
                row_id=df.loc[idx, "_row_id"],
                column=col,
                dimension="VALIDITY",
                rule="NEGATIVE_VALUE",
                value=numeric.loc[idx],
                severity="ERROR",
                action="Preserved for investigation",
            )


        df[col] = numeric

    return df


# =============================================================================
# 11. UKN / STA
# =============================================================================

def check_special_codes(
    df,
    dataset_name,
):
    """
    UKN = Unknown
    STA = Stateless

    Ces valeurs sont valides.
    Elles sont conservées.
    """

    for col in [
        "coo_iso",
        "coa_iso",
    ]:

        if col not in df.columns:
            continue

        values = (
            df[col]
            .astype("string")
            .str.strip()
            .str.upper()
        )

        for code in [
            "UKN",
            "STA",
        ]:

            count = (
                values == code
            ).sum()

            if count > 0:

                logger.info(
                    "%s | %s | %s : %s occurrence(s)",
                    dataset_name,
                    col,
                    code,
                    count,
                )


# =============================================================================
# 12. DOUBLONS STRICTS
# =============================================================================

def remove_strict_duplicates(
    df,
    dataset_name,
):

    df = df.copy()

    comparison_columns = [
        col
        for col in df.columns
        if col != "_row_id"
    ]


    duplicate_mask = df.duplicated(
        subset=comparison_columns,
        keep="first",
    )


    duplicates = df.loc[
        duplicate_mask
    ].copy()


    if duplicates.empty:

        logger.info(
            "%s : aucun doublon strict",
            dataset_name,
        )

        return df


    # Conserver une preuve avant suppression
    duplicates.to_csv(
        PROCESSED_DIR
        / f"{dataset_name}_strict_duplicates.csv",
        index=False,
    )


    for idx in duplicates.index:

        add_audit(
            dataset=dataset_name,
            row_id=df.loc[idx, "_row_id"],
            column="*",
            dimension="UNIQUENESS",
            rule="STRICT_DUPLICATE",
            value="Strict duplicate row",
            severity="WARNING",
            action=(
                "Removed from CLEAN copy; "
                "preserved in processed audit"
            ),
        )


    df = df.loc[
        ~duplicate_mask
    ].copy()


    logger.warning(
        "%s : %s doublon(s) strict(s) retiré(s)",
        dataset_name,
        len(duplicates),
    )


    return df


# =============================================================================
# 13. RAPPORT DE COMPLÉTUDE
# =============================================================================

def export_missing_summary(
    df,
    dataset_name,
):

    summary = pd.DataFrame(
        {
            "column": df.columns,

            "missing_count": [
                df[col].isna().sum()
                for col in df.columns
            ],

            "missing_pct": [
                round(
                    df[col].isna().mean() * 100,
                    2,
                )
                for col in df.columns
            ],
        }
    )


    summary.to_csv(
        PROCESSED_DIR
        / f"{dataset_name}_missing_summary.csv",
        index=False,
    )


# =============================================================================
# 14. NETTOYAGE D'UN DATASET
# =============================================================================

def clean_dataset(
    df,
    dataset_name,
):

    logger.info(
        "Début nettoyage : %s",
        dataset_name,
    )


    clean_df = (
        df
        .pipe(
            clean_column_names
        )
        .pipe(
            clean_text_columns,
            dataset_name
        )
        .pipe(
            clean_year,
            dataset_name
        )
        .pipe(
            clean_identifiers,
            dataset_name
        )
        .pipe(
            clean_numeric_columns,
            dataset_name
        )
    )


    check_special_codes(
        clean_df,
        dataset_name,
    )


    clean_df = remove_strict_duplicates(
        clean_df,
        dataset_name,
    )


    export_missing_summary(
        clean_df,
        dataset_name,
    )


    logger.info(
        "Fin nettoyage : %s | %s lignes",
        dataset_name,
        len(clean_df),
    )


    return clean_df


# =============================================================================
# 15. PIPELINE PRINCIPAL
# =============================================================================

def main():

    logger.info(
        "=== Phase 2 - Nettoyage : démarrage ==="
    )


    check_directories()


    raw_datasets = load_all_datasets()

    clean_datasets = {}


    for name, df in raw_datasets.items():

        clean_df = clean_dataset(
            df,
            name,
        )

        clean_datasets[
            name
        ] = clean_df


        clean_df.to_csv(
            CLEAN_DIR
            / f"{name}_clean.csv",
            index=False,
        )


    # -------------------------------------------------------------------------
    # Journal global d'audit
    # -------------------------------------------------------------------------

    audit_df = pd.DataFrame(
        audit_records
    )


    audit_df.to_csv(
        PROCESSED_DIR
        / "cleaning_audit_log.csv",
        index=False,
    )


    # -------------------------------------------------------------------------
    # Résumé RAW / CLEAN
    # -------------------------------------------------------------------------

    summary = pd.DataFrame(
        [
            {
                "dataset": name,
                "raw_rows": len(
                    raw_datasets[name]
                ),
                "clean_rows": len(
                    clean_datasets[name]
                ),
                "rows_removed": (
                    len(raw_datasets[name])
                    - len(clean_datasets[name])
                ),
            }
            for name in raw_datasets
        ]
    )


    summary.to_csv(
        PROCESSED_DIR
        / "cleaning_summary.csv",
        index=False,
    )


    logger.info(
        "=== Phase 2 - Nettoyage : terminé ==="
    )


# =============================================================================
# 16. EXÉCUTION
# =============================================================================

if __name__ == "__main__":
    main()