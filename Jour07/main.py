import os
import sys
import time
import random
import sqlite3
import requests
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from dataclasses import dataclass

try:
    import matplotlib.pyplot as plt
    from matplotlib.dates import DateFormatter
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("⚠ matplotlib non installé - graphiques désactivés")


# CONSTANTES GLOBALES

API_BASE_URL = "https://api.exchangerate.host"
CACHE_TTL = 600  # 10 minutes en secondes
MAX_RETRIES = 3
BASE_DELAY = 1
TIMEOUT = 10
DB_PATH = "currency_cache.db"

# DATACLASSES

@dataclass
class ConversionResult:
    """Résultat d'une conversion de devises"""
    from_currency: str
    to_currency: str
    amount: float
    converted_amount: float
    rate: float
    timestamp: datetime

 
# GESTIONNAIRE DE BASE DE DONNÉES


class DatabaseManager:
    """
    Gestionnaire de base de données SQLite pour le cache des taux de change.
    
    Fonctionnalités:
    - Stockage persistant des taux avec timestamp
    - Gestion du TTL (Time To Live)
    - Historique des conversions
    - Thread-safe avec connexions locales
    """
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._local = threading.local()
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """Obtient une connexion thread-safe"""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(self.db_path)
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection
    
    def init_database(self):
        """Initialise le schéma de la base de données"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table pour les taux actuels
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exchange_rates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                base_currency TEXT NOT NULL,
                target_currency TEXT NOT NULL,
                rate REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(base_currency, target_currency)
            )
        ''')
        
        # Table pour l'historique des taux
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rate_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                base_currency TEXT NOT NULL,
                target_currency TEXT NOT NULL,
                rate REAL NOT NULL,
                date DATE NOT NULL,
                UNIQUE(base_currency, target_currency, date)
            )
        ''')
        
        # Table pour les conversions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_currency TEXT NOT NULL,
                to_currency TEXT NOT NULL,
                amount REAL NOT NULL,
                converted_amount REAL NOT NULL,
                rate REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Index pour optimiser les requêtes
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_rates_timestamp 
            ON exchange_rates(timestamp)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_history_date 
            ON rate_history(date)
        ''')
        
        conn.commit()
        conn.close()
        print("✓ Base de données initialisée")
    
    def get_cached_rate(self, base: str, target: str) -> Optional[float]:
        """Récupère un taux en cache s'il est valide"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cutoff_time = datetime.now() - timedelta(seconds=CACHE_TTL)
        
        cursor.execute('''
            SELECT rate, timestamp FROM exchange_rates 
            WHERE base_currency = ? AND target_currency = ?
            AND timestamp > ?
        ''', (base, target, cutoff_time))
        
        result = cursor.fetchone()
        if result:
            return result['rate']
        return None
    
    def cache_rate(self, base: str, target: str, rate: float):
        """Stocke un taux dans le cache"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO exchange_rates 
            (base_currency, target_currency, rate, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (base, target, rate, datetime.now()))
        
        conn.commit()
    
    def save_conversion(self, result: ConversionResult):
        """Sauvegarde une conversion dans l'historique"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO conversions 
            (from_currency, to_currency, amount, converted_amount, rate, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (result.from_currency, result.to_currency, 
              result.amount, result.converted_amount,
              result.rate, result.timestamp))
        
        conn.commit()
    
    def get_conversion_history(self, days: int = 30) -> list:
        """Récupère l'historique des conversions"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        cursor.execute('''
            SELECT * FROM conversions 
            WHERE timestamp > ?
            ORDER BY timestamp DESC
        ''', (cutoff_date,))
        
        return cursor.fetchall()
    
    def cleanup_expired_cache(self) -> int:
        """Nettoie les entrées de cache expirées"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cutoff_time = datetime.now() - timedelta(seconds=CACHE_TTL)
        
        cursor.execute('''
            DELETE FROM exchange_rates WHERE timestamp < ?
        ''', (cutoff_time,))
        
        deleted = cursor.rowcount
        conn.commit()
        return deleted

# CLIENT API

class APIClient:
    """
    Client API avec gestion robuste des erreurs.
    
    Features:
    - Retry exponentiel avec jitter
    - Session HTTP persistante
    - Timeout configurable
    - Gestion des codes d'erreur HTTP
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CurrencyConverter/1.0',
            'Accept': 'application/json'
        })
    
    def _exponential_backoff(self, attempt: int) -> float:
        """Calcule le délai de retry avec backoff exponentiel et jitter"""
        exponential = BASE_DELAY * (2 ** attempt)
        jitter = random.uniform(0, 1)
        return min(exponential + jitter, 30)
    
    def _make_request(self, url: str, params: Dict = None) -> Optional[Dict]:
        """Effectue une requête HTTP avec retry automatique"""
        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(
                    url, 
                    params=params, 
                    timeout=TIMEOUT
                )
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.Timeout:
                print(f"⚠ Timeout (tentative {attempt + 1}/{MAX_RETRIES})")
                
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if e.response else 0
                print(f"⚠ Erreur HTTP {status_code}")
                if status_code not in [429, 500, 502, 503, 504]:
                    return None
                    
            except requests.exceptions.RequestException as e:
                print(f"⚠ Erreur réseau: {e}")
            
            if attempt < MAX_RETRIES - 1:
                delay = self._exponential_backoff(attempt)
                print(f"⟳ Retry dans {delay:.1f}s...")
                time.sleep(delay)
        
        print(f"✗ Échec après {MAX_RETRIES} tentatives")
        return None
    
    def get_exchange_rate(self, base: str, target: str) -> Optional[float]:
        """Récupère le taux de change avec cache"""
        # Vérifier le cache d'abord
        cached_rate = self.db.get_cached_rate(base, target)
        if cached_rate:
            print(f"✓ Utilisation du cache ({base} → {target})")
            return cached_rate
        
        # Appel API si nécessaire
        url = f"{API_BASE_URL}/convert"
        params = {
            'from': base,
            'to': target,
            'amount': 1
        }
        
        print(f"⟳ Récupération du taux {base} → {target}...")
        data = self._make_request(url, params)
        
        if data and 'result' in data:
            rate = float(data['result'])
            self.db.cache_rate(base, target, rate)
            print(f"✓ Taux mis en cache: {rate:.6f}")
            return rate
        
        return None
    
    def get_all_rates(self, base: str = 'EUR') -> Optional[Dict]:
        """Récupère tous les taux pour une devise de base"""
        url = f"{API_BASE_URL}/latest"
        params = {'base': base}
        
        data = self._make_request(url, params)
        if data and 'rates' in data:
            return data['rates']
        return None
    
    def get_historical_rates(self, base: str, target: str, 
                             days: int = 30) -> Optional[Dict[datetime, float]]:
        """Récupère l'historique des taux sur N jours"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        url = f"{API_BASE_URL}/timeseries"
        params = {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'base': base,
            'symbols': target
        }
        
        data = self._make_request(url, params)
        if data and 'rates' in data:
            rates = {}
            for date_str, rate_data in data['rates'].items():
                date = datetime.strptime(date_str, '%Y-%m-%d')
                if target in rate_data:
                    rates[date] = float(rate_data[target])
            return rates
        return None

# CONVERTISSEUR DE DEVISES


class CurrencyConverter:
    """Classe principale de conversion de devises"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.api = APIClient(self.db)
        self.available_currencies = self._load_currencies()
    
    def _load_currencies(self) -> list:
        """Charge la liste des devises disponibles"""
        return ['EUR', 'USD', 'GBP', 'JPY', 'CHF', 
                'CAD', 'AUD', 'CNY', 'INR', 'MXN',
                'BRL', 'RUB', 'KRW', 'SGD', 'NZD',
                'HKD', 'SEK', 'NOK', 'DKK', 'PLN']
    
    def convert(self, amount: float, from_curr: str, 
                to_curr: str) -> Optional[ConversionResult]:
        """Convertit un montant d'une devise à une autre"""
        from_curr = from_curr.upper()
        to_curr = to_curr.upper()
        
        if from_curr == to_curr:
            return ConversionResult(
                from_currency=from_curr,
                to_currency=to_curr,
                amount=amount,
                converted_amount=amount,
                rate=1.0,
                timestamp=datetime.now()
            )
        
        rate = self.api.get_exchange_rate(from_curr, to_curr)
        if rate is None:
            return None
        
        converted = amount * rate
        
        result = ConversionResult(
            from_currency=from_curr,
            to_currency=to_curr,
            amount=amount,
            converted_amount=converted,
            rate=rate,
            timestamp=datetime.now()
        )
        
        # Sauvegarder dans l'historique
        self.db.save_conversion(result)
        
        return result
    
    def display_rate_chart(self, base: str, target: str, days: int = 30):
        """Affiche un graphe de l'évolution des taux avec matplotlib"""
        if not MATPLOTLIB_AVAILABLE:
            print("✗ matplotlib n'est pas installé")
            return
        
        print(f"\n📊 Récupération de l'historique {base} → {target} ({days} jours)...")
        
        rates = self.api.get_historical_rates(base, target, days)
        if not rates:
            print("✗ Impossible de récupérer l'historique")
            return
        
        # Trier par date
        sorted_rates = sorted(rates.items())
        dates = [d for d, _ in sorted_rates]
        values = [v for _, v in sorted_rates]
        
        if len(values) == 0:
            print("✗ Pas de données disponibles")
            return
        
        # Calculer les statistiques
        min_rate = min(values)
        max_rate = max(values)
        avg_rate = sum(values) / len(values)
        
        print(f"\n📈 Statistiques sur {days} jours:")
        print(f"   Min: {min_rate:.6f}")
        print(f"   Max: {max_rate:.6f}")
        print(f"   Moy: {avg_rate:.6f}")
        print(f"   Vol: {((max_rate - min_rate) / avg_rate * 100):.2f}%")
        
        # Créer le graphe
        plt.figure(figsize=(12, 6))
        plt.plot(dates, values, 'b-', linewidth=2, label=f'{base}/{target}')
        plt.fill_between(dates, values, alpha=0.3)
        plt.axhline(y=avg_rate, color='r', linestyle='--', 
                    label=f'Moyenne: {avg_rate:.4f}')
        
        plt.title(f'Évolution du taux {base} → {target} ({days} jours)', 
                  fontsize=14, fontweight='bold')
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Taux de change', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        # Formater les dates
        plt.gca().xaxis.set_major_formatter(DateFormatter('%d/%m'))
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        plt.show()
    
    def print_ascii_chart(self, base: str, target: str, days: int = 30):
        """Affiche un graphe ASCII pour le terminal"""
        rates = self.api.get_historical_rates(base, target, days)
        if not rates:
            print("✗ Impossible de récupérer l'historique")
            return
        
        sorted_rates = sorted(rates.items())
        values = [v for _, v in sorted_rates]
        
        if len(values) == 0:
            print("✗ Pas de données disponibles")
            return
        
        min_val = min(values)
        max_val = max(values)
        avg_val = sum(values) / len(values)
        range_val = max_val - min_val if max_val != min_val else 1
        
        print(f"\n📊 Évolution {base} → {target} ({days}j)")
        print(f"   Min: {min_val:.4f} | Max: {max_val:.4f} | Moy: {avg_val:.4f}")
        print("─" * 55)
        
        # Afficher le graphe
        height = 12
        width = min(40, len(values))
        step = max(1, len(values) // width)
        sampled_values = values[::step][:width]
        
        for i in range(height, -1, -1):
            level = min_val + (range_val * i / height)
            if i == height:
                line = f"{max_val:>10.4f} │ "
            elif i == 0:
                line = f"{min_val:>10.4f} │ "
            elif i == height // 2:
                line = f"{avg_val:>10.4f} │ "
            else:
                line = f"{'':>10} │ "
            
            for val in sampled_values:
                normalized = (val - min_val) / range_val * height
                if normalized >= i:
                    line += "█"
                elif normalized >= i - 0.5:
                    line += "▄"
                else:
                    line += " "
            print(line)
        
        print(f"{'':>10} └" + "─" * len(sampled_values))

# INTERFACE CLI

class CLIInterface:
    """Interface en ligne de commande avec animations"""
    
    def __init__(self):
        self.converter = CurrencyConverter()
    
    def clear_screen(self):
        """Efface l'écran"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def sleep(self, ms):
        """Pause en millisecondes"""
        time.sleep(ms / 1000)
    
    def bien_venu(self):
        i = 0
        """Animation de bienvenue"""
        title = "      BIENVENUE SUR LE CONVERTISSEUR      "
        nb_char = len(title)
        for i in range(nb_char):
            self.clear_screen()
            print("\n\n\t\t\t++++++++++++++++++++++++++++++++++++++++++++")
            print("\t\t+=+=+=+=+\033[1;35m", end="")
            for u in range(i + 1):
                print(title[u], end="")
            for t in range(i + 1, nb_char):
                print(" ", end="")
            print("\033[0m++=+=+=+=+")
            print("\t\t+\t++++++++++++++++++++++++++++++++++++++++++++\t    +")
            if title[i] != ' ':
                pass#self.sleep(50)
    
    def aurevoir(self):
        """Animation d'au revoir"""
        msg = " AU REVOIR ET MERCI "
        nb = len(msg)
        for i in range(nb // 2 + 1):
            self.clear_screen()
            print("\n\n")
            print("\t\t+====+ \033[1;35m", end="")
            for u in range(i):
                print(msg[u], end="")
            for u in range(i, nb - i):
                print(" ", end="")
            for u in range(nb - i, nb):
                print(msg[u], end="")
            print("\033[0m +====+")
            #self.sleep(70)
        print("\n")
    
    def choix_non_disponible(self):
        """Message d'erreur pour choix invalide"""
        print("\n\t\t    +=+=+=+=+=+=+=+       \033[1;31m\033[5mCHOIX NON DISPONIBLE\033[0m\033[0m       +=+=+=+=+=+=+=+")
    
    def print_header(self):
        """Affiche l'en-tête"""
        print("\n\n\t\t\t++++++++++++++++++++++++++++++++++++++++++++")
        print("\t\t+=+=+=+=+     \033[1;35m BIENVENUE SUR LE CONVERTISSEUR      \033[0m++=+=+=+=+")
        print("\t\t+\t++++++++++++++++++++++++++++++++++++++++++++\t    +")
    
    def print_menu(self):
        """Affiche le menu principal"""
        print("\t\t+\t\t\t\t\t\t\t    +")
        print("\t\t+ =====\033[1;3m \033[1;4mMENU\033[0m \033[0m=====\t\t\t\t\t    +")
        print("\t\t+   1.   Convertir une devise\t\t\t\t    +")
        print("\t\t+   2.   Voir les taux disponibles\t\t\t    +")
        print("\t\t+   3.   Historique sur 30 jours\t\t\t    +")
        print("\t\t+   4.   Statistiques du cache\t\t\t\t    +")
        print("\t\t+   5.   Nettoyer le cache\t\t\t\t    +")
        print("\t\t+   0.   Quitter\t\t\t\t\t    +")
        print("\t\t+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    
    def handle_convert(self):
        """Gère la conversion de devises"""
        print("\n\t\t" + "═" * 60)
        print("    \t\t\t\t CONVERSION DE DEVISES")
        print("\t\t"+"═" * 60)
        
        # Afficher les devises disponibles
        print("\n\t\t\t Devises disponibles:")
        currencies = self.converter.available_currencies
        print("\t\t\t",end="")
        for i, curr in enumerate(currencies):
            print(f"   {curr}", end="")
            if (i + 1) % 5 == 0:
                print()
                print("\t\t\t",end="")
        print("\n")
        
        try:
            amount = float(input("\t\t   Montant à convertir: "))
            from_curr = input("\t\t   Devise source (ex: EUR): ").strip().upper()
            to_curr = input("\t\t   Devise cible (ex: USD): ").strip().upper()
            
            print("\n\t\t   ⟳ Conversion en cours...")
            result = self.converter.convert(amount, from_curr, to_curr)
            
            if result:
                print("\n\t\t   " + "─" * 40)
                print(f"   \t\t RÉSULTAT:")
                print(f"\t\t   {result.amount:,.2f} {result.from_currency} = "
                      f"\\t\t033[1;32m{result.converted_amount:,.2f} {result.to_currency}\033[0m")
                print(f"\t\t     Taux: 1 {result.from_currency} = {result.rate:.6f} {result.to_currency}")
                print(f"\t\t    Date: {result.timestamp.strftime('%d/%m/%Y %H:%M:%S')}")
                print("\t\t   " + "─" * 40)
            else:
                print("\n\t\t   Erreur lors de la conversion")
                
        except ValueError:
            print("\n\t\t    Montant invalide - veuillez entrer un nombre")
    
    def handle_all_rates(self):
        """Affiche tous les taux"""
        print("\n\t\t" + "═" * 60)
        print("\t\t     TAUX DE CHANGE ACTUELS")
        print("\t\t"+"═" * 60)
        
        base = input("\n\t\t   Devise de base (défaut: EUR): ").strip().upper() or 'EUR'
        
        print(f"\n\t\t   ⟳ Récupération des taux pour {base}...")
        rates = self.converter.api.get_all_rates(base)
        
        if rates:
            print(f"\n\t\t   💱 Taux de change (base: {base}):")
            print("   " + "─" * 35)
            
            sorted_rates = sorted(rates.items())
            for i, (currency, rate) in enumerate(sorted_rates[:20]):
                print(f"\t\t   {currency}: {rate:>12.4f}")
            
            if len(rates) > 20:
                print(f"\n\t\t   ... et {len(rates) - 20} autres devises")
        else:
            print("\t\t    Impossible de récupérer les taux")
    
    def handle_history(self):
        """Affiche l'historique des taux"""
        print("\n\t\t" + "═" * 60)
        print("\t\t      HISTORIQUE SUR 30 JOURS")
        print("\t\t"+"═" * 60)
        
        base = input("\n\t\t   Devise source (ex: EUR): ").strip().upper() or 'EUR'
        target = input("\t\t   Devise cible (ex: USD): ").strip().upper() or 'USD'
        
        # Afficher le graphe ASCII
        self.converter.print_ascii_chart(base, target)
        
        # Proposer le graphe matplotlib si disponible
        if MATPLOTLIB_AVAILABLE:
            show_graph = input("\n\t\t   Afficher le graphe détaillé? (o/n): ").lower()
            if show_graph in ['o', 'oui', 'y', 'yes']:
                self.converter.display_rate_chart(base, target)
    
    def handle_cache_stats(self):
        """Affiche les statistiques du cache"""
        print("\t\t"+"\n" + "═" * 60)
        print("\t\t    🗄️  STATISTIQUES DU CACHE")
        print("\t\t"+"═" * 60)
        
        history = self.converter.db.get_conversion_history(30)
        
        print(f"\n\t\t   ✓ Conversions effectuées (30 derniers jours): {len(history)}")
        
        if history:
            total_amount = sum(h['amount'] for h in history)
            currencies_used = set()
            for h in history:
                currencies_used.add(h['from_currency'])
                currencies_used.add(h['to_currency'])
            
            print(f"\t\t   ✓ Volume total converti: {total_amount:,.2f}")
            print(f"\t\t   ✓ Devises utilisées: {', '.join(sorted(currencies_used))}")
            
            # Dernières conversions
            print(f"\n\t\t     Dernières conversions:")
            print("\t\t   " + "─" * 50)
            for h in history[:5]:
                print(f"\t\t   {h['amount']:.2f} {h['from_currency']} → "
                      f"{h['converted_amount']:.2f} {h['to_currency']}")
        
        print(f"\n\t\t   ✓ TTL du cache: {CACHE_TTL // 60} minutes")
        print(f"\t\t   ✓ Fichier de base de données: {DB_PATH}")
    
    def handle_cleanup(self):
        """Nettoie le cache"""
        print("\n\t\t" + "═" * 60)
        print("\t\t     NETTOYAGE DU CACHE")
        print("\t\t"+"═" * 60)
        
        confirm = input("\n\t\t   Confirmer le nettoyage? (o/n): ").lower()
        if confirm in ['o', 'oui', 'y', 'yes']:
            print("\n\t\t   ⟳ Nettoyage en cours...")
            deleted = self.converter.db.cleanup_expired_cache()
            print(f"\t\t   ✓ {deleted} entrée(s) expirée(s) supprimée(s)")
        else:
            print("\t\t   ✗ Nettoyage annulé")
    
    def run(self):
        """Boucle principale de l'application"""
        try:
            # Animation de bienvenue
            self.bien_venu()
            
            print(f"\n\t\t   ✓ {len(self.converter.available_currencies)} devises disponibles")
            self.sleep(1000)
            
            while True:
                self.clear_screen()
                self.print_header()
                self.print_menu()
                
                choix_str = input("\n\t\t   Votre choix: ").strip()
                
                try:
                    choix = int(choix_str)
                except ValueError:
                    choix = -1
                
                if choix == 1:
                    self.handle_convert()
                elif choix == 2:
                    self.handle_all_rates()
                elif choix == 3:
                    self.handle_history()
                elif choix == 4:
                    self.handle_cache_stats()
                elif choix == 5:
                    self.handle_cleanup()
                elif choix == 0:
                    self.aurevoir()
                    break
                else:
                    self.choix_non_disponible()
                
                input("\n\t\t   Appuyez sur Entrée pour continuer...")
                
        except KeyboardInterrupt:
            print("\n\n")
            self.aurevoir()
        except Exception as e:
            print(f"\n\t\t   ❌ Erreur inattendue: {e}")
            raise


# POINT D'ENTRÉE

def main():
    """Point d'entrée principal de l'application"""
    print("\n\t\t" + "═" * 60)
    print("\t\t    💱 CONVERTISSEUR DE DEVISES PRO 💱")
    print("\t\t"+"═" * 60)
    print("\n\t\t   Initialisation...")
    
    try:
        cli = CLIInterface()
        cli.run()
    except Exception as e:
        print(f"\n\t\t    Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
