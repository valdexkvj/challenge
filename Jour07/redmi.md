# API de Conversion de Devises avec Cache
## Jour 7 – Projet Python

---

## Description

Ce projet est un convertisseur de devises robuste développé en Python.

Il permet :

- La récupération des taux de change en temps réel via une API externe
- La mise en cache des taux dans une base SQLite avec un TTL (Time To Live) de 10 minutes
- La gestion des erreurs réseau avec retry exponentiel
- Le calcul et l’affichage de l’historique sur 30 jours
- Une visualisation graphique ASCII et matplotlib
- Une interface CLI interactive complète

---

## Fonctionnalités

- Récupération des taux via API externe
- Cache SQLite avec expiration automatique (TTL : 10 minutes)
- Retry exponentiel avec jitter
- Historique des conversions sauvegardé
- Graphique ASCII dans le terminal
- Graphique détaillé avec matplotlib (optionnel)
- Nettoyage manuel du cache
- Architecture orientée objet modulaire
- Base de données thread-safe

---

## Architecture du Projet

currency_converter/
│
├── main.py
├── currency_cache.db (généré automatiquement)
└── README.md

---

## Technologies Utilisées

- Python 3.9+
- requests
- sqlite3
- json
- matplotlib (optionnel)
- dataclasses
- threading

---

## Installation

### 1. Cloner le projet

git clone <url-du-repo>
cd currency_converter

### 2. Installer les dépendances

pip install requests matplotlib

matplotlib est optionnel si vous ne souhaitez pas les graphiques détaillés.

---

## Lancement de l'application

python main.py

---

## Fonctionnement du Cache

- Si un taux existe en base et n’est pas expiré → utilisation du cache
- Sinon → appel API automatique
- TTL configuré à 10 minutes
- Nettoyage manuel possible via le menu

Base de données générée automatiquement :

currency_cache.db

---

## Retry Exponentiel

En cas d’erreur réseau :

- Maximum 3 tentatives
- Backoff exponentiel
- Jitter aléatoire
- Gestion des erreurs HTTP critiques (429, 500, 502, 503, 504)
- Timeout configurable

---

## Historique et Statistiques

Sur 30 jours :

- Minimum
- Maximum
- Moyenne
- Volatilité
- Visualisation ASCII dans le terminal
- Visualisation graphique détaillée (si matplotlib installé)

---

## Exemple d’utilisation

1. Lancer le programme
2. Choisir “Convertir une devise”
3. Entrer le montant
4. Saisir la devise source
5. Saisir la devise cible
6. Obtenir le résultat avec le taux et la date

---

## Gestion des erreurs

Le programme gère :

- Timeout réseau
- Erreurs HTTP
- Mauvaise saisie utilisateur
- Interruption clavier (CTRL + C)
- Exceptions inattendues

---

## Améliorations futures

- Interface graphique Tkinter
- Export CSV des conversions
- Tests unitaires avec pytest
- Dockerisation
- Support clé API privée
- Support multi-thread complet

---

## Citation

"Dis-moi avec qui tu marches, je te dirai qui tu es."

---

## Auteur

Projet réalisé dans le cadre du challenge Python – Jour 7.
