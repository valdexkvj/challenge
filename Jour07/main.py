import requests
import json
import sqlite3
import time
import random
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import threading
import os

API_BASE_URL = "https://api.exchangerate.host"
CACHE_TTL = 600  # 10 minutes en secondes
MAX_RETRIES = 3
BASE_DELAY = 1

DB_PATH = "currency_cache.db"

@dataclass
class ConversionResult:
    from_currency: str
    to_currency: str
    amount: float
    converted_amount: float
    rate: float
    timestamp: datetime

class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._local = threading.local()
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(self.db_path)
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection
    
    def init_database(self):
        """Initialise la base de données avec les tables nécessaires"""
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
        
        # Table pour l'historique
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
    
    def cleanup_expired_cache(self):
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

class APIClient:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CurrencyConverter/1.0'
        })
    
    def _exponential_backoff(self, attempt: int) -> float:
        """Calcule le délai de retry avec backoff exponentiel"""
        delay = (BASE_DELAY * (2 ** attempt) + 
                random.uniform(0, 1))
        return min(delay, 30)  # Max 30 secondes
    
    def _make_request(self, url: str, params: Dict = None) -> Optional[Dict]:
        """Effectue une requête HTTP avec retry exponentiel"""
        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(url, params=params, timeout=10)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                if attempt == MAX_RETRIES - 1:
                    print(f"✗ Échec après {MAX_RETRIES} tentatives: {e}")
                    return None
                
                delay = self._exponential_backoff(attempt)
                print(f"⚠ Tentative {attempt + 1} échouée, retry dans {delay:.1f}s...")
                time.sleep(delay)
        
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

class CurrencyConverter:
    def __init__(self):
        self.db = DatabaseManager()
        self.api = APIClient(self.db)
        self.available_currencies = self._load_currencies()
    
    def _load_currencies(self) -> list:
        """Charge la liste des devises disponibles"""
        return ['EUR', 'USD', 'GBP', 'JPY', 'CHF', 
                'CAD', 'AUD', 'CNY', 'INR', 'MXN',
                'BRL', 'RUB', 'KRW', 'SGD', 'NZD']
    
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
        """Affiche un graphe de l'évolution des taux"""
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
            return
        
        sorted_rates = sorted(rates.items())
        values = [v for _, v in sorted_rates]
        
        if len(values) == 0:
            return
        
        min_val = min(values)
        max_val = max(values)
        range_val = max_val - min_val if max_val != min_val else 1
        
        print(f"\n📊 Évolution {base} → {target} ({days}j):")
        print("─" * 50)
        
        # Afficher le graphe
        height = 10
        for i in range(height, -1, -1):
            level = min_val + (range_val * i / height)
            line = f"{level:>8.4f} │ "
            
            for val in values[::max(1, len(values)//30)]:
                if val >= level:
                    line += "█"
                else:
                    line += " "
            print(line)
        
        print("         └" + "─" * min(40, len(values)))

class CLIInterface:
    def __init__(self):
        self.converter = CurrencyConverter()
    
    def clear_screen(self):
        """Efface l'écran"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self):
        """Affiche l'en-tête"""
        print("\n" + "═"*60)
        print("    💱 Convertisseur de Devises Pro 💱".center(60))
        print("═"*60)
    
    def print_menu(self):
        """Affiche le menu principal"""
        print("\n📋 Menu Principal:")
        print("   1. 💰 Convertir une devise")
        print("   2. 📊 Voir tous les taux")
        print("   3. 📈 Historique 30 jours")
        print("   4. 🗄️  Statistiques cache")
        print("   5. 🧹 Nettoyer le cache")
        print("   6. ❌ Quitter")
    
    def handle_convert(self):
        """Gère la conversion de devises"""
        print("\n💰 Conversion de devises")
        print("─" * 40)
        
        try:
            amount = float(input("Montant: "))
            from_curr = input("De (ex: EUR): ").strip().upper()
            to_curr = input("Vers (ex: USD): ").strip().upper()
            
            result = self.converter.convert(amount, from_curr, to_curr)
            
            if result:
                print(f"\n✅ Résultat:")
                print(f"   {result.amount:.2f} {result.from_currency} = "
                      f"{result.converted_amount:.2f} {result.to_currency}")
                print(f"   Taux: 1 {result.from_currency} = {result.rate:.6f} {result.to_currency}")
                print(f"   Date: {result.timestamp.strftime('%d/%m/%Y %H:%M')}")
            else:
                print("\n❌ Erreur lors de la conversion")
                
        except ValueError:
            print("\n⚠️ Montant invalide")
    
    def handle_all_rates(self):
        """Affiche tous les taux"""
        base = input("\nDevise de base (défaut: EUR): ").strip().upper() or 'EUR'
        
        print(f"\n📊 Récupération des taux pour {base}...")
        rates = self.converter.api.get_all_rates(base)
        
        if rates:
            print(f"\n💱 Taux de change ({base}):")
            print("─" * 35)
            for currency, rate in sorted(rates.items())[:15]:
                print(f"   {currency}: {rate:.4f}")
            print(f"   ... et {len(rates) - 15} autres devises")
        else:
            print("❌ Impossible de récupérer les taux")
    
    def handle_history(self):
        """Affiche l'historique"""
        print("\n📈 Historique sur 30 jours")
        print("─" * 40)
        
        base = input("De (ex: EUR): ").strip().upper() or 'EUR'
        target = input("Vers (ex: USD): ").strip().upper() or 'USD'
        
        # Afficher le graphe ASCII
        self.converter.print_ascii_chart(base, target)
        
        # Proposer le graphe matplotlib
        show_graph = input("\nAfficher le graphe détaillé? (o/n): ").lower()
        if show_graph in ['o', 'oui', 'y', 'yes']:
            self.converter.display_rate_chart(base, target)
    
    def handle_cache_stats(self):
        """Affiche les stats du cache"""
        print("\n🗄️  Statistiques du cache")
        print("─" * 40)
        
        history = self.converter.db.get_conversion_history(30)
        print(f"✓ Conversions (30j): {len(history)}")
        
        if history:
            total_amount = sum(h['amount'] for h in history)
            print(f"✓ Volume total: {total_amount:,.2f}")
        
        print(f"✓ TTL du cache: {CACHE_TTL // 60} minutes")
    
    def handle_cleanup(self):
        """Nettoie le cache"""
        print("\n🧹 Nettoyage du cache...")
        deleted = self.converter.db.cleanup_expired_cache()
        print(f"✓ {deleted} entrées expirées supprimées")
    
    def run(self):
        """Boucle principale"""
        self.clear_screen()
        self.print_header()
        
        print("\n✓ Initialisation...")
        print(f"✓ {len(self.converter.available_currencies)} devises disponibles")
        
        while True:
            self.print_menu()
            
            try:
                choice = input("\n❯ Votre choix: ").strip()
                
                if choice == '1':
                    self.handle_convert()
                elif choice == '2':
                    self.handle_all_rates()
                elif choice == '3':
                    self.handle_history()
                elif choice == '4':
                    self.handle_cache_stats()
                elif choice == '5':
                    self.handle_cleanup()
                elif choice == '6':
                    print("\n👋 Au revoir!")
                    break
                else:
                    print("\n⚠️ Choix invalide")
                
                input("\nAppuyez sur Entrée pour continuer...")
                self.clear_screen()
                self.print_header()
                
            except KeyboardInterrupt:
                print("\n\n👋 Au revoir!")
                break
            except Exception as e:
                print(f"\n❌ Erreur: {e}")

def main():
    """Point d'entrée principal"""
    try:
        cli = CLIInterface()
        cli.run()
    except Exception as e:
        print(f"Erreur fatale: {e}")
        raise

if __name__ == "__main__":
    main()
