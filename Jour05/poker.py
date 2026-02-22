import random as rd
from collections import Counter
import time
import os


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def cadre(texte: str, largeur=64, couleur="37"):
    """Affiche un cadre ASCII de couleur ANSI et texte centré."""
    lignes = texte.strip().split("\n")
    print(f"\033[{couleur}m╔" + "═" * (largeur - 2) + "╗\033[0m")
    for ligne in lignes:
        print(f"\033[{couleur}m║ {ligne.center(largeur - 4)} ║\033[0m")
    print(f"\033[{couleur}m╚" + "═" * (largeur - 2) + "╝\033[0m")

def pause(msg="\nAppuie sur Entrée pour continuer..."):
    input(msg)

def avancer(texte, tempo=0.04):
    for ch in texte:
        print(ch, end="", flush=True)
        time.sleep(tempo)
    print()




class Carte:
    valeurs = ['2','3','4','5','6','7','8','9','10','J','Q','K','A']
    couleurs = ['♠','♣','♥','♦']
    num_val = {v: i for i, v in enumerate(valeurs, start=2)}

    def __init__(self, val, col):
        self.valeur = val
        self.couleur = col

    def __repr__(self):
        return f"{self.valeur}{self.couleur}"


class Deck:
    def __init__(self):
        self.bank = [Carte(v, c) for v in Carte.valeurs for c in Carte.couleurs]
        self.melanger()

    def melanger(self):
        rd.shuffle(self.bank)

    def tirer(self, n=1):
        pioche = self.bank[:n]
        self.bank = self.bank[n:]
        return pioche


class Main:
    def __init__(self, cartes=None):
        self.cartes = cartes or []

    def add(self, cartes):
        self.cartes.extend(cartes)

    def eval(self):
        num = sorted([Carte.num_val[c.valeur] for c in self.cartes])
        unique = Counter(num)
        coul = [c.couleur for c in self.cartes]
        couleur = len(set(coul)) == 1
        suite = len(unique) == 5 and max(num) - min(num) == 4

        if couleur and suite: return (9, max(num))
        if 4 in unique.values(): return (8, max(k for k,v in unique.items() if v==4))
        if sorted(unique.values()) == [2,3]: return (7, max(k for k,v in unique.items() if v==3))
        if couleur: return (6, max(num))
        if suite: return (5, max(num))
        if 3 in unique.values(): return (4, max(k for k,v in unique.items() if v==3))
        if list(unique.values()).count(2) == 2: return (3, max(k for k,v in unique.items() if v==2))
        if 2 in unique.values(): return (2, max(k for k,v in unique.items() if v==2))
        return (1, max(num))


class Joueur:
    def __init__(self, nom, jeton=1000):
        self.nom = nom
        self.jeton = jeton
        self.main = Main()

    def recevoir(self, cartes):
        self.main.add(cartes)

    def __repr__(self):
        return f"{self.nom} ({self.jeton} jetons): {self.main.cartes}"


class Bot(Joueur):
    def décider(self, mise_courante):
        choix = rd.choices(["se_coucher", "suivre", "relancer"], weights=[1,5,1])[0]
        if choix == "relancer":
            montant = rd.randint(10, 100)
            print(f"\033[33m{self.nom}\033[0m relance de {montant} jetons !")
            return ("relancer", montant)
        elif choix == "suivre":
            print(f"\033[33m{self.nom}\033[0m suit la mise.")
            return ("suivre", mise_courante)
        else:
            print(f"\033[33m{self.nom}\033[0m se couche.")
            return ("se_coucher", 0)




class Moteur:
    def __init__(self, noms_joueurs):
        self.deck = Deck()
        self.joueurs = [Joueur(n) for n in noms_joueurs]
        self.table = []

    def distribuer_initial(self):
        for j in self.joueurs:
            j.recevoir(self.deck.tirer(2))

    def flop_turn_river(self):
        self.deck.tirer(1)
        self.table.extend(self.deck.tirer(3))
        self.deck.tirer(1)
        self.table.extend(self.deck.tirer(1))
        self.deck.tirer(1)
        self.table.extend(self.deck.tirer(1))

    def afficher_table(self):
        n = len(self.table)
        print(" ┌──────┐" * n)
        for c in self.table: print(f" │{c.valeur:<2}    │", end="")
        print()
        for c in self.table: print(f" │  {c.couleur}   │", end="")
        print()
        for c in self.table: print(f" │    {c.valeur:<2}│", end="")
        print()
        print(" └──────┘" * n)

    def evaluer_partie(self):
        print("\nRésultats :")
        combinaisons = []
        for j in self.joueurs:
            combinaison = j.main.cartes + self.table
            meilleure = Main(combinaison).eval()
            combinaisons.append((meilleure, j))
        gagnant = max(combinaisons, key=lambda x: x[0])
        cadre(f" {gagnant[1].nom} gagne avec {gagnant[0]}", couleur="33")


class Humain(Joueur):
    def dessin(self):
        n = len(self.main.cartes)
        print("\n" + " " * 6 + "┌──────┐ " * n)
        print(" " * 6 + "".join(f"│{c.valeur:<2}    │ " for c in self.main.cartes))
        print(" " * 6 + "".join(f"│  {c.couleur}   │ " for c in self.main.cartes))
        print(" " * 6 + "".join(f"│    {c.valeur:<2}│ " for c in self.main.cartes))
        print(" " * 6 + "└──────┘ " * n)

    def décider(self, mise_courante):
        print(f"\nTes cartes : {' '.join(str(c) for c in self.main.cartes)}")
        self.dessin()
        print(f"\nMise actuelle : {mise_courante} jetons.")
        print("Actions : (1) suivre, (2) relancer, (3) se coucher")
        choix = input(" Que veux‑tu faire ? ").strip()
        if choix == '2':
            montant = int(input("Montant de ta relance : "))
            return ("relancer", montant)
        elif choix == '3':
            return ("se_coucher", 0)
        else:
            return ("suivre", mise_courante)


class MoteurInteractif(Moteur):
    def __init__(self, noms_joueurs):
        super().__init__(noms_joueurs)
        self.joueurs = [Humain(noms_joueurs[0])] + [Bot(n) for n in noms_joueurs[1:]]
        self.pot = 0
        self.mise_courante = 0

    def tour_de_mise(self):
        print("\n\033[36m─── Nouveau tour de mise ───\033[0m")
        for joueur in self.joueurs.copy():
            action, montant = joueur.décider(self.mise_courante)
            if action == "se_coucher":
                self.joueurs.remove(joueur)
                print(f"{joueur.nom} quitte le tour.")
            elif action == "relancer":
                self.mise_courante = montant
                self.pot += montant
            elif action == "suivre":
                self.pot += self.mise_courante
        print(f"\033[33mPot total :\033[31m {self.pot} jetons\033[0m\n")

    def jouer_partie(self):
        clear()
        cadre("=== Nouvelle Partie de Texas Hold'em ===", couleur="33")
        self.distribuer_initial()
        self.tour_de_mise()
        print("\n--- Flop / Turn / River ---")
        self.flop_turn_river()
        self.afficher_table()
        self.tour_de_mise()
        self.evaluer_partie()




def afficher_titre():
    clear()
    cadre("♠️  JEU DE POKER ♣️  -/ KVJ", couleur="33")
    for ligne in [
        "          ♠ ┌──────┐   ♥ ┌──────┐   ♦ ┌──────┐",
        "            │A     │     │K     │     │Q     │",
        "            │  ♠   │     │  ♥   │     │  ♦   │",
        "            │    A │     │    K │     │    Q │",
        "          ♣ └──────┘   ♠ └──────┘   ♥ └──────┘"]:
        avancer(ligne, tempo=0.01)
    print()


def menu_principal():
    joueur_nom = None
    while True:
        cadre("MENU PRINCIPAL", couleur="36")
        print("""
        (1) * Entrer ton nom de joueur
        (2) *  Suivant (nom par défaut)
        (3) * Quitter le jeu
        """)
        choix = input("➡️  Ton choix : ").strip()
        if choix == '1':
            joueur_nom = input("\nEntre ton nom : ").strip() or "Toi"
            cadre(f"Bienvenue, {joueur_nom} !", couleur="32")
        elif choix == '2':
            if not joueur_nom: joueur_nom = "Toi"
            break
        elif choix == '3':
            cadre(" À la prochaine !", couleur="31")
            exit()
        else:
            cadre(" Choix invalide, réessaie.", couleur="31")
    return joueur_nom


def demander_nb_bots():
    while True:
        try:
            cadre("Sélection du nombre d'adversaires", couleur="36")
            n = int(input("Combien d'adversaires veux‑tu affronter (1‑5) ? : "))
            if 1 <= n <= 5:
                cadre(f"Tu affronteras {n} adversaire(s) ", couleur="32")
                return n
            else:
                cadre(" Choisis un nombre entre 1 et 5.", couleur="31")
        except ValueError:
            cadre(" Entrée non valide. Tape un nombre.", couleur="31")



if __name__ == "__main__":
    afficher_titre()
    nom_joueur = menu_principal()
    nb_bots = demander_nb_bots()
    noms = [nom_joueur] + [f"Bot{i+1}" for i in range(nb_bots)]
    jeu = MoteurInteractif(noms)
    jeu.jouer_partie()
    cadre("Merci d’avoir joué ! ", couleur="33")
    pause()
