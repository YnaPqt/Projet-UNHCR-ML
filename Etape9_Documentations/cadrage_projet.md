# CADRAGE PROJET DATA & IA

## Analyse et anticipation des dynamiques de demandes d’asile à partir des données UNHCR & IDMC

**Domaine :** Humanitaire — Data & Intelligence Artificielle  
**Période d’analyse :** selon la couverture exploitable des données, jusqu’en 2025  
**Nature du projet :** Data Analytics, Data Quality, Feature Engineering et Machine Learning prédictif

---

# 1. Executive Summary

Les volumes de demandes d’asile évoluent fortement selon les années, les pays d’origine, les pays d’accueil et les différents corridors migratoires.

Pour une organisation humanitaire, un chercheur ou un décideur public, connaître les volumes historiques est nécessaire mais insuffisant.

L’enjeu opérationnel est également de pouvoir répondre suffisamment tôt à trois questions :

**Où la pression risque-t-elle d’augmenter ?**

**De quelle origine pourrait provenir cette augmentation ?**

**Quelle pourrait être son ampleur ?**

Le projet vise donc à construire un produit Data permettant de passer d’une analyse rétrospective des demandes d’asile à une logique d’**anticipation et de surveillance des hausses potentielles à T+1**.

Le cas d’usage prédictif principal consiste à déterminer si un segment de demandes d’asile risque de connaître une **augmentation supérieure à 15 % l’année suivante**.

Un second axe cherchera à estimer le **volume de demandes attendu à T+1**.

Les résultats ne doivent pas être interprétés comme une décision automatique d’allocation de ressources humanitaires. Ils constituent un **outil d’aide à la priorisation et à la surveillance**, devant être complété par des informations opérationnelles et contextuelles.

---

# 2. Contexte

L’UNHCR collecte et publie des données relatives aux populations relevant de son mandat et notamment aux demandes d’asile, pays d’origine, pays d’accueil et décisions associées.

Des données IDMC peuvent également apporter des informations complémentaires sur certaines dynamiques de déplacement interne.

Ces données constituent un patrimoine historique permettant d’étudier l’évolution des phénomènes dans le temps.

Cependant, leur exploitation pose plusieurs difficultés :

- multiplicité des dimensions géographiques et administratives ;
- forte variation des volumes ;
- données manquantes sur certaines variables ;
- différences de disponibilité selon les années ;
- nécessité de distinguer demandes d’asile, réfugiés, déplacés internes et autres populations ;
- risque de fuite d’information lors de la construction d’un modèle prédictif temporel.

Le projet adopte donc une approche **Data Product** : construire une chaîne analytique reproductible, documentée et évolutive plutôt qu’une analyse ponctuelle.

---

# 3. Problématique métier

## Comment exploiter les données historiques disponibles afin d’identifier les dynamiques des demandes d’asile et d’anticiper les pays, régions ou segments susceptibles de connaître une augmentation importante l’année suivante ?

Le projet cherche à transformer les données historiques en trois niveaux d’information :

**Comprendre → Détecter → Anticiper**

### Comprendre

Que s’est-il passé et où les demandes se concentrent-elles ?

### Détecter

Quels pays, régions ou corridors présentent des évolutions inhabituelles ou persistantes ?

### Anticiper

Quels segments présentent aujourd’hui des signaux pouvant annoncer une hausse importante à T+1 ?

---

# 4. Utilisateurs cibles et décisions associées

## Organisations humanitaires

Elles souhaitent identifier les territoires susceptibles de connaître une augmentation des demandes afin de renforcer la surveillance, préparer la coordination et approfondir l’analyse des capacités disponibles.

## Chercheurs et analystes

Ils souhaitent comprendre les dynamiques temporelles et géographiques, identifier les ruptures de tendance et rechercher les facteurs associés aux évolutions futures.

## Décideurs publics et institutions

Ils souhaitent disposer d’indicateurs permettant d’identifier les territoires pouvant nécessiter une attention particulière et compléter leurs analyses prospectives.

## Médias spécialisés

Ils souhaitent identifier et contextualiser les évolutions majeures, les concentrations géographiques, les accélérations et les changements de tendances.

---

# 5. Objectifs du produit Data

Le projet poursuit quatre objectifs.

## Objectif 1 — Fiabiliser

Construire un dataset consolidé, documenté et auditable à partir des différentes sources disponibles.

## Objectif 2 — Comprendre

Identifier les principales dynamiques temporelles, géographiques et catégorielles des demandes d’asile.

## Objectif 3 — Détecter

Identifier les pays, régions et corridors présentant simultanément des volumes importants, des accélérations ou des tendances persistantes.

## Objectif 4 — Anticiper

Évaluer la capacité des données historiques disponibles à prédire une hausse critique ou un volume futur de demandes à T+1.

---

# 6. Questions Business

## QB1 — Évolution temporelle

**Comment les demandes d’asile évoluent-elles dans le temps et quelles périodes présentent les principales ruptures de tendance ?**

Décision associée : comprendre le contexte historique et distinguer les tendances structurelles des épisodes exceptionnels.

---

## QB2 — Origines sous surveillance

**Quels pays et régions d’origine contribuent le plus aux volumes et aux accélérations annuelles des demandes d’asile ?**

Décision associée : identifier les zones d’origine nécessitant une surveillance analytique renforcée.

---

## QB3 — Pression sur les pays d’accueil

**Quels pays et régions d’accueil concentrent les volumes les plus importants et lesquels combinent volume élevé et forte croissance ?**

Décision associée : identifier les territoires pouvant connaître une pression croissante.

Une forte croissance ne suffit pas à définir une pression importante : le volume absolu doit également être pris en compte.

---

## QB4 — Corridors origine → accueil

**Quels corridors entre pays d’origine et pays d’accueil présentent les volumes, accélérations ou tendances persistantes les plus importants ?**

Décision associée : identifier les flux prioritaires à surveiller.

---

## QB5 — Persistance et rupture

**Les hausses observées constituent-elles des événements ponctuels ou s’inscrivent-elles dans une dynamique persistante sur plusieurs années ?**

Décision associée : différencier un choc temporaire d’une évolution structurelle.

---

## QB6 — Signaux précurseurs

**Quels indicateurs disponibles à l’année T caractérisent les segments qui connaissent ensuite une hausse importante à T+1 ?**

Décision associée : identifier les variables candidates au modèle prédictif.

Cette question constitue la transition entre l’EDA et le Machine Learning.

---

# 7. Questions prédictives

## QP1 — Classification : risque de hausse critique

### À partir des informations disponibles à l’année T, peut-on identifier les segments de demandes d’asile susceptibles de connaître une augmentation supérieure à 15 % à T+1 ?

**Type :** classification binaire

**Cible :** `hausse_critique_demandes_t1`

- `0` : hausse ≤ 15 %
- `1` : hausse > 15 %

**Horizon :** T+1 année.

Les observations sans véritable année T+1 ne sont pas artificiellement classées en 0 : elles restent non labellisables.

---

## QP2 — Régression : volume futur

### Peut-on estimer le nombre de demandes d’asile attendu à T+1 pour un pays, une région ou un segment ?

**Type :** régression

**Cible candidate :** `applied_t1`

Cette prédiction complète la classification :

- classification : **y aura-t-il une hausse critique ?**
- régression : **quel volume peut-on anticiper ?**

---

# 8. Principe de priorisation métier

Une augmentation relative ne représente pas nécessairement la même pression opérationnelle selon le volume initial.

Exemple :

- 100 → 130 demandes = **+30 %**, soit +30 demandes ;
- 100 000 → 112 000 = **+12 %**, soit +12 000 demandes.

Le premier segment franchit le seuil prédictif de +15 %, mais le second peut représenter une augmentation absolue beaucoup plus importante.

Le produit Data devra donc distinguer :

**risque de croissance relative**  
et  
**impact potentiel en volume absolu**.

Une évolution future pourra combiner :

- volume actuel ;
- croissance historique ;
- croissance prédite ;
- volume supplémentaire attendu ;
- persistance de la tendance.

L’objectif serait de produire un **niveau de vigilance analytique**, et non un score automatique de besoin humanitaire.

---

# 9. Périmètre V1

## IN-SCOPE

- demandes d’asile ;
- évolution annuelle ;
- pays d’origine ;
- pays d’accueil ;
- régions disponibles ;
- corridors origine → accueil ;
- types de procédures et catégories disponibles ;
- décisions exploitables à T=0 ;
- enrichissements IDMC suffisamment complets ;
- Data Quality ;
- EDA descriptive et analytique ;
- Feature Engineering temporel ;
- classification T+1 ;
- expérimentation d’une régression T+1.

## OUT-OF-SCOPE

En l’état actuel des données :

- estimation exhaustive de toutes les personnes déplacées de force dans le monde ;
- prédiction du stock total d’IDPs ;
- analyse complète des apatrides ;
- saisonnalité mensuelle ou trimestrielle à partir de données annuelles ;
- analyse complète de vulnérabilité par âge, sexe, handicap ou composition familiale ;
- causalité entre conflits et déplacements ;
- prédiction directe du nombre de lits, repas, médecins ou budgets nécessaires.

Ces besoins nécessitent des sources complémentaires.

---

# 10. Data Quality et gouvernance

Le dataset sera contrôlé selon six dimensions :

**Complétude :** quantification systématique des valeurs manquantes.

**Unicité :** contrôle des doublons stricts et du grain métier.

**Cohérence :** harmonisation des catégories et référentiels.

**Validité :** contrôle des taux, dates et valeurs possibles.

**Exactitude :** identification des valeurs statistiquement ou métier incohérentes.

**Fraîcheur :** vérification de la couverture temporelle.

Aucune anomalie métier ne sera supprimée silencieusement.

Les observations suspectes seront :

**conservées → marquées → documentées → auditées.**

---

# 11. Feature Engineering

Les variables prédictives devront être disponibles au moment réel de la prédiction T=0.

Les principales features candidates sont :

- `applied_t` ;
- `applied_lag1` ;
- `applied_lag2` ;
- croissance T/T-1 ;
- croissance T-1/T-2 ;
- moyenne mobile ;
- tendance sur plusieurs années ;
- volatilité historique ;
- nombre d’années consécutives de hausse ;
- variation absolue ;
- pays/région d’origine ;
- pays/région d’accueil ;
- corridor origine → accueil ;
- type de procédure ;
- type de demande ;
- indicateurs contextuels disponibles à T.

Les informations provenant de T+1 seront strictement interdites comme features.

---

# 12. Stratégie Machine Learning

La dimension temporelle impose une validation chronologique.

Le principe sera :

**Passé → Train → Validation → Futur → Test**

Un split aléatoire ne sera pas utilisé comme méthode principale d’évaluation.

Le preprocessing sera appris uniquement sur le Train.

Une baseline naïve sera calculée avant toute comparaison de modèles.

Pour la classification actuelle, la classe majoritaire représente environ **60,51 %** des observations labellisées : cette valeur constitue donc une première baseline d’accuracy.

Les performances seront évaluées avec :

- Recall ;
- Precision ;
- F1-score ;
- PR-AUC ;
- matrice de confusion.

Une attention particulière sera portée aux faux négatifs : segments connaissant réellement une hausse critique mais non détectés.

---

# 13. Critères de succès

## Succès Data

Dataset consolidé, documenté et anomalies tracées.

## Succès analytique

Capacité à identifier quantitativement :

- principales évolutions temporelles ;
- principales origines ;
- principaux pays d’accueil ;
- corridors en accélération ;
- phénomènes persistants.

## Succès ML

Le modèle doit apporter une valeur mesurable par rapport à la baseline et maintenir ses performances sur une période future jamais utilisée pendant l’entraînement.

## Succès métier

Les résultats doivent permettre de produire une liste compréhensible de territoires ou segments nécessitant une **surveillance renforcée**, accompagnée des facteurs expliquant cette priorisation.

---

# 14. Limites

Les résultats doivent être interprétés en tenant compte des limites suivantes :

- données principalement annuelles ;
- couverture variable selon les indicateurs ;
- absence de certaines dimensions démographiques ;
- données incomplètes pour certaines solutions durables ;
- évolution des distributions au cours du temps ;
- impossibilité d’inférer une causalité géopolitique avec les seules données disponibles ;
- impossibilité de convertir directement une prévision de demandes en besoins matériels.

Les limites seront documentées explicitement afin de ne pas présenter une précision ou une portée que les données ne permettent pas de soutenir.

---

# 15. North Star Metric

La North Star Metric du produit est :

**capacité à identifier suffisamment tôt les segments connaissant réellement une hausse critique à T+1.**

Elle sera principalement matérialisée par le **Recall de la classe “hausse critique”**, complété par la Precision afin d’éviter de générer un volume excessif de fausses alertes.

---

# 16. Proposition de valeur

Le produit doit permettre de passer de :

**« Que s’est-il passé ? »**

à :

**« Où observe-t-on une accélération ? »**

puis :

**« Quels territoires ou flux devons-nous surveiller en priorité ? »**

et enfin :

**« Quels segments risquent de connaître une hausse importante l’année prochaine et quelle pourrait être son ampleur ? »**

Le Machine Learning reste un outil d’aide à l’anticipation.

La décision opérationnelle finale reste humaine et doit être enrichie par les informations terrain, les capacités locales et le contexte humanitaire.