# Système Bancaire Python

Ce projet est un **système bancaire simplifié** écrit en Python, avec gestion des comptes clients, administrateurs et super-administrateurs.  
Le système respecte des **permissions strictes** selon le rôle de l’utilisateur.

---

## Fonctionnalités principales

### 1. Gestion des utilisateurs
- **SuperAdmin**
  - Peut créer des **Admins**
  - Peut créer des **Comptes Clients**
  - Peut effectuer des **dépôts sur les comptes**
  - **Ne peut pas** retirer ni faire de virement
- **Admin**
  - Peut créer des **Comptes Clients**
  - Peut effectuer des **dépôts sur les comptes**
  - **Ne peut pas** retirer ni faire de virement
- **Client**
  - Peut effectuer **retrait d’argent**
  - Peut faire des **virements vers d’autres comptes**
  - Peut consulter **son historique**
  - **Ne peut pas** faire de dépôt

### 2. Gestion des comptes
- **Compte classique**
  - Dépôt, retrait, virement
  - Historique des opérations
- **Compte Épargne**
  - Calcul automatique des intérêts
- **Compte Professionnel**
  - Virement avec frais bancaires
  - Application de frais supplémentaires si nécessaire

### 3. Sécurité
- Mot de passe **haché** avec SHA256
- Login avec vérification de rôle et permissions
- Sauvegarde et chargement automatique des utilisateurs et comptes via JSON

---

## Installation

1. Cloner le dépôt :
```bash
git clone <url_du_depot>
