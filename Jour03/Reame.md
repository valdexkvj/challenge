
# Calculatrice Scientifique Responsive avec Tkinter

Ce projet est une calculatrice scientifique complète réalisée en Python avec l'interface graphique Tkinter. Elle intègre un historique de navigation, un moteur de calcul sécurisé et une syntaxe flexible (exemple : √9 fonctionne sans parenthèses).
 Fonctionnalités Clés

    Interface Responsive : S'adapte à la taille de la fenêtre grâce au gestionnaire de géométrie .grid().
    Sécurité (AST) : N'utilise pas eval() de manière brute. Le code utilise le module ast pour analyser et calculer l'expression en toute sécurité.
    Expérience Utilisateur (UX) :
        Supporte l'écriture simplifiée (ex: sin30, √9 sont convertis automatiquement en sin(30), sqrt(9)).
        Historique navigable avec les flèches (⬆️ / ⬇️).
    Opérations Scientifiques : Trigonométrie, Logarithmes, Factorielle, Puissances, etc.

🛠️ Prérequis

Aucune installation externe n'est nécessaire. Le projet utilise uniquement les bibliothèques standard de Python :

    tkinter : Pour l'interface graphique.
    math : Pour les fonctions mathématiques.
    ast : Pour l'analyse syntaxique sécurisée.
    operator : Pour effectuer les calculs (+, -, *, /).
    re : (Regex) Pour la manipulation intelligente des chaînes de caractères.

📂 Structure du Code
1. Les Importations

Python

import tkinter as tk
import math
import ast
import operator
import re  # Indispensable pour la reconnaissance de motifs (ex: √9)

2. Le Moteur de Calcul Sécurisé (safe_eval)

Au lieu d'exécuter n'importe quel code Python avec eval(), nous analysons la chaîne de caractères comme un arbre syntaxique.

    Pourquoi ? Pour empêcher un utilisateur malveillant d'exécuter des commandes système via la calculatrice.
    Comment ? La fonction safe_eval parcourt les nœuds (nombres, opérateurs, appels de fonction) et ne calcule que si c'est autorisé dans les dictionnaires OPERATORS et FUNCTIONS.

Python

def safe_eval(expr):
    # Analyse l'expression et vérifie chaque nœud
    # ...

3. La "Magie" des Regex (Expression Régulière)

C'est cette partie qui permet à l'utilisateur de taper √9 au lieu de sqrt(9).

    Problème : Python ne comprend pas sqrt9. Il veut sqrt(9).
    Solution : On utilise une regex pour trouver le motif "Mot + Chiffre" et on insère des parenthèses.

Python

# Cherche une fonction suivie d'un nombre
pattern = r'(sqrt|sin|cos|tan|log|ln|asin|acos|atan|exp)(\d+(\.\d+)?)'
# Remplace par Fonction(Nombre)
expression = re.sub(pattern, r'\1(\2)', expression)

4. Le Système de Navigation (nav)

Cette fonction gère l'historique stocké dans la liste history = [].

    ⬆️ (Haut) : Remonte dans le passé (incrémente l'index vers l'arrière).
    ⬇️ (Bas) : Redescend vers les calculs récents.
    Gestion intelligente : Si l'utilisateur modifie un ancien calcul, le mode "historique" se désactive automatiquement pour permettre une nouvelle saisie.

5. L'Interface Graphique (Grid Layout)

L'interface est rendue responsive grâce à la configuration des poids (weight) des lignes et des colonnes.
