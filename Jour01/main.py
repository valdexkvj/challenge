from class_system import Utilisateur, Admin, SuperAdmin, Compte, CompteEpargne, ComptePro

# CHARGEMENT DES DONNEES EXISTANTES
Utilisateur.charger_utilisateurs()
Compte.charger()

# FONCTION POUR AFFICHER MENU SELON ROLE
def afficher_menu(user):
    print("\n--- MENU ---")
    if user.role == "superadmin":
        print("1 - Creer Admin")
        print("2 - Creer Compte Client")
        print("3 - Depot sur Compte Client")
        print("0 - Deconnexion")
    elif user.role == "admin":
        print("1 - Creer Compte Client")
        print("2 - Depot sur Compte Client")
        print("0 - Deconnexion")
    else:  # client
        print("1 - Retrait")
        print("2 - Virement")
        print("3 - Historique")
        print("0 - Deconnexion")

# FONCTION LOGIN OU CREATION COMPTE
def connexion():
    print("1 - Connexion")
    print("2 - Creer un compte client")
    choix = input("Choisir une option: ")
    
    if choix == "1":
        nom = input("Nom: ")
        mot_passe = input("Mot de passe: ")
        user = Utilisateur.login(nom, mot_passe)
        return user
    elif choix == "2":
        nom = input("Nom: ")
        mot_passe = input("Mot de passe: ")
        compte = Compte(nom, mot_passe)
        print(f"Compte client cree: {nom}")
        compte.sauvegarder_compte()
        Compte.sauvegarder()
        return None
    else:
        print("Option invalide")
        return None

# BOUCLE PRINCIPALE
def main():
    while True:
        user = connexion()
        if not user:
            continue

        while True:
            afficher_menu(user)
            action = input("Choisir une action: ")

            # ACTIONS SUPERADMIN
            if user.role == "superadmin":
                if action == "1":  # creer admin
                    nom = input("Nom du nouvel admin: ")
                    mot_passe = input("Mot de passe: ")
                    admin = user.creer_admin(nom, mot_passe)
                    Utilisateur.sauvegarder_utilisateurs()
                elif action == "2":  # creer compte client
                    nom = input("Nom du client: ")
                    mot_passe = input("Mot de passe client: ")
                    compte = user.creer_compte(nom, mot_passe)
                    compte.sauvegarder_compte()
                    Compte.sauvegarder()
                elif action == "3":  # depot sur compte
                    id_compte = int(input("ID du compte: "))
                    compte = Compte.charger_compte(id_compte)
                    if compte:
                        montant = float(input("Montant depot: "))
                        user.verifier_permission("depot") and compte.depot(montant)
                        compte.sauvegarder_compte()
                elif action == "0":
                    break

            # ACTIONS ADMIN
            elif user.role == "admin":
                if action == "1":  # creer compte client
                    nom = input("Nom du client: ")
                    mot_passe = input("Mot de passe client: ")
                    compte = user.creer_compte(nom, mot_passe)
                    compte.sauvegarder_compte()
                    Compte.sauvegarder()
                elif action == "2":  # depot sur compte
                    id_compte = int(input("ID du compte: "))
                    compte = Compte.charger_compte(id_compte)
                    if compte:
                        montant = float(input("Montant depot: "))
                        user.verifier_permission("depot") and compte.depot(montant)
                        compte.sauvegarder_compte()
                elif action == "0":
                    break

            # ACTIONS CLIENT
            else:
                compte = user  # pour clarté
                if action == "1":  # retrait
                    montant = float(input("Montant retrait: "))
                    compte.retrait(montant)
                    compte.sauvegarder_compte()
                elif action == "2":  # virement
                    id_dest = int(input("ID du destinataire: "))
                    compte_dest = Compte.charger_compte(id_dest)
                    if compte_dest:
                        montant = float(input("Montant virement: "))
                        compte.virement(compte_dest, montant)
                        compte.sauvegarder_compte()
                        compte_dest.sauvegarder_compte()
                elif action == "3":  # historique
                    for op in compte.historique_operations:
                        print(op)
                elif action == "0":
                    break

# EXECUTION DU PROGRAMME
if __name__ == "__main__":
    main()
