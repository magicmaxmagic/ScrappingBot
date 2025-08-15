#!/usr/bin/env python3
"""
Monitoring en temps réel du scraper
Surveillance des performances, alertes et métriques
"""
import json
import time
import os
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
import argparse
import threading
from dataclasses import dataclass

@dataclass
class MetricPoint:
    """Point de métrique avec timestamp"""
    timestamp: datetime
    value: float
    label: str

class ScraperMonitor:
    def __init__(self, interval: int = 30):
        self.interval = interval
        self.running = False
        self.metrics = {
            'response_times': [],
            'success_rates': [],
            'listing_counts': [],
            'error_counts': [],
        }
        self.alerts = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log avec timestamp et niveau"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        levels = {
            "INFO": "📊",
            "WARN": "⚠️",
            "ERROR": "❌",
            "SUCCESS": "✅",
            "ALERT": "🚨"
        }
        icon = levels.get(level, "ℹ️")
        print(f"[{timestamp}] {icon} {message}")
    
    def get_preview_files_stats(self) -> Dict[str, Any]:
        """Analyse les fichiers preview pour extraire des métriques"""
        logs_dir = Path("logs")
        stats = {
            'total_files': 0,
            'total_listings': 0,
            'blocked_sources': 0,
            'successful_sources': 0,
            'avg_response_time': 0,
            'latest_scrapes': []
        }
        
        if not logs_dir.exists():
            return stats
        
        preview_files = list(logs_dir.glob("preview_*.json"))
        stats['total_files'] = len(preview_files)
        
        response_times = []
        
        for file in preview_files:
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                
                # Métriques par fichier
                count = data.get('count', 0)
                blocked = data.get('blocked', True)
                elapsed = data.get('elapsed_sec', 0)
                
                stats['total_listings'] += count
                response_times.append(elapsed)
                
                if blocked:
                    stats['blocked_sources'] += 1
                elif count > 0:
                    stats['successful_sources'] += 1
                
                # Garder les derniers scrapes
                stats['latest_scrapes'].append({
                    'source': file.stem.replace('preview_', ''),
                    'count': count,
                    'blocked': blocked,
                    'elapsed': elapsed,
                    'timestamp': data.get('timestamp', file.stat().st_mtime)
                })
                
            except Exception as e:
                self.log(f"Erreur lecture {file}: {e}", "ERROR")
        
        if response_times:
            stats['avg_response_time'] = sum(response_times) / len(response_times)
        
        # Trier par timestamp décroissant
        stats['latest_scrapes'].sort(key=lambda x: x['timestamp'], reverse=True)
        
        return stats
    
    def run_health_check(self) -> Dict[str, Any]:
        """Exécute un check de santé du scraper"""
        self.log("Exécution health check...", "INFO")
        
        start_time = time.time()
        
        try:
            # Test rapide avec timeout court
            result = subprocess.run([
                "python3", "scraper/spiders/clean_scraper.py",
                "--where", "health-check",
                "--what", "monitor",
                "--timeout", "3000"
            ], 
            capture_output=True, 
            text=True, 
            timeout=15,
            cwd=Path(__file__).resolve().parents[1]
            )
            
            elapsed = time.time() - start_time
            
            return {
                'success': result.returncode in [0, 2],  # 0=success, 2=blocked (OK)
                'response_time': elapsed,
                'exit_code': result.returncode,
                'stdout': result.stdout[-200:] if result.stdout else "",
                'stderr': result.stderr[-200:] if result.stderr else ""
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'response_time': time.time() - start_time,
                'exit_code': -1,
                'error': 'Timeout'
            }
        except Exception as e:
            return {
                'success': False,
                'response_time': time.time() - start_time,
                'exit_code': -2,
                'error': str(e)
            }
    
    def check_disk_space(self) -> Dict[str, Any]:
        """Vérifie l'espace disque dans logs/"""
        logs_dir = Path("logs")
        if not logs_dir.exists():
            return {'available_mb': 0, 'used_mb': 0, 'warning': True}
        
        try:
            # Taille du dossier logs
            total_size = sum(f.stat().st_size for f in logs_dir.rglob('*') if f.is_file())
            used_mb = total_size / (1024 * 1024)
            
            # Espace libre sur le disque
            stat = os.statvfs(logs_dir)
            available_mb = (stat.f_bavail * stat.f_frsize) / (1024 * 1024)
            
            return {
                'available_mb': available_mb,
                'used_mb': used_mb,
                'warning': available_mb < 100  # Moins de 100MB libre
            }
        except Exception as e:
            return {'error': str(e), 'warning': True}
    
    def detect_anomalies(self, current_stats: Dict[str, Any]) -> List[str]:
        """Détecte des anomalies dans les métriques"""
        anomalies = []
        
        # Taux de blocage élevé
        total_sources = current_stats['blocked_sources'] + current_stats['successful_sources']
        if total_sources > 0:
            block_rate = current_stats['blocked_sources'] / total_sources
            if block_rate > 0.8:  # Plus de 80% bloqué
                anomalies.append(f"Taux de blocage élevé: {block_rate:.1%}")
        
        # Temps de réponse élevé
        if current_stats['avg_response_time'] > 30:  # Plus de 30 secondes
            anomalies.append(f"Temps de réponse élevé: {current_stats['avg_response_time']:.1f}s")
        
        # Aucun listing récupéré
        if current_stats['total_listings'] == 0 and current_stats['successful_sources'] > 0:
            anomalies.append("Aucun listing récupéré malgré des sources actives")
        
        # Vérifier les scrapes récents (dernière heure)
        recent_scrapes = [
            s for s in current_stats['latest_scrapes']
            if isinstance(s['timestamp'], (int, float)) and 
            datetime.fromtimestamp(s['timestamp']) > datetime.now() - timedelta(hours=1)
        ]
        
        if len(recent_scrapes) == 0 and total_sources > 0:
            anomalies.append("Aucun scrape récent détecté")
        
        return anomalies
    
    def save_metrics_history(self, stats: Dict[str, Any], health: Dict[str, Any]):
        """Sauvegarde l'historique des métriques"""
        history_file = Path("logs/monitor_history.json")
        
        # Charger historique existant
        history = []
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    history = json.load(f)
            except:
                history = []
        
        # Ajouter point actuel
        point = {
            'timestamp': datetime.now().isoformat(),
            'stats': stats,
            'health': health,
            'disk': self.check_disk_space()
        }
        history.append(point)
        
        # Garder seulement les 24 dernières heures (si interval=30min, max 48 points)
        max_points = 48
        if len(history) > max_points:
            history = history[-max_points:]
        
        # Sauvegarder
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    
    def generate_status_report(self, stats: Dict[str, Any], health: Dict[str, Any]) -> str:
        """Génère un rapport de statut"""
        disk = self.check_disk_space()
        anomalies = self.detect_anomalies(stats)
        
        status = "🟢 SAIN" if health['success'] and len(anomalies) == 0 else "🟡 ATTENTION" if health['success'] else "🔴 CRITIQUE"
        
        report = f"""
╭─────────────────────────────────────────────────╮
│  🤖 SCRAPER MONITORING - {datetime.now().strftime('%H:%M:%S')}           │
├─────────────────────────────────────────────────┤
│  Status: {status}                                │
│                                                 │
│  📊 MÉTRIQUES:                                  │
│  • Total listings: {stats['total_listings']:,}                      │
│  • Sources actives: {stats['successful_sources']}/{stats['successful_sources'] + stats['blocked_sources']}                         │
│  • Temps moyen: {stats['avg_response_time']:.1f}s                     │
│  • Health check: {health['response_time']:.1f}s (code: {health['exit_code']})     │
│                                                 │
│  💾 DISQUE:                                     │
│  • Utilisé: {disk.get('used_mb', 0):.1f} MB                          │
│  • Libre: {disk.get('available_mb', 0):.1f} MB                        │
│                                                 │
│  🚨 ALERTES: {len(anomalies)}                                  │
"""
        
        for anomaly in anomalies[:3]:  # Max 3 alertes
            report += f"│  • {anomaly[:43]:43} │\n"
        
        report += "╰─────────────────────────────────────────────────╯"
        
        return report
    
    def monitor_loop(self):
        """Boucle principale de monitoring"""
        self.log("🚀 Démarrage du monitoring...", "SUCCESS")
        self.log(f"📊 Intervalle: {self.interval}s", "INFO")
        
        iteration = 0
        
        while self.running:
            try:
                iteration += 1
                self.log(f"--- Cycle {iteration} ---", "INFO")
                
                # Collecter métriques
                stats = self.get_preview_files_stats()
                health = self.run_health_check()
                
                # Sauvegarder historique
                self.save_metrics_history(stats, health)
                
                # Générer rapport
                report = self.generate_status_report(stats, health)
                print(report)
                
                # Alertes critiques
                if not health['success']:
                    self.log("🚨 ALERTE: Health check échoué!", "ALERT")
                
                disk = self.check_disk_space()
                if disk.get('warning', False):
                    self.log(f"🚨 ALERTE: Espace disque faible ({disk.get('available_mb', 0):.1f} MB)", "ALERT")
                
                # Attendre prochain cycle
                time.sleep(self.interval)
                
            except KeyboardInterrupt:
                self.log("👋 Arrêt demandé par l'utilisateur", "INFO")
                break
            except Exception as e:
                self.log(f"💥 Erreur monitoring: {e}", "ERROR")
                time.sleep(5)  # Pause courte avant retry
        
        self.log("🛑 Monitoring arrêté", "INFO")
    
    def start(self):
        """Démarre le monitoring en arrière-plan"""
        if self.running:
            self.log("⚠️ Monitoring déjà en cours", "WARN")
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop(self):
        """Arrête le monitoring"""
        self.running = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join(timeout=5)
    
    def run_once(self):
        """Exécute un cycle de monitoring unique"""
        stats = self.get_preview_files_stats()
        health = self.run_health_check()
        report = self.generate_status_report(stats, health)
        print(report)
        return stats, health

def main():
    parser = argparse.ArgumentParser(description="Monitoring du scraper")
    parser.add_argument('--interval', type=int, default=30, help='Intervalle en secondes (défaut: 30)')
    parser.add_argument('--once', action='store_true', help='Exécuter un cycle unique')
    parser.add_argument('--daemon', action='store_true', help='Mode daemon (arrière-plan)')
    args = parser.parse_args()
    
    monitor = ScraperMonitor(interval=args.interval)
    
    if args.once:
        # Cycle unique
        monitor.run_once()
        return 0
    
    if args.daemon:
        # Mode daemon
        monitor.start()
        try:
            # Garder le processus vivant
            while monitor.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            monitor.stop()
    else:
        # Mode interactif
        try:
            monitor.monitor_loop()
        except KeyboardInterrupt:
            pass
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
