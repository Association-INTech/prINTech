---
title: "Pré-rapport de Projet : PrINTech"
subtitle: "Encadrant : Mohamed SELLAMI | Version : 1.0"
subject: "Livrable 1"
author: |
  `\begin{tabular}{cc}
  Adam ALLOU & Arnaud COSTERMANS \\
  \footnotesize adam.allou@telecom-sudparis.eu & \footnotesize arnaud.costermans@telecom-sudparis.eu \\
  & \\
  Célian GIAUME & Yanis BELLOT \\
  \footnotesize celian.giaume@telecom-sudparis.eu & \footnotesize yanis.bellot@telecom-sudparis.eu
  \end{tabular}`{=latex}
date: "20 Février 2026"
toc: true
toc-title: "Sommaire du Pré-rapport"

---

# 1. Plan du Rapport Final

1. **Introduction :** Contexte, présentation du sujet et objectifs.
2. **Analyse et Spécifications :** Cahier des charges, recueil des besoins fonctionnels et non fonctionnels.
3. **Conception :** Architecture système, conception de la base de données.
4. **Réalisation et Choix Techniques :** Justification des packages, implémentation des fonctionnalités clés.
5. **Validation et Tests :** Stratégie de test, correction des bugs.
6. **Bilan de la Gestion de Projet :** Analyse du planning, plan de charge réel contre prévisionnel, difficultés rencontrées.
7. **Conclusion et Perspectives.**

---

\newpage

# 2. Cahier des charges

## 2.1. Description du sujet

Jusqu'alors, l'association INTech du campus Tsp-Imtbs rencontrait des difficultées de gestion des impressions 3D.
En effet, lorsqu'une personne veut faire une impression, elle doit demander à un membre de l'association qui annote alors sur un fichier Excel le nom de la dite personne.
C'est une tâche chronophage et manuelle qui implique des erreurs et un pré-paiement des bobines.

Intervient alors le projet PrINTech consistant au développement d'une application web dynamique qui permette une gestion des impressions 3D de manière automatique.

Contrairement aux solutions Excel existantes, ce projet s'inscrit dans une vision long terme avec une scalabilité des fonctionnalitées possible ainsi qu'une sécurité accrue.

## 2.2. Liste des fonctionnalités de l'application
Afin de répondre au sujet, l'application doit intégrer les fonctionnalités suivantes, classées par priorité de développement :

| ID | Fonctionnalité de l'application | Description technique | Priorité |
| :--- | :--- | :--- | :---: |
| **F01** | **Authentification** | Connexion et déconnexion via Django Auth. | Haute |
| **F02** | **Gestion des profils** | Affichage et modification des informations utilisateurs. | Basse |
| **F03** | **Gestion des impressions** | Flux complet d'impression 3D, du dépôt STL à la mise en file. | Haute |
| **F03-1** | **Déposer un STL** | Upload d'un fichier STL. | Haute |
| **F03-2** | **Slicer automatique** | Convertir le modèle en G-code via un slicer. | Moyenne |
| **F03-3** | **Estimation du coût** | Calculer le prix d'impression à partir des paramètres. | Basse |
| **F03-4** | **Position dans la file** | Afficher la place du travail dans la file. | Basse |
| **F03-5** | **Priorité projets INTech** | Autoriser certains utilisateurs à prioriser leurs travaux. | Basse |
| **F03-6** | **Crédit restant** | Afficher le crédit restant d'un utilisateur. | Basse |
| **F03-7** | **Quantité d'impressions** | Indiquer le nombre d'exemplaires à imprimer. | Basse |
| **F04** | **Espace administrateur** | Interface d'administration pour une gestion complète. | Moyenne |
| **F04-1** | **Gestion des utilisateurs** | Créer, modifier et supprimer les utilisateurs. | Haute |
| **F04-2** | **Gestion des travaux** | Créer, modifier et supprimer la file de travaux. | Moyenne |
| **F04-3** | **Reprise des erreurs** | Déclarer un travail en erreur et le remettre en file. | Moyenne |
| **F05** | **Intégrations** | SSO et notifications externes. | Pour aller plus loin |
| **F05-1** | **Intégration CAS** | Inscription et connexion via le CAS de l'école. | Pour aller plus loin |
| **F05-2** | **Intégration Discord** | Utiliser des webhooks pour les notifications. | Pour aller plus loin |
| **F05-3** | **Intégration HelloAsso** | Créditer les comptes via HelloAsso. | Pour aller plus loin |
| **F06** | **Impression technique** | Options avancées d'impression. | Pour aller plus loin |
| **F06-1** | **Utilisation de supports** | Détecter quand l'utilisation de supports est nécessaire. | Pour aller plus loin |
| **F06-2** | **Paramétrage du slicer** | Permettre l'upload d'un JSON de paramètres. | Pour aller plus loin |
| **F06-3** | **Choix des matériaux** | Choisir un plastique autre que le PLA. | Pour aller plus loin |
| **F07** | **Gestion des filaments** | Administration des filaments et du stock. | Pour aller plus loin |
| **F07-1** | **Activation des filaments** | Activer et désactiver des filaments. | Pour aller plus loin |
| **F07-2** | **Stock de filament** | Gérer la quantité de filament restant. | Pour aller plus loin |
| **F07-3** | **Rapport de consommation** | Rapport sur quantités, crédits et montant imprimé. | Pour aller plus loin |



---

\newpage

# 3. Conception Préliminaire
*Conformément au cycle de développement (Cycle en V), cette section valide l'étape de conception préliminaire en traduisant les besoins en architecture technique.*

## 3.1. Base de données

![Schema de base de données](diagrams/db-diagram.svg)

---

\newpage

## 3.2. Séquence de l'Authentification

![Schema de l'authentification](diagrams/auth-diagram.svg)

---