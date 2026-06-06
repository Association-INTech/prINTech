---
title: "Rapport de Projet : PrINTech"
subtitle: "Encadrant : Mohamed SELLAMI | Version : 1.0"
subject: "Livrable 3"
author: |
  `\begin{tabular}{cc}
  Adam ALLOU & Arnaud COSTERMANS \\
  \footnotesize adam.allou@telecom-sudparis.eu & \footnotesize arnaud.costermans@telecom-sudparis.eu \\
  & \\
  Célian GIAUME & Yanis BELLOT \\
  \footnotesize celian.giaume@telecom-sudparis.eu & \footnotesize yanis.bellot@telecom-sudparis.eu
  \end{tabular}`{=latex}
date: "06 Juin 2026"
toc: true
toc-title: "Sommaire du Rapport Final"

---

\newpage

# 1. Introduction

Depuis cette année, l'association INTech du campus rencontrait des difficultés de gestion des impressions 3D faites par les membres. En effet, depuis cette année, INTech offre aux membres du campus la possibilité d'imprimer leur modèle 3D en devenant adhérents.
\newline
Actuellement, le système de gestion possède des problèmes. Les adhérents doivent télécharger et paramétrer un logiciel appelé slicer qui permet de transformer un modèle 3D en série d'instructions pour les imprimantes 3D, appelé G-code. On demande ensuite aux adhérents de charger le G-code sur les imprimantes, de lancer les impressions et ensuite de remplir un Google Form avec le nom de leur fichier, le poids de l'impression et d'autres paramètres.  
\newline
Ce système implique beaucoup d'étapes manuelles qui peuvent mener à des erreurs et rendre la fraude facile. Il faut aussi former tout le monde qui devient adhérent à l'utilisation des imprimantes.

![Diagramme BPMN du fonctionnement pré-PrIntech](diagrams/bpmn-before-diagram.svg)

Intervient alors le projet PrINTech consistant au développement d'une application web dynamique qui permette une gestion des impressions 3D de manière automatique.
\newline
Contrairement à la solution existante, ce projet a une vision plus long terme et facilite l'expansion à plus d'imprimantes ou de personnes et permet de réduire la charge de travail du bureau.

---

\newpage

# 2. Cahier des charges

## 2.1. Description du sujet

Notre projet consiste en la réalisation d'une Application Web dynamique. C'est-à-dire que le site doit être capable d'intéragir avec une base de donnée qu'on doit aussi implémenter. Ce site web permettra alors l'identification sécurisé des étudiants voulant imprimer des modèles 3D avec un système de gestion d'utilisateurs, de requêtes, et de gestion de queues.

---

\newpage

## 2.2. Liste des fonctionnalités de l'application
Afin de répondre au sujet, l'application doit intégrer les fonctionnalités suivantes, classées par priorité de développement :

| ID | Fonctionnalité de l'application | Description technique | Priorité |
| :--- |:--------------------------------| :--- | :---: |
| **F01** | **Authentification**            | Connexion et déconnexion via Django Auth. | Haute |
| **F02** | **Gestion des profils**         | Affichage et modification des informations utilisateurs. | Basse |
| **F03** | **Gestion des impressions**     | Flux complet d'impression 3D, du dépôt STL à la mise en file. | Haute |
| **F03-1** | **Déposer un STL**              | Upload d'un fichier STL. | Haute |
| **F03-2** | **Slicer automatique**          | Convertir le modèle en G-code via un slicer. | Moyenne |
| **F03-3** | **Estimation du coût**          | Calculer le prix d'impression à partir des paramètres. | Basse |
| **F03-4** | **Position dans la file**       | Afficher la place du travail dans la file. | Basse |
| **F03-5** | **Priorité projets INTech**     | Autoriser certains utilisateurs à prioriser leurs travaux. | Basse |
| **F03-6** | **Crédit restant**              | Afficher le crédit restant d'un utilisateur. | Basse |
| **F03-7** | **Quantité d'impressions**      | Indiquer le nombre d'exemplaires à imprimer. | Basse |
| **F04** | **Espace administrateur**       | Interface d'administration pour une gestion complète. | Moyenne |
| **F04-1** | **Gestion des utilisateurs**    | Créer, modifier et supprimer les utilisateurs. | Haute |
| **F04-2** | **Gestion des travaux**         | Créer, modifier et supprimer la file de travaux. | Moyenne |
| **F04-3** | **Reprise des erreurs**         | Déclarer un travail en erreur et le remettre en file. | Moyenne |
| **F05** | **Intégrations**                | SSO et notifications externes. | Pour aller plus loin |
| **F05-1** | **Intégration CAS**             | Inscription et connexion via le CAS de l'école. | Pour aller plus loin |
| **F05-2** | **Intégration Discord**         | Utiliser des webhooks pour les notifications. | Pour aller plus loin |
| **F05-3** | **Intégration HelloAsso**       | Créditer les comptes via HelloAsso. | Pour aller plus loin |
| **F06** | **Impression technique**        | Options avancées d'impression. | Pour aller plus loin |
| **F06-1** | **Utilisation de supports**     | Détecter quand l'utilisation de supports est nécessaire. | Pour aller plus loin |
| **F06-2** | **Paramétrage du slicer**       | Permettre l'upload d'un JSON de paramètres. | Pour aller plus loin |
| **F06-3** | **Choix des matériaux**         | Choisir un plastique autre que le PLA. | Pour aller plus loin |
| **F07** | **Gestion des filaments**       | Administration des filaments et du stock. | Pour aller plus loin |
| **F07-1** | **Activation des filaments**    | Activer et désactiver des filaments. | Pour aller plus loin |
| **F07-2** | **Gestion des filament**        | Gérer la quantité de filament restant. | Pour aller plus loin |
| **F07-3** | **Gestion de consommation**     | Rapport sur quantités, crédits et montant imprimé. | Pour aller plus loin |

---

\newpage

# 3. Conception

## 3.1. Base de données

![Schema de base de données](diagrams/db-diagram.svg)

---

\newpage

## 3.2. Séquence de l'Authentification

![Schema de l'authentification](diagrams/auth-diagram.svg)

---

\newpage

## 3.3. Processus d'impression 3D avec PrIntech

![Diagramme BPMN du fonctionnement post-PrIntech](diagrams/bpmn-after-diagram.svg)

---

\newpage

# 4. Réalisation et choix techniques

## 4.1. Choix des technologies

Les technologies pour développer une Application Web sont nombreuses. Pour faire la sélection des technologies, nous avons d'abord examiné lesquelles étaient capables de répondre à notre cahier des charges, puis ensuite sur les technologies auxquelles les membres de notre équipe avaient déjà de l'expérience. Sur la base de ces critères, nous avons sélectionné le stack suivant. D'abord pour le frontend :
\newline
- **AngularJS** : pour réaliser le frontend
\newline

Ensuite pour le backend :
\newline
- **Django** : pour réaliser le backend et l'API REST
\newline
- **PostgreSQL** : pour la base de données de l'application
\newline
- **Klipper** : comme firmware des imprimantes. Ce firmware communautaire vient remplacer celui du constructeur
\newline
- **Moonraker** : expose les API JSON-RPC de Klipper avec une API REST
\newline

Afin de partitionner logiquement les différentes couches (Frontend, Backend, et la Base De Données), nous avons utilisé **Docker** puisque c'est une technologie largement utilisée professionnellement qui permet la conteneurisation puis ensuite simplifie le déploiement.
\newline
Finalement, le déploiement sera assuré par **Nginx** avec **Gunicorn**.

--- 

\newpage

## 4.2. Réalisation

Afin de gérer nos librairies et versions de python, on a utilisé uv. C'est un équivalent de poetry mais en plus optimisé car implémenté en Rust. On doit alors préciser avant chaque commande "uv run" afin que le processus passe bien par uv.
\newline

Pour la conteneurisation, il a fallu créer les conteneurs. Pour se faire, il faut configurer un fichier "docker-compose.yaml" afin qu'il créer un conteneur PostgreSQL configuré sur le bon port après la commande.
\newline

Enfin pour la mise en commun du code, on a utilisé Git, et plus particulièrement git flow qui permet de produire simplement un cadre de travail professionnel (avec les branches main, develop, features/... etc.) et des commandes qui facilitent son utilisation.

---

\newpage

# 5. Validation et tests

---

\newpage

# 6. Bilan du projet

## 6.1. Plannings

### 6.1.1. Planning prévisionnel

![Planning prévisionnel du projet PrIntech](planning-previsionnel.pdf)

---

\newpage

### 6.1.2. Planning final

![Planning final du projet PrIntech](planning-final.pdf)

---

\newpage

### 6.1.3. Commentaires

- **Choix du planning prévisionnel** :
\newline
  - Angular est appris en parallele du projet. Le dev front ne commence qu'en fevrier.
  - Django est maitrise -> execution rapide. La partie Moonraker/Klipper est la plus incertaine.
  - la phase 3 est la plus longue a cause de l'apprentissage en cours.
\newline
- **Comparaison au planning réel** :
  - le projet a accumulé du retard notamment en raison d'autres dates importantes comme les projets Gate ou bien les partiels mais aussi car on a sous-estimé la complexité de certaines taches que nous verrons plus bas.
  - en réponse, on a ré-évalué le périmètre de notre projet afin d'en inclure à la date du rendu que les fonctionnalités nécessaires au vu du cahier des charges (Pas de tests e2e pour l'instant)
  - Ce retard n'est pas une fatalité puisque compte tenu de l'utilité du projet, celui-ci sera poursuivi à bien au-delà de la date de rendu.

---

\newpage

## 6.2. Plan de charges

### 6.2.1. Plan de charges prévisionnel

![Plan de Charge prévisionnel](plan-de-charge-previsionnel.pdf)

---

\newpage

### 6.2.2. Plan de charges final

---

\newpage

### 6.2.3. Commentaires

Nous avons bien utilisé le temps imparti. Celui-ci nous a permis de nous former non seulement sur les technologies auxquelles nous étions assignées mais aussi à comprendre l'ensemble du code que ce soit le front ou le back.
\newline

Nous sommes ainsi parvenu à rendre notre profil beaucoup plus attractif avec une compréhension plus fine des abstractions des différentes technologies mais aussi une vision beaucoup moins étroite de notre champ d'action. 
\newline
Pour indication, Célian ne connaissait pas Django au démarrage du projet, Adam démarrait sur Angular et Yanis était surtout focalisé sur Django; maintenant, nous sommes tous en mesure de comprendre le code de l'autre et de le corriger à travers un système de PR (Pull Request) sur Git.

---

\newpage

## 6.3. Difficultés rencontrées

Notre projet, malgré un produit final assez satisfaisant, a été le théâtres de certaines difficultés qui nous ont poussé à modifier notre champ d'action :
\newline

- La mise en commun du travail a été plus nébuleuse que prévu (notamment après l'instauration de PR qui ont empêchés le bon fonctionnement de certaines commandes de git flow)
\newline
- les retards accumulés qui on sappé l'efficacité du projet malgré un démarrage rapide
\newline
- l'utilisation des APIs des imprimantes 3D : Notre objectif initial était de relier directement les imprimantes 3D à l'application grâce au logiciel FDM Monster. Cependant, cette configuration s'est révélée difficile en raison des systèmes propriétaires des machines. De plus, comme les imprimantes sont très sollicitées, nous avons temporairement configuré le site pour qu'un administrateur lance chaque impression manuellement. Nous continuons néanmoins à travailler sur l'automatisation de ce processus.

---

\newpage

# 7. Conclusion et perspective

Malgré des difficultés, notre projet a produit une Application Web fonctionnelle selon les critères que nous nous étions imposés en préambule avec le cahier des charges.
\newline

Tout du moins, nous souhaiterions peaufiner ce projet au-delà du rendu final, que ce soit par la continuation de celui-ci par un autre groupe de projet informatique, ou bien par la maintenance de celui-ci par l'Association Intech elle-même.
En effet, ce projet est un projet enrichissant pour un étudiant ingénieur dans le développement informatique à travers l'utilisation d'outils et de technologies professionnels qui s'intègre pleinement dans le cadre de nos études et du campus avec Intech.
\newline

Ce projet, au-delà de la réalisation purement technique, est aussi une expérience d'équipe avec tout ses avantages et ses défauts qu'on a expérimenté (comme les retards et la mise en commun du code). Cela en fait donc une force pour tous nos futurs projets en groupe.
