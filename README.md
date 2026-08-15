# Projet-UNHCR-ML
* ### Analyses des données collectées par UNHCR concernant les personnes déplacées de force ou apatrides

## Qu’est-ce que l’UNHCR?

![unhcr-logo](https://github.com/YnaPqt/Projet-UNHCR-ML/blob/main/unhcr-logo.png)

* **Identité :** Fondée par l'ONU le 14 décembre 1950, l'UNHCR ( United Nations Human Rights Council)  est une agence des Nations Unies pour les réfugiés. Elle a pour mission de garantir le droit d'asile et de trouver un refuge sûr pour ceux qui fuient la guerre, la violence, les persécutions ou les catastrophes.

* **Bénéficiaires :** L'agence protège et assiste les réfugiés, les demandeurs d'asile, les déplacés internes et les apatrides.

* **Actions d'urgence :** Présente dans plus de 130 pays, elle fournit une aide vitale immédiate — abris, nourriture, eau potable, soins médicaux, éducation — ainsi qu'un accompagnement psychosocial aux survivants de traumatismes.

* **Solutions à long terme :** Elle aide à reconstruire des vies dignes grâce à trois issues durables : le retour volontaire en sécurité, l'intégration locale ou la réinstallation dans un pays tiers.

* **Identité visuelle :** Son célèbre logo bleu représentant deux mains abritant une silhouette symbolise la protection, la bienveillance et l'espoir qu'elle apporte aux populations vulnérables.


## **Contenu et structure des données**


Les données présentées constituent des 5 jeux de données.

1. **UNHCR:**
    1. **End-year population figures** - il s'agit des données de stock (effectifs totaux) pour des catégories spécifiques de populations à la fin de chaque année, comprenant notamment les réfugiés, les déplacés internes(IDP) et les demandeurs d'asile.
    2. **Solutions**: Il s'agit de données de flux, représentant le nombre total d'individus ayant bénéficié de chaque type de solution au cours de l'année

2. **IDMC (Observatoire des situations de déplacement interne)** : Chiffres mondiaux pour les personnes déplacées à l'intérieur de leur propre pays en raison de conflits et de violences

3. **UNRWA (Office de secours et de travaux des Nations Unies) :** Réfugiés de Palestine sous le mandat de l'UNRWA

4. **Données démographiques (Demographics)**: Elles sont disponibles pour les données du HCR, de l'IDMC et de l'UNRWA. Aucune donnée démographique n'est disponible pour les données de réinstallation et de naturalisation

## **Structure des données (Data structure)**

Toutes les données sont ventilées par année, type de population, pays/territoire d'asile et d'origine. Le terme « pays/territoire d'asile » varie selon le contexte du jeu de données choisi


1. **Réinstallation (Resettlement) :** Dans ce contexte, il s'agit du pays d'arrivée, c'est-à-dire le pays dans lequel un réfugié a été réinstallé.

2. **Retours (Returns) :** Dans ce contexte, il s'agit du pays de départ, c'est-à-dire le pays depuis lequel un réfugié a été rapatrié de manière volontaire

Chaque variable peut prendre les valeurs suivantes:

1. **Année (Year)** : Un nombre entier compris entre 2000 et 2025.

2. **Types de population** : Ils sont identifiés par les codes suivants:

*   REF – Réfugié (Refugee)
*   ROC – Personnes dans une situation semblable à celle des réfugiés (People in refugee-like situation)
* ASY – Demandeurs d'asile (Asylum-seekers)
* OIP – Autres personnes ayant besoin d'une protection internationale (Other people in need of international protection)
* IDP – Personnes déplacées à l'intérieur de leur propre pays (Internally displaced persons)
* IOC – Personnes dans une situation semblable à celle des déplacés internes (People in IDP-like situation)
* STA – Personnes apatrides (Stateless people)
* OOC – Autres personnes necesitant l'aide du HCR (Others of concern)
* HST – Communauté d'accueil (Host community)

3. **Solutions :** Elles sont représentées par les codes suivants:

* RET – Réfugiés de retour / rapatriés (Returned refugees)
* RST – Réfugiés réinstallés (Resettled refugees)
* NAT – Réfugiés naturalisés (Naturalized refugees)
* RDP – Personnes déplacées internes de retour (Returned IDPs)

4. **Pays/territoire d'asile et d'origine :** La liste complète des pays de l'ONU est disponible sur la page méthodologique de la Division de statistique des Nations Unies (UNSD). Les codes pays ISO3 sont inclus. Le HCR utilise également les codes ISO3 non standard suivants:

* UKN pour Divers/Inconnu (Various/unknown)
* STA pour Apatride (Stateless)

## **Jeux de données sur les demandes d'asile et les décisions**


Dans les ensembles de données sur les demandes d'asile et les décisions d'asile, les paramètres suivants ont les valeurs:

**Autorité (Authority) :** L'une des valeurs de décision suivantes
 :
* **G** – Gouvernement (Government)
* **J** – Conjointe (Joint)
* **U** – HCR (UNHCR)


**Étape de la procédure pour les demandes d'asile (asylum applications):**

* **N** – Nouvelles demandes (New applications)
* **R** – Demandes réitérées (Repeat applications)
* **A** – Demandes en appel (Appeal applications)
* **NA** – Nouvelles demandes et demandes en appel : lorsque les données ont été fournies ensemble
* **NR** – Nouvelles demandes et demandes réitérées : lorsque les données ont été fournies ensemble
* **FA** – Premières demandes et demandes en appel : utilisé par la France en 2006, Israël en 2007 et le Tchad en 2017
* **J** – Judiciaire : les demandes sont au niveau judiciaire (Judiciary)
* **BL** – Arriéré (Backlog) : Demandes réitérées traitées lors d'événements spécifiques pour réduire l'arriéré des dossiers (utilisé par l'Italie en 2007 et l'Afrique du Sud en 2008)
* **SP** – Protection subsidiaire (Subsidiary protection) : utilisé avant l'intégration de la protection subsidiaire en Europe (utilisé par la Belgique en 2008 et l'Irlande en 2011)


**Étape de la procédure pour les décisions d'asile (asylum decisions):**

* **NA** – Nouvelles demandes (New Applications)
* **FI** – Décisions de première instance (First instance decisions)
* **AR** – Décisions de réexamen administratif (Administrative Review decisions)
* **RA** – Demandes réitérées/réouvertes (Repeat/reopened applications)
* **IN** – Services de citoyenneté et d'immigration des États-Unis (US Citizenship and Immigration Services)
* **EO** – Bureau exécutif d'examen de l'immigration des États-Unis (US Executive Office of Immigration Review)
* **JR** – Contrôle judiciaire (Judicial Review)
* **SP** – Protection subsidiaire (Subsidiary protection)
* **FA** – Première instance et appel (First instance and appeal)
* **TP** – Protection temporaire (Temporary protection)
* **TA** – Asile temporaire (Temporary asylum) ; utilisé en Fédération de Russie
* **BL** – Arriéré (Backlog) : Demandes réitérées traitées lors d'événements spécifiques pour réduire l'arriéré des dossiers (utilisé par le Royaume-Uni en 2000, l'Italie en 2007 et l'Afrique du Sud en 2008)
* **TR** – Autorisation temporaire de séjour en dehors de la procédure d'asile (Temporary leave to remain outside the asylum procedure)
* **CA** – Réglementations cantonales en Suisse (Cantonal regulations)

**Type de données (Data type) : L'un des types suivants:**
* **P** – Personnes (Persons)
* **C** – Dossiers / Cas (Cases)

## **Données démographiques**

**Dans les données démographiques, les paramètres ont les valeurs suivantes:**

* **Localisation (Location)** : La description textuelle du lieu. Depuis 2010, des métadonnées supplémentaires sont ajoutées après un « : » pour indiquer le type de lieu (par exemple : un point géographique, une région ou un pays).

* **Urbain / Rural (Urban / Rural)** : Indique si le lieu est urbain ou rural, un lieu urbain étant défini comme un établissement comptant plus de 5 000 habitants. Les valeurs possibles sont:

  * **C** – Camp (Camp) - Notez que cette classification « C » a été abandonnée après 2010, période à laquelle l'information sur le type d'hébergement est devenue disponible.

  * **U** – Urbain (Urban)
  * **R** – Rural
  * **V** – Divers/Inconnu (Various/unknown)
* **Type d'hébergement (Accommodation Type)** : Introduit en 2010 mais renseigné à partir de 2012.

  Ces codes représentent les types d'hebergements suivants:

  * **I** – Hébergement individuel au sein de communautés (Individual accommodation in communities)
  * **S** – Établissement informel (Informal settlement)
  * **P** – Établissement formel (Formal settlement)
  * **C** – Centre collectif (Collective centre)
  * **R** – Camp de transit (Transit camp)
  * **U** – Non défini (Undefined)










