import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.animation import FuncAnimation


#  CHARGEMENT DES DONNÉES
print(" Chargement du fichier iris.csv...")

try:
    df = pd.read_csv('iris.csv')
    print("Fichier chargé avec succès !\n")
except FileNotFoundError:
    print(" ERREUR : Le fichier 'iris.csv' est introuvable !")
    print(" Assure-toi qu'il est dans le même dossier que le code Python.")
    exit()


# 2. DÉTECTION AUTOMATIQUE DES COLONNES

print(" |-----------DÉTECTION DES COLONNES-----------|")
print()

print("Colonnes détectées :", df.columns.tolist())
print()

# Fonction pour trouver les colonnes (peu importe leur nom exact)
def trouver_colonne(df, mots_cles):
    #Trouve une colonne dont le nom contient un des mots-clés (insensible à la casse)
    for col in df.columns:
        for mot in mots_cles:
            if mot.lower() in col.lower():
                return col
    return None

# Recherche des colonnes
col_sepal_length = trouver_colonne(df, ['sepal', 'length', 'sepallength'])
col_sepal_width = trouver_colonne(df, ['sepal', 'width', 'sepalwidth'])
col_petal_length = trouver_colonne(df, ['petal', 'length', 'petallength'])
col_petal_width = trouver_colonne(df, ['petal', 'width', 'petalwidth'])
col_species = trouver_colonne(df, ['species', 'variety', 'class'])

# Vérification
colonnes_trouvees = {
    'Sepal Length': col_sepal_length,
    'Sepal Width': col_sepal_width,
    'Petal Length': col_petal_length,
    'Petal Width': col_petal_width,
    'Species': col_species
}

print("Colonnes utilisées :")
for nom, col in colonnes_trouvees.items():
    if col:
        print(f"   {nom:15} → '{col}'")
    else:
        print(f"   {nom:15} → NON TROUVÉE")

if None in colonnes_trouvees.values():
    print("\n ERREUR : Certaines colonnes sont manquantes !")
    print(" Affichage des premières lignes pour t'aider :")
    print(df.head())
    exit()

# Créer une liste pratique des colonnes numériques
colonnes_num = [col_sepal_length, col_sepal_width, col_petal_length, col_petal_width]


#  APERÇU DES DONNÉES

print("\n" + "=" * 60)
print(" APERÇU DU DATASET IRIS")
print("=" * 60)
print(df.head(10))
print(f"\n Dimensions : {df.shape[0]} lignes × {df.shape[1]} colonnes")
print(f" Espèces : {df[col_species].unique()}")


#  STATISTIQUES DESCRIPTIVES

print("\n" + "=" * 60)
print(" STATISTIQUES DESCRIPTIVES")
print("=" * 60)

for col in colonnes_num:
    print(f"\n--- {col} ---")
    print(f"  Moyenne    : {df[col].mean():.4f}")
    print(f"  Médiane    : {df[col].median():.4f}")
    print(f"  Écart-type : {df[col].std():.4f}")
    print(f"  Q1 (25%)   : {df[col].quantile(0.25):.4f}")
    print(f"  Q2 (50%)   : {df[col].quantile(0.50):.4f}")
    print(f"  Q3 (75%)   : {df[col].quantile(0.75):.4f}")

# Tableau récapitulatif
print()
print(" TABLEAU RÉCAPITULATIF")
print()
print(df[colonnes_num].describe().round(4))

#  CRÉATION DE LA PALETTE DE COULEURS

especes_uniques = df[col_species].unique()
couleurs_base = ['#FF6B6B', '#4ECDC4', '#45B7D1']
palette = {espece: couleurs_base[i] for i, espece in enumerate(especes_uniques)}

print("\n Palette de couleurs :")
for espece, couleur in palette.items():
    print(f"  {espece:20} → {couleur}")

#  CRÉATION DU TABLEAU DE BORD (subplot 2x2)

sns.set_style("whitegrid")
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

fig.suptitle(' TABLEAU DE BORD IRIS - Visualisation Multi-Graphiques',
             fontsize=18, fontweight='bold', y=0.98, color='#2C3E50')

# GRAPHIQUE 1 : HISTOGRAMME

ax1 = axes[0, 0]

for species in especes_uniques:
    subset = df[df[col_species] == species]
    ax1.hist(subset[col_petal_length],
             bins=15, alpha=0.6, label=species,
             color=palette[species],
             edgecolor='white', linewidth=0.8)

for species in especes_uniques:
    moy = df[df[col_species] == species][col_petal_length].mean()
    ax1.axvline(moy, color=palette[species], linestyle='--', linewidth=1.5)

ax1.set_title(' Distribution de la Longueur des Pétales', 
              fontsize=12, fontweight='bold')
ax1.set_xlabel('Longueur du Pétale (cm)', fontsize=10)
ax1.set_ylabel('Fréquence', fontsize=10)
ax1.legend(title='Espèce', fontsize=8)


# GRAPHIQUE 2 : SCATTER PLOT + RÉGRESSION

ax2 = axes[0, 1]

for species in especes_uniques:
    subset = df[df[col_species] == species]
    ax2.scatter(subset[col_petal_length], subset[col_petal_width],
                c=palette[species], label=species,
                alpha=0.7, edgecolors='white', s=60)
    
    x = subset[col_petal_length].values
    y = subset[col_petal_width].values
    coeffs = np.polyfit(x, y, 1)
    ligne_x = np.linspace(x.min(), x.max(), 100)
    ligne_y = np.polyval(coeffs, ligne_x)
    ax2.plot(ligne_x, ligne_y, color=palette[species], linewidth=2)

corr = df[col_petal_length].corr(df[col_petal_width])
ax2.annotate(f'Corrélation : r = {corr:.3f}',
             xy=(0.05, 0.95), xycoords='axes fraction',
             fontsize=9, fontweight='bold',
             bbox=dict(boxstyle='round,pad=0.4', facecolor='lightyellow',
                       edgecolor='orange', alpha=0.9))

ax2.set_title(' Scatter Plot avec Régression Linéaire', 
              fontsize=12, fontweight='bold')
ax2.set_xlabel('Longueur du Pétale (cm)', fontsize=10)
ax2.set_ylabel('Largeur du Pétale (cm)', fontsize=10)
ax2.legend(title='Espèce', fontsize=8)


# GRAPHIQUE 3 : HEATMAP DE CORRELATION

ax3 = axes[1, 0]

matrice_corr = df[colonnes_num].corr()

sns.heatmap(matrice_corr, annot=True, fmt='.3f',
            cmap='RdYlBu_r', center=0, square=True,
            linewidths=2, linecolor='white', ax=ax3,
            cbar_kws={'shrink': 0.8, 'label': 'Coefficient'},
            vmin=-1, vmax=1,
            annot_kws={'size': 10, 'fontweight': 'bold'})

labels_courts = ['Sép. L', 'Sép. W', 'Pét. L', 'Pét. W']
ax3.set_xticklabels(labels_courts, rotation=45, ha='right', fontsize=9)
ax3.set_yticklabels(labels_courts, rotation=0, fontsize=9)
ax3.set_title(' Heatmap de Corrélation', fontsize=12, fontweight='bold')


# GRAPHIQUE 4 : COURBE

ax4 = axes[1, 1]

couleurs_courbes = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
for i, col in enumerate(colonnes_num):
    moyennes_mobiles = df[col].rolling(window=10).mean()
    ax4.plot(range(len(moyennes_mobiles)), moyennes_mobiles,
             label=col.split('Cm')[0] if 'Cm' in col else col,
             color=couleurs_courbes[i], linewidth=2, alpha=0.8)

# Séparateur
n = len(df)
if n >= 100:
    ax4.axvline(x=n//3, color='gray', linestyle=':', alpha=0.7)
    ax4.axvline(x=2*n//3, color='gray', linestyle=':', alpha=0.7)

ax4.set_title(' Évolution des Mesures (Moyenne Mobile)', 
              fontsize=12, fontweight='bold')
ax4.set_xlabel('Échantillon', fontsize=10)
ax4.set_ylabel('Valeur (cm)', fontsize=10)
ax4.legend(title='Variable', fontsize=7, loc='best')


# 7. SAUVEGARDE ET AFFICHAGE

plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig('dashboard_iris.png', dpi=300, bbox_inches='tight')
print("\n Dashboard sauvegardé : dashboard_iris.png")
plt.show()

# 8. ANIMATION (OPTIONNELLE)
print("\n Lancement de l'animation (ferme la fenêtre du dashboard d'abord)...")

fig_anim, ax_anim = plt.subplots(figsize=(12, 6))
ax_anim.set_xlim(0, len(df))
ax_anim.set_ylim(0, df[colonnes_num].max().max() + 1)
ax_anim.set_title('🎬 Animation : Construction Progressive des Courbes Iris',
                   fontsize=14, fontweight='bold')
ax_anim.set_xlabel('Échantillon', fontsize=11)
ax_anim.set_ylabel('Valeur (cm)', fontsize=11)

lignes = []
for i, col in enumerate(colonnes_num):
    ligne, = ax_anim.plot([], [], label=col.split('Cm')[0] if 'Cm' in col else col,
                          color=couleurs_courbes[i], linewidth=2)
    lignes.append(ligne)

ax_anim.legend(title='Variable', fontsize=9, loc='upper left')

def init():
    for ligne in lignes:
        ligne.set_data([], [])
    return lignes

def animer(frame):
    for i, col in enumerate(colonnes_num):
        x_data = list(range(frame + 1))
        y_data = df[col].iloc[:frame + 1].tolist()
        lignes[i].set_data(x_data, y_data)
    return lignes

animation = FuncAnimation(fig_anim, animer, init_func=init,
                          frames=len(df), interval=30,
                          blit=True, repeat=True)

plt.tight_layout()
plt.show()

