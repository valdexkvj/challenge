import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import os, glob

# 
path = "/home/valdex/Documents/chalenge/jour04"
csv_files = glob.glob(os.path.join(path, "*.csv"))
print("Fichiers trouvés :", csv_files)
dataframes = {}

for file in csv_files:
    name = os.path.basename(file).replace(".csv", "")
    df = pd.read_csv(file)
    dataframes[name] = df
    print(f"{name:30s} : {df.shape[0]} lignes - {df.shape[1]} colonnes")

# nettoyage des colonnes et valeurs manquantes 
for name, df in dataframes.items():
    # uniformiser les noms de colonnes
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    
    # remplacer les valeurs manquantes par la médiane
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].apply(lambda x: x.fillna(x.median()))
    
    dataframes[name] = df
    print(f"{name} nettoyé (valeurs manquantes traitées)")

# Suppression des outliers par la méthode IQR 
for name, df in dataframes.items():
    num_cols = df.select_dtypes(include=[np.number]).columns
    for col in num_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        low, high = Q1 - 1.5 * IQR, Q3 + 1.5 * IQR
        df = df[(df[col] >= low) & (df[col] <= high)]
    dataframes[name] = df
    print(f"{name} : outliers supprimés")

# Création de variables dérivées ===
for name, df in dataframes.items():
    num_cols = df.select_dtypes(include=[np.number]).columns
    if len(num_cols) > 0:
        df["mean_all_numeric"] = df[num_cols].mean(axis=1)
        df["std_all_numeric"] = df[num_cols].std(axis=1)
    dataframes[name] = df
    print(f"{name} : nouvelles variables dérivées ajoutées")

# Fusion des jeux de données corrigée 
if dataframes:
    try:
        combined = pd.concat(dataframes.values(), ignore_index=True, join="outer")
    except ValueError:
        raise ValueError("Aucun dataframe ou colonnes à concaténer. Vérifie tes fichiers CSV.")
else:
    raise ValueError("Aucun fichier CSV n'a été chargé.")

# Export des fichiers nettoyés 
os.makedirs("cleaned_output", exist_ok=True)

for name, df in dataframes.items():
    df.to_csv(f"cleaned_output/{name}_clean.csv", index=False)
    if df.shape[0] < 500000:   # limite arbitraire
        df.to_excel(f"cleaned_output/{name}_clean.xlsx", index=False)
        print(f"{name} exporté en CSV et Excel")
    else:
        print(f"{name} exporté uniquement en CSV (trop volumineux pour Excel)")
# Visualisations 
sns.set(style="whitegrid")

# distribution d'une variable appelée price (si elle existe)
if "price" in combined.columns:
    plt.figure(figsize=(6, 4))
    sns.histplot(combined["price"], kde=True)
    plt.title("Distribution des prix - Produits combinés")
    plt.tight_layout()
    plt.savefig("cleaned_output/distribution_prix.png")
    plt.close()

# boxplot de toutes les variables numériques
num_cols = combined.select_dtypes(include=[np.number]).columns
if len(num_cols) > 0:
    plt.figure(figsize=(8, 4))
    sns.boxplot(data=combined[num_cols])
    plt.title("Boxplot des variables numériques (tous jeux combinés)")
    plt.tight_layout()
    plt.savefig("cleaned_output/numeric_boxplot.png")
    plt.close()

# Rapport statistique global
summary = combined.describe(include="all").T
summary.to_csv("cleaned_output/summary_stats.csv", index=True)
print("Rapport statistique sauvegardé.")
