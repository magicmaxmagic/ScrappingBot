#!/usr/bin/env python3
"""
Utilitaire de maintenance et nettoyage pour le scraper
Nettoyage des logs, archivage, optimisation
"""
import os
import shutil
import gzip
from pathlib import Path
from datetime import datetime, timedelta
import json
import argparse
from typing import Dict, List, Any

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def log(message: str, color: str = Colors.CYAN):
    """Log avec couleur et timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {color}{message}{Colors.RESET}")

def get_file_size_mb(file_path: Path) -> float:
    """Retourne la taille du fichier en MB"""
    try:
        return file_path.stat().st_size / (1024 * 1024)
    except:
        return 0

def get_directory_size_mb(dir_path: Path) -> float:
    """Retourne la taille totale du dossier en MB"""
    try:
        return sum(f.stat().st_size for f in dir_path.rglob('*') if f.is_file()) / (1024 * 1024)
    except:
        return 0

def archive_old_files(logs_dir: Path, days_old: int = 7) -> Dict[str, int]:
    """Archive les fichiers anciens"""
    log(f"📦 Archivage des fichiers de plus de {days_old} jours...", Colors.BLUE)
    
    archive_dir = logs_dir / "archive"
    archive_dir.mkdir(exist_ok=True)
    
    cutoff_date = datetime.now() - timedelta(days=days_old)
    stats = {'archived': 0, 'size_mb': 0.0}
    
    for file in logs_dir.glob("*.json"):
        if file.name.startswith("archive"):
            continue
            
        try:
            file_date = datetime.fromtimestamp(file.stat().st_mtime)
            
            if file_date < cutoff_date:
                # Archiver et compresser
                archive_name = f"{file.stem}_{file_date.strftime('%Y%m%d')}.json.gz"
                archive_path = archive_dir / archive_name
                
                with open(file, 'rb') as f_in:
                    with gzip.open(archive_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                stats['size_mb'] += get_file_size_mb(file)
                stats['archived'] += 1
                
                # Supprimer l'original
                file.unlink()
                log(f"  📦 {file.name} → {archive_name}", Colors.GREEN)
                
        except Exception as e:
            log(f"  ❌ Erreur archivage {file}: {e}", Colors.YELLOW)
    
    return stats

def clean_duplicate_previews(logs_dir: Path) -> Dict[str, int]:
    """Nettoie les fichiers preview dupliqués (même source, garder le plus récent)"""
    log("🧹 Nettoyage des previews dupliqués...", Colors.BLUE)
    
    # Grouper par source
    sources = {}
    for file in logs_dir.glob("preview_*.json"):
        source = file.stem.replace("preview_", "")
        if source not in sources:
            sources[source] = []
        sources[source].append(file)
    
    stats = {'removed': 0, 'size_mb': 0.0}
    
    for source, files in sources.items():
        if len(files) > 1:
            # Trier par date de modification (plus récent = dernière position)
            files.sort(key=lambda f: f.stat().st_mtime)
            
            # Garder seulement le plus récent
            for file in files[:-1]:  # Tous sauf le dernier
                stats['size_mb'] += get_file_size_mb(file)
                stats['removed'] += 1
                file.unlink()
                log(f"  🗑️ {file.name} (doublon)", Colors.GREEN)
    
    return stats

def clean_debug_files(logs_dir: Path, max_debug_files: int = 10) -> Dict[str, int]:
    """Nettoie les fichiers debug en gardant seulement les N plus récents"""
    log(f"🗂️ Nettoyage des fichiers debug (max: {max_debug_files})...", Colors.BLUE)
    
    # Fichiers debug HTML et PNG
    debug_files = list(logs_dir.glob("debug_*.html")) + list(logs_dir.glob("debug_*.png"))
    debug_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)  # Plus récent en premier
    
    stats = {'removed': 0, 'size_mb': 0.0}
    
    if len(debug_files) > max_debug_files:
        for file in debug_files[max_debug_files:]:  # Au-delà de la limite
            stats['size_mb'] += get_file_size_mb(file)
            stats['removed'] += 1
            file.unlink()
            log(f"  🗑️ {file.name} (trop ancien)", Colors.GREEN)
    
    return stats

def cleanup_empty_files(logs_dir: Path) -> Dict[str, int]:
    """Supprime les fichiers vides ou corrompus"""
    log("🔍 Nettoyage des fichiers vides/corrompus...", Colors.BLUE)
    
    stats = {'removed': 0, 'size_mb': 0.0}
    
    for file in logs_dir.glob("*.json"):
        try:
            if file.stat().st_size == 0:
                # Fichier vide
                stats['removed'] += 1
                file.unlink()
                log(f"  🗑️ {file.name} (vide)", Colors.GREEN)
            elif file.name.startswith("preview_"):
                # Vérifier si JSON valide
                with open(file, 'r') as f:
                    data = json.load(f)
                
                # Vérifier structure minimale
                if not isinstance(data, dict) or 'timestamp' not in data:
                    stats['removed'] += 1
                    file.unlink()
                    log(f"  🗑️ {file.name} (structure invalide)", Colors.GREEN)
                    
        except (json.JSONDecodeError, OSError) as e:
            # Fichier corrompu
            stats['size_mb'] += get_file_size_mb(file) 
            stats['removed'] += 1
            file.unlink()
            log(f"  🗑️ {file.name} (corrompu: {e})", Colors.GREEN)
    
    return stats

def generate_maintenance_report(logs_dir: Path) -> Dict[str, Any]:
    """Génère un rapport de maintenance"""
    log("📋 Génération du rapport de maintenance...", Colors.BLUE)
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_size_mb': get_directory_size_mb(logs_dir),
        'file_counts': {},
        'largest_files': [],
        'oldest_files': [],
        'recommendations': []
    }
    
    # Compter les types de fichiers
    for pattern in ['preview_*.json', 'debug_*.html', 'debug_*.png', '*.json', 'archive/*']:
        files = list(logs_dir.glob(pattern))
        file_type = pattern.replace('*', 'X')
        report['file_counts'][file_type] = len(files)
    
    # Plus gros fichiers
    all_files = [(f, get_file_size_mb(f)) for f in logs_dir.rglob('*') if f.is_file()]
    all_files.sort(key=lambda x: x[1], reverse=True)
    
    report['largest_files'] = [
        {'name': f.name, 'size_mb': round(size, 2)}
        for f, size in all_files[:5]
    ]
    
    # Plus anciens fichiers
    all_files.sort(key=lambda x: x[0].stat().st_mtime)
    report['oldest_files'] = [
        {
            'name': f.name, 
            'age_days': (datetime.now() - datetime.fromtimestamp(f.stat().st_mtime)).days
        }
        for f, _ in all_files[:5]
    ]
    
    # Recommandations
    if report['total_size_mb'] > 100:
        report['recommendations'].append("Dossier logs volumineux (>100MB) - Envisager archivage")
    
    if report['file_counts'].get('debug_X.html', 0) > 20:
        report['recommendations'].append("Trop de fichiers debug - Nettoyer régulièrement")
    
    # Sauvegarder rapport
    report_path = logs_dir / "maintenance_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    log(f"📊 Rapport sauvé: {report_path}", Colors.GREEN)
    return report

def print_summary(stats: Dict[str, Dict[str, int]]):
    """Affiche un résumé des opérations"""
    log("📊 RÉSUMÉ DES OPÉRATIONS", Colors.BOLD)
    log("=" * 50, Colors.MAGENTA)
    
    total_removed = sum(s.get('removed', 0) for s in stats.values())
    total_archived = sum(s.get('archived', 0) for s in stats.values())
    total_size = sum(s.get('size_mb', 0) for s in stats.values())
    
    log(f"📁 Fichiers supprimés: {total_removed}", Colors.GREEN)
    log(f"📦 Fichiers archivés: {total_archived}", Colors.BLUE)
    log(f"💾 Espace libéré: {total_size:.1f} MB", Colors.CYAN)
    
    if stats:
        log("\nDétails par opération:", Colors.YELLOW)
        for operation, data in stats.items():
            log(f"  • {operation}: {data.get('removed', 0)} fichiers ({data.get('size_mb', 0):.1f} MB)")

def main():
    parser = argparse.ArgumentParser(description="Maintenance et nettoyage du scraper")
    parser.add_argument('--archive-days', type=int, default=7, help='Archiver les fichiers de plus de N jours')
    parser.add_argument('--max-debug', type=int, default=10, help='Nombre max de fichiers debug à garder')
    parser.add_argument('--dry-run', action='store_true', help='Simulation sans modifications')
    parser.add_argument('--report-only', action='store_true', help='Générer seulement le rapport')
    args = parser.parse_args()
    
    logs_dir = Path(__file__).resolve().parents[1] / "logs"
    
    if not logs_dir.exists():
        log("❌ Dossier logs/ introuvable", Colors.YELLOW)
        return 1
    
    log("🧹 MAINTENANCE DU SCRAPER", Colors.BOLD)
    log("=" * 40, Colors.MAGENTA)
    
    # Taille initiale
    initial_size = get_directory_size_mb(logs_dir)
    log(f"📊 Taille initiale: {initial_size:.1f} MB", Colors.CYAN)
    
    stats = {}
    
    if not args.report_only:
        if args.dry_run:
            log("🔍 MODE SIMULATION (aucun fichier ne sera modifié)", Colors.YELLOW)
            return 0
        
        # Opérations de nettoyage
        stats['archivage'] = archive_old_files(logs_dir, args.archive_days)
        stats['doublons_preview'] = clean_duplicate_previews(logs_dir)
        stats['debug_files'] = clean_debug_files(logs_dir, args.max_debug)
        stats['fichiers_vides'] = cleanup_empty_files(logs_dir)
        
        # Taille finale
        final_size = get_directory_size_mb(logs_dir)
        log(f"📊 Taille finale: {final_size:.1f} MB", Colors.CYAN)
        log(f"💾 Espace libéré: {initial_size - final_size:.1f} MB", Colors.GREEN)
        
        print_summary(stats)
    
    # Rapport de maintenance
    report = generate_maintenance_report(logs_dir)
    
    log("✅ Maintenance terminée!", Colors.GREEN)
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
