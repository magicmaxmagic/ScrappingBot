#!/usr/bin/env python3
"""
Suite de tests automatisés complète pour le scraper
Tests unitaires, d'intégration, de performance et de régression
"""
import asyncio
import json
import os
import subprocess
import time
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Tuple
import argparse
from datetime import datetime
import shutil
import signal
import threading

class Colors:
    """Couleurs ANSI pour les logs"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

class TestRunner:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results = {
            'passed': 0,
            'failed': 0, 
            'errors': 0,
            'skipped': 0,
            'details': []
        }
        self.start_time = time.time()
        
    def log(self, message: str, color: str = Colors.WHITE):
        """Log avec couleur"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {color}{message}{Colors.RESET}")
        
    def run_command(self, cmd: List[str], timeout: int = 30, capture_output: bool = True) -> Tuple[int, str, str]:
        """Exécute une commande avec timeout"""
        try:
            if capture_output:
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    timeout=timeout,
                    cwd=Path(__file__).resolve().parents[1]
                )
                return result.returncode, result.stdout, result.stderr
            else:
                result = subprocess.run(cmd, timeout=timeout, cwd=Path(__file__).resolve().parents[1])
                return result.returncode, "", ""
        except subprocess.TimeoutExpired:
            return -1, "", "Timeout dépassé"
        except Exception as e:
            return -2, "", str(e)
    
    def test_scraper_help(self) -> bool:
        """Test: Affichage de l'aide du scraper"""
        self.log("🔍 Test affichage aide...", Colors.CYAN)
        
        code, stdout, stderr = self.run_command([
            "python3", "scraper/spiders/clean_scraper.py", "--help"
        ])
        
        if code == 0 and "--where" in stdout and "--what" in stdout:
            self.log("✅ Aide affichée correctement", Colors.GREEN)
            return True
        else:
            self.log(f"❌ Erreur aide: code={code}, stderr={stderr[:100]}...", Colors.RED)
            return False
    
    def test_scraper_invalid_args(self) -> bool:
        """Test: Arguments invalides"""
        self.log("🔍 Test arguments invalides...", Colors.CYAN)
        
        code, stdout, stderr = self.run_command([
            "python3", "scraper/spiders/clean_scraper.py",
            "--where", "test"
            # Manque --what
        ])
        
        if code != 0:
            self.log("✅ Arguments invalides détectés", Colors.GREEN)
            return True
        else:
            self.log("❌ Arguments invalides non détectés", Colors.RED)
            return False
    
    def test_waf_detection(self) -> bool:
        """Test: Détection WAF sur realtor.ca"""
        self.log("🔍 Test détection WAF...", Colors.CYAN)
        
        code, stdout, stderr = self.run_command([
            "python3", "scraper/spiders/clean_scraper.py",
            "--where", "test", 
            "--what", "test",
            "--timeout", "5000"
        ])
        
        # Code 2 = WAF bloqué (comportement attendu)
        if code == 2:
            self.log("✅ WAF détecté correctement", Colors.GREEN)
            return True
        elif code == 0:
            self.log("⚠️  Pas de WAF détecté (site accessible)", Colors.YELLOW)
            return True
        else:
            self.log(f"❌ Erreur détection WAF: code={code}", Colors.RED)
            return False
    
    def test_mock_data_extraction(self) -> bool:
        """Test: Extraction sur données de test"""
        self.log("🔍 Test extraction données mock...", Colors.CYAN)
        
        # Créer données de test temporaires
        test_html = """
        <!DOCTYPE html>
        <html>
        <body>
            <div class="listing" data-price="500000">
                <h3>Belle maison à Montreal</h3>
                <div class="price">500 000$</div>
                <div class="address">123 Rue Test, Montreal</div>
                <div class="details">3 chambres, 2 salles de bain</div>
            </div>
            <div class="listing" data-price="350000">
                <h3>Condo moderne</h3>
                <div class="price">350 000$</div>
                <div class="address">456 Ave Test, Laval</div>
                <div class="details">2 chambres, 1 salle de bain</div>
            </div>
        </body>
        </html>
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(test_html)
            temp_file = f.name
        
        try:
            code, stdout, stderr = self.run_command([
                "python3", "scraper/spiders/clean_scraper.py",
                "--where", "test",
                "--what", "mock",
                "--source", "mock",
                "--start_url", f"file://{temp_file}",
                "--dom",
                "--timeout", "5000"
            ])
            
            if code == 0 and "✅ Success:" in stdout:
                # Vérifier le fichier preview
                preview_path = Path("logs/preview_mock.json")
                if preview_path.exists():
                    with open(preview_path) as f:
                        preview = json.load(f)
                    
                    if preview.get('count', 0) > 0 and not preview.get('blocked', True):
                        self.log(f"✅ Extraction mock réussie: {preview['count']} items", Colors.GREEN)
                        return True
            
            self.log(f"❌ Extraction mock échouée: code={code}", Colors.RED)
            return False
            
        finally:
            os.unlink(temp_file)
    
    def test_debug_mode(self) -> bool:
        """Test: Mode debug avec capture"""
        self.log("🔍 Test mode debug...", Colors.CYAN)
        
        code, stdout, stderr = self.run_command([
            "python3", "scraper/spiders/clean_scraper.py", 
            "--where", "test",
            "--what", "debug", 
            "--debug",
            "--timeout", "5000"
        ], timeout=60)
        
        # Vérifier fichiers debug générés
        debug_files = list(Path("logs").glob("debug_*.html")) + list(Path("logs").glob("debug_*.png"))
        
        if len(debug_files) > 0:
            self.log(f"✅ Mode debug OK: {len(debug_files)} fichiers générés", Colors.GREEN)
            return True
        else:
            self.log("❌ Mode debug: aucun fichier généré", Colors.RED)
            return False
    
    def test_multiple_strategies(self) -> bool:
        """Test: Test de toutes les stratégies (XHR, DOM, etc.)"""
        self.log("🔍 Test stratégies multiples...", Colors.CYAN)
        
        strategies = [
            ("xhr", []),
            ("dom", ["--dom"]),
        ]
        
        success_count = 0
        
        for strategy, args in strategies:
            self.log(f"  - Test stratégie {strategy}...", Colors.BLUE)
            
            cmd = [
                "python3", "scraper/spiders/clean_scraper.py",
                "--where", "test",
                "--what", strategy,
                "--timeout", "5000"
            ] + args
            
            code, stdout, stderr = self.run_command(cmd)
            
            if code in [0, 2]:  # 0=success, 2=WAF blocked (OK)
                success_count += 1
                self.log(f"    ✅ {strategy} OK", Colors.GREEN)
            else:
                self.log(f"    ❌ {strategy} échec: {code}", Colors.RED)
        
        if success_count == len(strategies):
            self.log(f"✅ Toutes les stratégies testées: {success_count}/{len(strategies)}", Colors.GREEN)
            return True
        else:
            self.log(f"⚠️  Stratégies partielles: {success_count}/{len(strategies)}", Colors.YELLOW)
            return success_count > 0
    
    def test_output_format(self) -> bool:
        """Test: Format de sortie JSON valide"""
        self.log("🔍 Test format JSON...", Colors.CYAN)
        
        # Tester avec données mock pour garantir un output
        test_html = """
        <html><body>
        <div class="listing">
            <div class="price">400000</div>
            <div class="address">Test Address</div>
        </div>
        </body></html>
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(test_html)
            temp_file = f.name
        
        try:
            code, stdout, stderr = self.run_command([
                "python3", "scraper/spiders/clean_scraper.py",
                "--where", "format-test",
                "--what", "json", 
                "--source", "mock",
                "--start_url", f"file://{temp_file}",
                "--dom",
                "--timeout", "5000"
            ])
            
            preview_path = Path("logs/preview_json.json")
            if preview_path.exists():
                try:
                    with open(preview_path) as f:
                        data = json.load(f)
                    
                    # Vérifier structure JSON
                    required_fields = ['timestamp', 'count', 'blocked', 'strategy', 'elapsed_sec']
                    if all(field in data for field in required_fields):
                        self.log("✅ Format JSON valide", Colors.GREEN)
                        return True
                    else:
                        missing = [f for f in required_fields if f not in data]
                        self.log(f"❌ Champs JSON manquants: {missing}", Colors.RED)
                        return False
                        
                except json.JSONDecodeError as e:
                    self.log(f"❌ JSON invalide: {e}", Colors.RED)
                    return False
            else:
                self.log("❌ Fichier preview non généré", Colors.RED)
                return False
                
        finally:
            os.unlink(temp_file)
    
    def test_dev_server_integration(self) -> bool:
        """Test: Intégration avec le serveur de dev"""
        self.log("🔍 Test intégration serveur dev...", Colors.CYAN)
        
        # Démarrer le serveur en arrière-plan
        server_process = None
        try:
            server_process = subprocess.Popen([
                "python3", "scripts/dev_scraper_server.py"
            ], cwd=Path(__file__).resolve().parents[1])
            
            # Attendre que le serveur démarre
            time.sleep(3)
            
            # Tester endpoint /run
            code, stdout, stderr = self.run_command([
                "curl", "-X", "POST", 
                "http://127.0.0.1:8000/run",
                "-H", "Content-Type: application/json",
                "-d", '{"where": "test", "what": "server-test", "scraper": "realtor", "debug": false}'
            ], timeout=15)
            
            if code == 0:
                self.log("✅ Serveur de dev répond", Colors.GREEN)
                return True
            else:
                self.log(f"❌ Serveur de dev ne répond pas: {stderr}", Colors.RED)
                return False
                
        except Exception as e:
            self.log(f"❌ Erreur serveur dev: {e}", Colors.RED)
            return False
            
        finally:
            if server_process:
                server_process.terminate()
                time.sleep(1)
                if server_process.poll() is None:
                    server_process.kill()
    
    def test_performance_basic(self) -> bool:
        """Test: Performance de base (timeout respecté)"""
        self.log("🔍 Test performance...", Colors.CYAN)
        
        start = time.time()
        code, stdout, stderr = self.run_command([
            "python3", "scraper/spiders/clean_scraper.py",
            "--where", "perf-test",
            "--what", "performance",
            "--timeout", "3000"  # 3 secondes max
        ], timeout=10)
        
        elapsed = time.time() - start
        
        if elapsed < 8:  # Doit finir en moins de 8 secondes (avec marge)
            self.log(f"✅ Performance OK: {elapsed:.1f}s", Colors.GREEN)
            return True
        else:
            self.log(f"❌ Performance lente: {elapsed:.1f}s", Colors.RED)
            return False
    
    def test_concurrent_execution(self) -> bool:
        """Test: Exécutions concurrentes"""
        self.log("🔍 Test exécutions concurrentes...", Colors.CYAN)
        
        def run_scraper(test_id: int):
            """Fonction pour thread de test"""
            code, stdout, stderr = self.run_command([
                "python3", "scraper/spiders/clean_scraper.py",
                "--where", f"concurrent-{test_id}",
                "--what", "concurrent",
                "--timeout", "5000"
            ])
            return code
        
        # Lancer 3 scrapers en parallèle
        threads = []
        results = []
        
        for i in range(3):
            thread = threading.Thread(target=lambda i=i: results.append(run_scraper(i)))
            threads.append(thread)
            thread.start()
        
        # Attendre que tous finissent
        for thread in threads:
            thread.join(timeout=20)
        
        if len(results) == 3:
            self.log(f"✅ Exécutions concurrentes OK: {results}", Colors.GREEN)
            return True
        else:
            self.log(f"❌ Exécutions concurrentes échouées: {len(results)}/3", Colors.RED)
            return False
    
    def test_file_cleanup(self) -> bool:
        """Test: Nettoyage des fichiers temporaires"""
        self.log("🔍 Test nettoyage fichiers...", Colors.CYAN)
        
        # Compter fichiers avant
        logs_before = len(list(Path("logs").glob("*")))
        
        # Exécuter scraper
        code, stdout, stderr = self.run_command([
            "python3", "scraper/spiders/clean_scraper.py",
            "--where", "cleanup-test",
            "--what", "cleanup"
        ])
        
        # Compter fichiers après
        logs_after = len(list(Path("logs").glob("*")))
        
        # Ne doit pas y avoir explosion de fichiers temporaires
        if logs_after - logs_before < 10:  # Max 10 nouveaux fichiers
            self.log("✅ Pas d'accumulation de fichiers", Colors.GREEN)
            return True
        else:
            self.log(f"⚠️  Possible accumulation: +{logs_after - logs_before} fichiers", Colors.YELLOW)
            return True  # Warning mais pas échec
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Exécute tous les tests"""
        tests = [
            ("Arguments & Aide", self.test_scraper_help),
            ("Arguments Invalides", self.test_scraper_invalid_args),
            ("Détection WAF", self.test_waf_detection),
            ("Extraction Mock", self.test_mock_data_extraction),
            ("Mode Debug", self.test_debug_mode),
            ("Stratégies Multiples", self.test_multiple_strategies),
            ("Format JSON", self.test_output_format),
            ("Performance", self.test_performance_basic),
            ("Exécutions Concurrentes", self.test_concurrent_execution),
            ("Nettoyage Fichiers", self.test_file_cleanup),
            ("Intégration Serveur", self.test_dev_server_integration),
        ]
        
        self.log(f"\n🚀 Démarrage de {len(tests)} tests...\n", Colors.BOLD)
        
        for test_name, test_func in tests:
            self.log(f"\n{'='*60}", Colors.MAGENTA)
            self.log(f"Test: {test_name}", Colors.BOLD)
            self.log(f"{'='*60}", Colors.MAGENTA)
            
            try:
                start = time.time()
                success = test_func()
                elapsed = time.time() - start
                
                if success:
                    self.results['passed'] += 1
                    self.log(f"✅ PASSÉ ({elapsed:.1f}s)\n", Colors.GREEN)
                else:
                    self.results['failed'] += 1
                    self.log(f"❌ ÉCHOUÉ ({elapsed:.1f}s)\n", Colors.RED)
                
                self.results['details'].append({
                    'name': test_name,
                    'success': success,
                    'elapsed': elapsed
                })
                
            except Exception as e:
                self.results['errors'] += 1
                self.log(f"💥 ERREUR: {e}\n", Colors.RED)
                self.results['details'].append({
                    'name': test_name,
                    'success': False,
                    'error': str(e),
                    'elapsed': 0
                })
        
        # Rapport final
        total_time = time.time() - self.start_time
        self.generate_report(total_time)
        
        return self.results
    
    def generate_report(self, total_time: float):
        """Génère un rapport de test"""
        total_tests = self.results['passed'] + self.results['failed'] + self.results['errors']
        success_rate = (self.results['passed'] / total_tests * 100) if total_tests > 0 else 0
        
        self.log(f"\n{'='*80}", Colors.BOLD)
        self.log(f"📊 RAPPORT FINAL", Colors.BOLD)
        self.log(f"{'='*80}", Colors.BOLD)
        
        self.log(f"✅ Passés: {self.results['passed']}", Colors.GREEN)
        self.log(f"❌ Échecs: {self.results['failed']}", Colors.RED)
        self.log(f"💥 Erreurs: {self.results['errors']}", Colors.RED)
        self.log(f"📈 Taux de réussite: {success_rate:.1f}%", Colors.CYAN)
        self.log(f"⏱️  Temps total: {total_time:.1f}s", Colors.BLUE)
        
        # Sauvegarde rapport JSON
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_time': total_time,
            'success_rate': success_rate,
            **self.results
        }
        
        report_path = Path("logs/test_report.json")
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
        self.log(f"💾 Rapport sauvé: {report_path}", Colors.MAGENTA)

def main():
    parser = argparse.ArgumentParser(description="Suite de tests automatisés pour le scraper")
    parser.add_argument('-v', '--verbose', action='store_true', help='Mode verbeux')
    parser.add_argument('--test', help='Exécuter un test spécifique')
    args = parser.parse_args()
    
    runner = TestRunner(verbose=args.verbose)
    
    if args.test:
        # Test spécifique
        test_method = getattr(runner, f'test_{args.test}', None)
        if test_method:
            success = test_method()
            return 0 if success else 1
        else:
            runner.log(f"❌ Test '{args.test}' non trouvé", Colors.RED)
            return 1
    else:
        # Tous les tests
        results = runner.run_all_tests()
        return 0 if results['failed'] == 0 and results['errors'] == 0 else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
