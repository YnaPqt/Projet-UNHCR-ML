"""
 — Normalisation des données
===================================

Objectifs :
- travailler uniquement à partir des fichiers nettoyés ;
- homogénéiser les formats avant consolidation ;
- standardiser les codes métier ;
- fiabiliser les futures jointures ;
- conserver les valeurs UKN et STA ;
- ne supprimer aucune ligne ;
- ne réaliser aucune agrégation ni jointure à ce stade.

Entrée :
    data/cleaned/

Sortie :
    data/normalized/

Important :
- les fichiers RAW ne sont jamais modifiés ;
- aucune valeur manquante n'est remplacée par 0 ;
- aucun mapping métier non documenté n'est appliqué ;
- aucune cible ML n'est construite ici.
"""

from pathlib import Path
import logging
import re

import pandas as pd


# =============================================================================
# 1. CONFIGURATION
# =============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parents[1]

CLEAN_DIR = BASE_DIR / "data" / "cleaned"
NORMALIZED_DIR = BASE_DIR / "data" / "normalized"
PROCESSED_DIR = BASE_DIR / "data" / "processed"


FILES = {
    "idmc": CLEAN_DIR / "idmc_clean.csv",
    "demandes": CLEAN_DIR / "demandes_clean.csv",
    "decisions": CLEAN_DIR / "decisions_clean.csv",
    "solutions": CLEAN_DIR / "solutions_clean.csv",
    "demographie": CLEAN_DIR / "demographie_clean.csv",
    "pays": CLEAN_DIR / "pays_clean.csv",
}


# -----------------------------------------------------------------------------
# Colonnes représentant des codes
# -----------------------------------------------------------------------------

CODE_COLUMNS = [
    "coo",
    "coo_iso",
    "coa",
    "coa_iso",
    "procedure_type",
    "app_type",
    "dec_level",
    "app_pc",
    "dec_pc",
    "code",
    "iso",
    "iso2",
]


# -----------------------------------------------------------------------------
# Colonnes représentant des libellés
# -----------------------------------------------------------------------------

NAME_COLUMNS = [
    "coo_name",
    "coa_name",
    "name",
    "nameOrigin",
    "nameLong",
    "nameShort",
    "nameFormal",
    "nationality",
    "majorArea",
    "region",
    "nameFr",
    "majorAreaFr",
    "regionFr",
]


ID_COLUMNS = [
    "coo_id",
    "coa_id",
    "id",
]


SPECIAL_CODES = {
    "UKN",
    "STA",
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
# 3. JOURNAL D'AUDIT
# =============================================================================

audit_records = []


def add_audit(
    dataset,
    column,
    rule,
    count,
    action,
):
    """
    Journal synthétique des transformations.

    Contrairement au nettoyage, nous ne journalisons pas
    nécessairement chaque ligne individuellement car la
    normalisation applique des transformations homogènes.
    """

    audit_records.append(
        {
            "dataset": dataset,
            "column": column,
            "rule": rule,
            "affected_rows": count,
            "action": action,
        }
    )


# =============================================================================
# 4. VÉRIFICATION DES DOSSIERS
# =============================================================================

def check_directories():

    if not CLEAN_DIR.exists():

        raise FileNotFoundError(
            f"Dossier cleaned introuvable : {CLEAN_DIR}"
        )


    if not PROCESSED_DIR.exists():

        raise FileNotFoundError(
            f"Dossier processed introuvable : {PROCESSED_DIR}"
        )


    # Le dossier de sortie peut être créé
    NORMALIZED_DIR.mkdir(
        parents=True,
        exist_ok=True,
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


    logger.info(
        "%s chargé : %s lignes | %s colonnes",
        dataset_name,
        len(df),
        len(df.columns),
    )


    return df


# =============================================================================
# 6. ESPACES MULTIPLES
# =============================================================================

def normalize_spaces(value):
    """
    Transforme par exemple :

        "Democratic   Republic   of Congo"

    en :

        "Democratic Republic of Congo"

    Les valeurs manquantes restent manquantes.
    """

    if pd.isna(value):
        return pd.NA


    value = str(value).strip()


    value = re.sub(
        r"\s+",
        " ",
        value,
    )


    return value


# =============================================================================
# 7. NORMALISATION DES COLONNES TEXTE
# =============================================================================

def normalize_text_columns(
    df,
    dataset_name,
):

    df = df.copy()


    text_columns = df.select_dtypes(
        include=[
            "object",
            "string",
        ]
    ).columns


    for col in text_columns:

        before = df[col].copy()


        df[col] = (
            df[col]
            .astype("string")
            .apply(normalize_spaces)
        )


        changed = (
            before.astype("string")
            != df[col].astype("string")
        ).fillna(False)


        count = int(
            changed.sum()
        )


        if count > 0:

            add_audit(
                dataset=dataset_name,
                column=col,
                rule="NORMALIZE_SPACES",
                count=count,
                action=(
                    "Leading/trailing and "
                    "multiple spaces standardized"
                ),
            )


    return df


# =============================================================================
# 8. NORMALISATION DES CODES
# =============================================================================

def normalize_codes(
    df,
    dataset_name,
):

    df = df.copy()


    for col in CODE_COLUMNS:

        if col not in df.columns:
            continue


        before = (
            df[col]
            .astype("string")
        )


        normalized = (
            before
            .str.strip()
            .str.upper()
        )


        changed = (
            before != normalized
        ).fillna(False)


        count = int(
            changed.sum()
        )


        if count > 0:

            add_audit(
                dataset=dataset_name,
                column=col,
                rule="UPPERCASE_CODE",
                count=count,
                action=(
                    "Code converted to uppercase"
                ),
            )


        df[col] = normalized


    return df


# =============================================================================
# 9. CONTRÔLE UKN / STA
# =============================================================================

def check_special_codes(
    df,
    dataset_name,
):

    for col in [
        "coo_iso",
        "coa_iso",
        "iso",
    ]:

        if col not in df.columns:
            continue


        values = (
            df[col]
            .astype("string")
            .str.upper()
        )


        for code in SPECIAL_CODES:

            count = int(
                values.eq(code).sum()
            )


            if count > 0:

                logger.info(
                    "%s | %s | %s = %s "
                    "(modalité valide conservée)",
                    dataset_name,
                    col,
                    code,
                    count,
                )


# =============================================================================
# 10. NORMALISATION DES IDENTIFIANTS
# =============================================================================

def normalize_identifiers(
    df,
    dataset_name,
):

    df = df.copy()


    for col in ID_COLUMNS:

        if col not in df.columns:
            continue


        numeric = pd.to_numeric(
            df[col],
            errors="coerce",
        )


        # Les identifiants ont déjà été contrôlés
        # lors du nettoyage.
        #
        # Ici on harmonise uniquement leur type.
        df[col] = numeric.astype(
            "Int64"
        )


    return df


# =============================================================================
# 11. NORMALISATION DE L'ANNÉE
# =============================================================================

def normalize_year(df):

    df = df.copy()


    if "year" not in df.columns:
        return df


    df["year"] = (
        pd.to_numeric(
            df["year"],
            errors="coerce",
        )
        .astype("Int64")
    )


    return df


# =============================================================================
# 12. CONTRÔLE DES CODES ISO
# =============================================================================

def check_iso_codes(
    df,
    dataset_name,
):

    """
    Contrôle syntaxique simple.

    IMPORTANT :
    UKN et STA sont considérés comme valides
    car documentés dans les données du projet.

    Aucun code invalide n'est supprimé.
    """

    for col in [
        "coo_iso",
        "coa_iso",
        "iso",
    ]:

        if col not in df.columns:
            continue


        values = (
            df[col]
            .astype("string")
            .str.upper()
        )


        # Code ISO attendu sur 3 caractères.
        # UKN / STA passent également ce contrôle.
        valid_mask = (
            values.isna()
            | values.str.fullmatch(
                r"[A-Z]{3}",
                na=False,
            )
        )


        invalid_count = int(
            (~valid_mask).sum()
        )


        if invalid_count > 0:

            logger.warning(
                "%s | %s : %s code(s) "
                "hors format attendu",
                dataset_name,
                col,
                invalid_count,
            )


            add_audit(
                dataset=dataset_name,
                column=col,
                rule="INVALID_ISO_FORMAT",
                count=invalid_count,
                action=(
                    "Preserved for investigation"
                ),
            )


# =============================================================================
# 13. CONTRÔLE DES LIBELLÉS PAYS
# =============================================================================

def normalize_country_names(
    df,
    dataset_name,
):

    """
    Les noms de pays ne sont PAS convertis en majuscules.

    Ils servent notamment à la lecture métier et peuvent
    contenir accents, ponctuation ou conventions propres
    au référentiel.

    On normalise uniquement les espaces.
    """

    df = df.copy()


    for col in NAME_COLUMNS:

        if col not in df.columns:
            continue


        df[col] = (
            df[col]
            .astype("string")
            .apply(normalize_spaces)
        )


    return df


# =============================================================================
# 14. CONTRÔLE DE L'UNICITÉ DU RÉFÉRENTIEL PAYS
# =============================================================================

def check_country_reference(
    df,
    dataset_name,
):

    if dataset_name != "pays":
        return


    for col in [
        "id",
        "code",
        "iso",
        "iso2",
    ]:

        if col not in df.columns:
            continue


        duplicate_count = int(
            df[col]
            .dropna()
            .duplicated()
            .sum()
        )


        if duplicate_count > 0:

            logger.warning(
                "Référentiel pays | %s : "
                "%s valeur(s) dupliquée(s)",
                col,
                duplicate_count,
            )


            add_audit(
                dataset=dataset_name,
                column=col,
                rule="REFERENCE_DUPLICATE",
                count=duplicate_count,
                action=(
                    "Preserved; investigation required"
                ),
            )


# =============================================================================
# 15. NORMALISATION D'UN DATASET
# =============================================================================

def normalize_dataset(
    df,
    dataset_name,
):

    logger.info(
        "Début normalisation : %s",
        dataset_name,
    )


    normalized_df = (
        df
        .pipe(
            normalize_text_columns,
            dataset_name
        )
        .pipe(
            normalize_codes,
            dataset_name
        )
        .pipe(
            normalize_country_names,
            dataset_name
        )
        .pipe(
            normalize_identifiers,
            dataset_name
        )
        .pipe(
            normalize_year
        )
    )


    check_special_codes(
        normalized_df,
        dataset_name,
    )


    check_iso_codes(
        normalized_df,
        dataset_name,
    )


    check_country_reference(
        normalized_df,
        dataset_name,
    )


    logger.info(
        "Fin normalisation : %s | %s lignes",
        dataset_name,
        len(normalized_df),
    )


    return normalized_df


# =============================================================================
# 16. PIPELINE PRINCIPAL
# =============================================================================

def main():

    logger.info(
        "=== Phase 2 - Normalisation : démarrage ==="
    )


    check_directories()


    normalized_datasets = {}


    for name, path in FILES.items():

        clean_df = load_dataset(
            path,
            name,
        )


        normalized_df = normalize_dataset(
            clean_df,
            name,
        )


        normalized_datasets[
            name
        ] = normalized_df


        normalized_df.to_csv(
            NORMALIZED_DIR
            / f"{name}_normalized.csv",
            index=False,
        )


    # -------------------------------------------------------------------------
    # Journal de normalisation
    # -------------------------------------------------------------------------

    audit_df = pd.DataFrame(
        audit_records
    )


    audit_df.to_csv(
        PROCESSED_DIR
        / "normalization_audit_log.csv",
        index=False,
    )


    # -------------------------------------------------------------------------
    # Résumé
    # -------------------------------------------------------------------------

    summary = pd.DataFrame(
        [
            {
                "dataset": name,
                "rows": len(df),
                "columns": len(df.columns),
            }
            for name, df
            in normalized_datasets.items()
        ]
    )


    summary.to_csv(
        PROCESSED_DIR
        / "normalization_summary.csv",
        index=False,
    )


    logger.info(
        "=== Phase 2 - Normalisation : terminée ==="
    )


# =============================================================================
# 17. EXÉCUTION
# =============================================================================

if __name__ == "__main__":
    main()