"""
Asylum Decisions Data

> Décisions prises concernant les demandes d’asile, classées par année, par pays d’asile et par pays d’origine. Les demandes d’asile sont des demandes de protection internationale, et les décisions rendues peuvent être positives, négatives ou faire l’objet d’une clôture pour un autre motif.

"""
import time
import requests
import pandas as pd
from pathlib import Path

RAW_DATA_DIR = Path(".") / "data" / "raw"

# API Endpoint
url = "https://api.unhcr.org/population/v1/asylum-decisions/"

page = 1
limit = 5000
tous_les_resultats = []

while True:
    params = {
        "page": page,
        "limit": limit,
        "yearFrom": 2000,
        "coo_all": "true",
        "coa_all": "true",
        "cf_type": "ISO"
    }

    try:
        response = requests.get(
            url,
            params=params,
            headers={
                "Accept": "application/json",
                "User-Agent": "Python UNHCR data project"
            },
            timeout=60
        )

        print(
            f"Page {page} — "
            f"code HTTP {response.status_code}"
        )

        response.raise_for_status()

        data = response.json()
        items = data.get("items", [])

        if not items:
            print("Aucun résultat supplémentaire.")
            break

        tous_les_resultats.extend(items)

        print(
            f"{len(items)} lignes récupérées — "
            f"total : {len(tous_les_resultats)}"
        )

        if len(items) < limit:
            print("Dernière page atteinte.")
            break

        page += 1
        time.sleep(0.2)

    except requests.exceptions.RequestException as erreur:
        print("Erreur HTTP :", erreur)
        break

    except ValueError:
        print("La réponse n'est pas au format JSON.")
        print(response.text[:1000])
        break

df = pd.DataFrame(tous_les_resultats)

print("Dimensions finales :", df.shape)
print(df.head())

df.to_csv(
    RAW_DATA_DIR / "decisions_asile_depuis_2000.csv",
    index=False,
    encoding="utf-8-sig"
)