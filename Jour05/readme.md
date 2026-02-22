# ♠️ Jeu de Poker – Texas Hold'em (Console)

Un jeu de **Texas Hold'em en Python** jouable directement dans le terminal, avec interface ASCII colorée, système de mise, bots automatiques et évaluation des mains.

---

##  Fonctionnalités

-  Jeu interactif en console
-  Cartes affichées en ASCII
-  Couleurs ANSI dans le terminal
-  Système de mise (relance, suivre, se coucher)
-  Bots avec décisions aléatoires pondérées
-  Gestion du pot
-  Évaluation automatique des mains
-  Menu principal interactif
-  Animation texte

---

##  Classement des mains

Le moteur reconnaît les combinaisons suivantes :

| Rang | Combinaison |
|------|-------------|
| 1 | Carte Haute |
| 2 | Paire |
| 3 | Double Paire |
| 4 | Brelan |
| 5 | Suite |
| 6 | Couleur |
| 7 | Full House |
| 8 | Carré |
| 9 | Quinte Flush |

---

##  Architecture du Projet

###  Classes principales

### `Carte`
Représente une carte avec :
- valeur (2 → A)
- couleur (♠ ♣ ♥ ♦)

---

### `Deck`
- Génère les 52 cartes
- Mélange automatiquement
- Permet de tirer des cartes

---

### `Main`
- Contient les cartes d’un joueur
- Évalue la meilleure combinaison

---

### `Joueur`
- Nom
- Nombre de jetons
- Main de cartes

---

### `Bot`
- Hérite de `Joueur`
- Décision automatique :
  - se coucher
  - suivre
  - relancer

---

### `Humain`
- Interaction via input()
- Affichage graphique des cartes
- Choix manuel des actions

---

### `Moteur`
- Gère :
  - Distribution
  - Flop / Turn / River
  - Évaluation finale

---

### `MoteurInteractif`
- Ajoute :
  - Tour de mise
  - Gestion du pot
  - Gestion des bots
  - Partie complète

