from datetime import datetime
import json
import hashlib


# FONCTION HASH
def hash_mot_de_passe(mot_de_passe):
    return hashlib.sha256(mot_de_passe.encode()).hexdigest()


# UTILISATEUR
class Utilisateur:
    utilisateurs = []

    # CONSTRUCTEUR
    def __init__(self, nom, mot_passe, role):
        self.nom = nom
        self.mot_passe = hash_mot_de_passe(mot_passe)
        self.role = role
        Utilisateur.utilisateurs.append(self)

    # LOGIN
    @staticmethod
    def login(nom, mot_passe):
        mot_de_passe_hash = hash_mot_de_passe(mot_passe)

        for user in Utilisateur.utilisateurs:
            if user.nom == nom and user.mot_passe == mot_de_passe_hash:
                print(f"Connexion reussie : {user.nom} ({user.role})")
                return user

        print("Identifiants incorrects")
        return None

    # VERIFIER PERMISSION
    def verifier_permission(self, permission):
        permissions = {
            "superadmin": ["creer_admin", "creer_compte", "depot"],
            "admin": ["creer_compte", "depot"]
        }

        if permission in permissions.get(self.role, []):
            return True
        else:
            print("Permission refusee")
            return False
        
    # SAUVEGARDE UTILISATEURS
    @staticmethod
    def sauvegarder_utilisateurs():
        data = []

        for user in Utilisateur.utilisateurs:
            data.append({
                "nom": user.nom,
                "mot_passe": user.mot_passe,
                "role": user.role
            })

        with open("utilisateurs.json", "w") as f:
            json.dump(data, f, indent=4)

        print("Utilisateurs sauvegardes")

    # CHARGER UTILISATEURS
    @staticmethod
    def charger_utilisateurs():
        try:
            with open("utilisateurs.json", "r") as f:
                data = json.load(f)

                Utilisateur.utilisateurs = []

                for user_data in data:
                    if user_data["role"] == "superadmin":
                        user = SuperAdmin.__new__(SuperAdmin)
                    else:
                        user = Admin.__new__(Admin)

                    user.nom = user_data["nom"]
                    user.mot_passe = user_data["mot_passe"]
                    user.role = user_data["role"]

                    Utilisateur.utilisateurs.append(user)

            print("Utilisateurs charges")

        except FileNotFoundError:
            print("Aucun utilisateur sauvegarde")


class Compte:
    nb = 0
    listes = []

    def __init__(self, nom, mot_passe):
        Compte.nb += 1
        self.id = Compte.nb
        self.nom = nom
        self.mot_passe = mot_passe
        self.solde = 0
        self.historique_operations = []

        Compte.listes.append({
            "id": self.id,
            "nom": self.nom
        })

    
    # MOT DE PASSE
    
    def changer_mot_passe(self, ancien, nouveau):
        if self.mot_passe == ancien:
            self.mot_passe = nouveau
            print("Mot de passe changé avec succès.")
        else:
            print("Ancien mot de passe incorrect.")

    
    # HISTORIQUE
    
    def historique(self, type_operation, montant, destinataire=None):
        transaction = {
            "type": type_operation,
            "date": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
            "montant": montant,
            "destinataire": destinataire
        }
        self.historique_operations.append(transaction)

    # DEPOT
    
    def depot(self, montant):
        if montant > 0:
            self.solde += montant
            print(f"Votre solde est de {self.solde}")
            self.historique("depot", montant)
        else:
            print("Le montant doit être supérieur à 0")

    # RETRAIT
    
    def retrait(self, montant):
        if montant > 0:
            if self.solde >= montant:
                self.solde -= montant
                print(f"Retrait de {montant} effectué. Solde restant : {self.solde}")
                self.historique("retrait", montant)
            else:
                print("Solde insuffisant")
        else:
            print("Le montant doit être supérieur à 0")

    
    # VIREMENT
    
    def virement(self, compte_destinataire, montant):
        if montant > 0:
            if self.solde >= montant:
                self.solde -= montant
                compte_destinataire.solde += montant

                print(f"Virement de {montant} vers {compte_destinataire.nom}")
                print(f"Solde restant : {self.solde}")

                self.historique("virement", montant, compte_destinataire.nom)
                compte_destinataire.historique("reception virement", montant, self.nom)
            else:
                print("Solde insuffisant")
        else:
            print("Le montant doit être supérieur à 0")

    # SAUVEGARDE COMPTE INDIVIDUEL
    
    def sauvegarder_compte(self):
        data = {
            "id": self.id,
            "nom": self.nom,
            "mot_passe": self.mot_passe,
            "solde": self.solde,
            "historique_operations": self.historique_operations,
            "type": self.__class__.__name__
        }

        with open(f"compte_{self.id}.json", "w") as f:
            json.dump(data, f, indent=4)

        print("Compte sauvegardé.")

    
    # CHARGER COMPTE INDIVIDUEL
    @classmethod
    def charger_compte(cls, id_compte):
        try:
            with open(f"compte_{id_compte}.json", "r") as f:
                data = json.load(f)

                if data["type"] == "CompteEpargne":
                    obj = CompteEpargne(data["nom"], data["mot_passe"], 0.02)
                elif data["type"] == "ComptePro":
                    obj = ComptePro(data["nom"], data["mot_passe"])
                else:
                    obj = cls(data["nom"], data["mot_passe"])

                obj.id = data["id"]
                obj.solde = data["solde"]
                obj.historique_operations = data["historique_operations"]

                return obj

        except FileNotFoundError:
            print("Aucun compte trouvé.")
            return None

    # SAUVEGARDE LISTE COMPTES
    
    @staticmethod
    def sauvegarder():
        with open("comptes.json", "w") as f:
            json.dump(Compte.listes, f, indent=4)

    # CHARGER LISTE COMPTES
    
    @staticmethod
    def charger():
        try:
            with open("comptes.json", "r") as f:
                Compte.listes = json.load(f)
        except FileNotFoundError:
            print("Aucun compte existant.")


# COMPTE EPARGNE

class CompteEpargne(Compte):
    def __init__(self, nom, mot_passe, taux_interet):
        super().__init__(nom, mot_passe)
        self.taux_interet = taux_interet

    def calculer_interets(self):
        interets = self.solde * self.taux_interet
        self.solde += interets
        print(f"Intérêts ajoutés : {interets}")
        self.historique("calcul interets", interets)


# COMPTE PRO
class ComptePro(Compte):
    frais_bancaire = 0.01
    def __init__(self, nom, mot_passe):
        super().__init__(nom, mot_passe)
        self.frais_bancaire = 0.01
    def virement(self, compte_destinataire, montant):
        frais = montant * self.frais_bancaire
        if self.solde >= montant + frais:
            self.solde -= (montant + frais)
            compte_destinataire.solde += montant
            print(f"Virement de {montant} vers {compte_destinataire.nom} vous a coute {frais}")
            print(f"Solde restant : {self.solde}")
            self.historique("virement", montant, compte_destinataire.nom)
            compte_destinataire.historique("reception virement", montant, self.nom)
        else:
            print("Solde insuffisant")

    def appliquer_frais(self, frais):
        if self.solde >= frais:
            self.solde -= frais
            print(f"Frais de {frais} appliqués.")
            self.historique("frais bancaire", frais)
        else:
            print("Solde insuffisant pour appliquer les frais.")

# ADMIN
class Admin(Utilisateur):

    # CONSTRUCTEUR
    def __init__(self, nom, mot_passe):
        super().__init__(nom, mot_passe, "admin")

    # CREER COMPTE
    def creer_compte(self, nom, mot_passe):
        if self.verifier_permission("creer_compte"):
            compte = Compte(nom, mot_passe)
            print(f"Compte cree pour {nom}")
            return compte


# SUPERADMIN
class SuperAdmin(Utilisateur):

    # CONSTRUCTEUR
    def __init__(self, nom, mot_passe):
        super().__init__(nom, mot_passe, "superadmin")

    # CREER ADMIN
    def creer_admin(self, nom, mot_passe):
        if self.verifier_permission("creer_admin"):
            admin = Admin(nom, mot_passe)
            print(f"Admin {nom} cree")
            return admin

    # CREER COMPTE
    def creer_compte(self, nom, mot_passe):
        if self.verifier_permission("creer_compte"):
            compte = Compte(nom, mot_passe)
            print(f"Compte cree pour {nom}")
            return compte



