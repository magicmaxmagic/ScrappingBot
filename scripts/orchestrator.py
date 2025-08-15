#!/usr/bin/env python3
"""
Orchestrateur global pour le scraper
Lance tous les tests, génère le dashboard et démarre le monitoring
"""
import subprocess
import time
import sys
from pathlib import Path
import argparse
from datetime import datetime

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def log(message: str, color: str = Colors.WHITE):
    """Log avec couleur et timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {color}{message}{Colors.RESET}")

def run_command(cmd: list, description: str, critical: bool = True) -> bool:
    """Exécute une commande avec gestion d'erreur"""
    log(f"🚀 {description}...", Colors.CYAN)
    
    try:
        result = subprocess.run(
            cmd, 
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes max
        )
        
        if result.returncode == 0:
            log(f"✅ {description} - Succès", Colors.GREEN)
            return True
        else:
            log(f"❌ {description} - Échec (code: {result.returncode})", Colors.RED)
            if critical:
                log(f"   stderr: {result.stderr[:200]}...", Colors.RED)
            return not critical
            
    except subprocess.TimeoutExpired:
        log(f"⏰ {description} - Timeout", Colors.YELLOW)
        return not critical
    except Exception as e:
        log(f"💥 {description} - Erreur: {e}", Colors.RED)
        return not critical

def run_demo_scrapes():
    """Lance quelques scrapes de démonstration"""
    log("🎯 Lancement des scrapes de démonstration...", Colors.BOLD)
    
    demo_configs = [
        {
            'where': 'montreal',
            'what': 'condo-demo', 
            'args': ['--timeout', '10000'],
            'description': 'Scrape Montreal condos (WAF attendu)'
        },
        {
            'where': 'demo-mock',
            'what': 'test-data',
            'args': ['--dom', '--source', 'mock', '--timeout', '5000'],
            'description': 'Test extraction DOM avec données mock'
        },
        {
            'where': 'debug-test',
            'what': 'visual-debug',
            'args': ['--debug', '--timeout', '8000'],
            'description': 'Test mode debug avec captures'
        }
    ]
    
    success_count = 0
    
    for config in demo_configs:
        cmd = [
            'python3', 'scraper/spiders/clean_scraper.py',
            '--where', config['where'],
            '--what', config['what']
        ] + config['args']
        
        if run_command(cmd, config['description'], critical=False):
            success_count += 1
        
        time.sleep(2)  # Pause entre scrapes
    
    log(f"📊 Scrapes de démo: {success_count}/{len(demo_configs)} réussis", Colors.CYAN)
    return success_count > 0

def main():
    parser = argparse.ArgumentParser(description="Orchestrateur global du scraper")
    parser.add_argument('--skip-tests', action='store_true', help='Ignorer les tests automatisés')
    parser.add_argument('--skip-demo', action='store_true', help='Ignorer les scrapes de démo')
    parser.add_argument('--skip-dashboard', action='store_true', help='Ignorer la génération du dashboard')
    parser.add_argument('--monitor', action='store_true', help='Démarrer le monitoring à la fin')
    parser.add_argument('--monitor-interval', type=int, default=60, help='Intervalle de monitoring (secondes)')
    args = parser.parse_args()
    
    log("🤖 ORCHESTRATEUR SCRAPER - Démarrage", Colors.BOLD)
    log("=" * 60, Colors.MAGENTA)
    
    start_time = time.time()
    
    # Phase 1: Tests automatisés
    if not args.skip_tests:
        log("\n🧪 PHASE 1: Tests automatisés", Colors.BOLD)
        log("-" * 40, Colors.BLUE)
        
        success = run_command(
            ['python3', 'scripts/test_suite.py'],
            'Suite de tests complète'
        )
        
        if not success:
            log("⚠️ Des tests ont échoué, mais on continue...", Colors.YELLOW)
    else:
        log("⏭️ Tests automatisés ignorés", Colors.YELLOW)
    
    # Phase 2: Scrapes de démonstration
    if not args.skip_demo:
        log("\n🎯 PHASE 2: Scrapes de démonstration", Colors.BOLD) 
        log("-" * 40, Colors.BLUE)
        
        run_demo_scrapes()
    else:
        log("⏭️ Scrapes de démo ignorés", Colors.YELLOW)
    
    # Phase 3: Génération du dashboard
    if not args.skip_dashboard:
        log("\n📊 PHASE 3: Génération du dashboard", Colors.BOLD)
        log("-" * 40, Colors.BLUE)
        
        success = run_command(
            ['python3', 'scripts/generate_dashboard.py'],
            'Dashboard de visualisation',
            critical=False
        )
        
        if success:
            dashboard_path = Path(__file__).resolve().parents[1] / "logs/dashboard.html"
            log(f"🌐 Dashboard disponible: file://{dashboard_path}", Colors.GREEN)
    else:
        log("⏭️ Dashboard ignoré", Colors.YELLOW)
    
    # Phase 4: Monitoring en temps réel
    if args.monitor:
        log("\n📡 PHASE 4: Monitoring en temps réel", Colors.BOLD)
        log("-" * 40, Colors.BLUE)
        
        log(f"🔄 Démarrage monitoring (intervalle: {args.monitor_interval}s)", Colors.CYAN)
        log("💡 Appuyez sur Ctrl+C pour arrêter", Colors.WHITE)
        
        try:
            subprocess.run([
                'python3', 'scripts/monitor.py',
                '--interval', str(args.monitor_interval)
            ], cwd=Path(__file__).resolve().parents[1])
        except KeyboardInterrupt:
            log("\n👋 Monitoring arrêté", Colors.CYAN)
    
    # Rapport final
    total_time = time.time() - start_time
    log("\n🎉 ORCHESTRATION TERMINÉE", Colors.BOLD)
    log("=" * 60, Colors.MAGENTA)
    log(f"⏱️ Temps total: {total_time:.1f}s", Colors.BLUE)
    
    # Instructions finales
    log("\n📋 PROCHAINES ÉTAPES:", Colors.BOLD)
    log("• 🌐 Ouvrir logs/dashboard.html pour voir les résultats", Colors.WHITE)
    log("• 📊 Consulter logs/test_report.json pour les détails des tests", Colors.WHITE)
    log("• 🔍 Vérifier logs/preview_*.json pour les données scrapées", Colors.WHITE)
    log("• 🚀 Lancer scripts/monitor.py --once pour un status check", Colors.WHITE)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
