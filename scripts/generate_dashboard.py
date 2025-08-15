#!/usr/bin/env python3
"""
Dashboard de visualisation des résultats de scraping
Génère des rapports HTML avec cartes, graphiques et métriques
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any
import argparse

def load_preview_files() -> Dict[str, Any]:
    """Charge tous les fichiers preview_*.json"""
    logs_dir = Path(__file__).resolve().parents[1] / "logs"
    previews = {}
    
    for file in logs_dir.glob("preview_*.json"):
        source = file.stem.replace("preview_", "")
        try:
            with open(file, 'r', encoding='utf-8') as f:
                previews[source] = json.load(f)
        except Exception as e:
            print(f"Erreur lecture {file}: {e}")
    
    return previews

def generate_map_data(previews: Dict[str, Any]) -> str:
    """Génère les données JavaScript pour la carte"""
    markers = []
    
    for source, data in previews.items():
        if not data.get('blocked', True) and data.get('preview'):
            for listing in data['preview']:
                if listing.get('address') and listing.get('price'):
                    # Coordonnées approximatives pour Montréal/Lachine
                    lat = 45.445 + (hash(listing['address']) % 100) * 0.001
                    lon = -73.675 + (hash(listing['address']) % 100) * 0.001
                    
                    markers.append({
                        'lat': lat,
                        'lon': lon,
                        'price': listing['price'],
                        'address': listing['address'],
                        'source': source,
                        'url': listing.get('url', '#')
                    })
    
    return json.dumps(markers)

def generate_html_dashboard(previews: Dict[str, Any]) -> str:
    """Génère le dashboard HTML complet"""
    
    # Stats globales
    total_listings = sum(p.get('count', 0) for p in previews.values())
    total_sources = len(previews)
    blocked_sources = sum(1 for p in previews.values() if p.get('blocked', True))
    successful_sources = total_sources - blocked_sources
    
    # Prix moyen
    all_prices = []
    for data in previews.values():
        if not data.get('blocked') and data.get('preview'):
            for listing in data['preview']:
                if isinstance(listing.get('price'), (int, float)):
                    all_prices.append(listing['price'])
    
    avg_price = sum(all_prices) / len(all_prices) if all_prices else 0
    min_price = min(all_prices) if all_prices else 0
    max_price = max(all_prices) if all_prices else 0
    
    # Données pour la carte
    map_data = generate_map_data(previews)
    
    # Génération du HTML
    html = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ScrappingBot Dashboard</title>
    <link href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" rel="stylesheet" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui; 
            background: #f8fafc;
            color: #1e293b;
        }}
        .header {{ 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; 
            padding: 2rem;
            text-align: center;
        }}
        .header h1 {{ font-size: 2.5rem; margin-bottom: 0.5rem; }}
        .header p {{ opacity: 0.9; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem; }}
        .stats-grid {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
            gap: 1rem; 
            margin-bottom: 2rem;
        }}
        .stat-card {{ 
            background: white; 
            padding: 1.5rem; 
            border-radius: 12px; 
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .stat-card h3 {{ color: #64748b; font-size: 0.9rem; text-transform: uppercase; }}
        .stat-card .value {{ font-size: 2rem; font-weight: bold; margin: 0.5rem 0; }}
        .stat-card.success .value {{ color: #10b981; }}
        .stat-card.warning .value {{ color: #f59e0b; }}
        .stat-card.danger .value {{ color: #ef4444; }}
        .stat-card.info .value {{ color: #3b82f6; }}
        
        .content-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; }}
        .panel {{ background: white; border-radius: 12px; padding: 1.5rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }}
        .panel h2 {{ margin-bottom: 1rem; color: #1e293b; }}
        
        #map {{ height: 400px; border-radius: 8px; }}
        
        .source-list {{ max-height: 400px; overflow-y: auto; }}
        .source-item {{ 
            padding: 1rem; 
            border-bottom: 1px solid #e2e8f0; 
            display: flex; 
            justify-content: between;
            align-items: center;
        }}
        .source-status {{ 
            padding: 0.25rem 0.75rem; 
            border-radius: 20px; 
            font-size: 0.8rem; 
            font-weight: 600;
        }}
        .status-success {{ background: #dcfce7; color: #166534; }}
        .status-blocked {{ background: #fee2e2; color: #991b1b; }}
        .status-error {{ background: #fef3c7; color: #92400e; }}
        
        .listing-preview {{ 
            max-height: 300px; 
            overflow-y: auto; 
            background: #f1f5f9; 
            padding: 1rem; 
            border-radius: 8px; 
        }}
        .listing-item {{ 
            background: white; 
            padding: 0.75rem; 
            margin-bottom: 0.5rem; 
            border-radius: 6px; 
            font-size: 0.9rem;
        }}
        .listing-price {{ font-weight: bold; color: #059669; }}
        .listing-address {{ color: #64748b; margin-top: 0.25rem; }}
        
        @media (max-width: 768px) {{
            .content-grid {{ grid-template-columns: 1fr; }}
            .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🏠 ScrappingBot Dashboard</h1>
        <p>Visualisation en temps réel des données immobilières scrapées</p>
        <p><small>Dernière mise à jour: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</small></p>
    </div>
    
    <div class="container">
        <!-- Stats principales -->
        <div class="stats-grid">
            <div class="stat-card success">
                <h3>Total Listings</h3>
                <div class="value">{total_listings:,}</div>
            </div>
            <div class="stat-card info">
                <h3>Sources Actives</h3>
                <div class="value">{successful_sources}/{total_sources}</div>
            </div>
            <div class="stat-card warning">
                <h3>Prix Moyen</h3>
                <div class="value">{avg_price:,.0f}$</div>
            </div>
            <div class="stat-card danger">
                <h3>Sources Bloquées</h3>
                <div class="value">{blocked_sources}</div>
            </div>
        </div>
        
        <div class="content-grid">
            <!-- Carte interactive -->
            <div class="panel">
                <h2>🗺️ Carte des Listings</h2>
                <div id="map"></div>
            </div>
            
            <!-- Sources et statuts -->
            <div class="panel">
                <h2>📊 État des Sources</h2>
                <div class="source-list">
"""
    
    # Ajout des sources
    for source, data in previews.items():
        strategy = data.get('strategy', 'unknown')
        count = data.get('count', 0)
        blocked = data.get('blocked', True)
        elapsed = data.get('elapsed_sec', 0)
        
        if blocked:
            status_class = "status-blocked"
            status_text = "BLOQUÉ"
        elif count > 0:
            status_class = "status-success"
            status_text = f"{count} items"
        else:
            status_class = "status-error" 
            status_text = "VIDE"
            
        html += f"""
                    <div class="source-item">
                        <div>
                            <strong>{source}</strong><br>
                            <small>Stratégie: {strategy} • {elapsed:.1f}s</small>
                        </div>
                        <span class="source-status {status_class}">{status_text}</span>
                    </div>
        """
    
    html += """
                </div>
            </div>
        </div>
        
        <!-- Aperçu des listings -->
        <div class="panel" style="margin-top: 2rem;">
            <h2>🏘️ Aperçu des Listings</h2>
            <div class="listing-preview">
"""
    
    # Ajout des listings
    all_listings = []
    for source, data in previews.items():
        if not data.get('blocked') and data.get('preview'):
            for listing in data['preview'][:5]:  # Max 5 par source
                listing['_source'] = source
                all_listings.append(listing)
    
    # Tri par prix décroissant
    all_listings.sort(key=lambda x: x.get('price', 0), reverse=True)
    
    for listing in all_listings[:20]:  # Max 20 total
        price_str = f"{listing.get('price', 0):,}$" if listing.get('price') else "Prix non spécifié"
        html += f"""
                <div class="listing-item">
                    <div class="listing-price">{price_str}</div>
                    <div class="listing-address">{listing.get('address', 'Adresse non spécifiée')}</div>
                    <small>Source: {listing.get('_source', 'unknown')} • Chambres: {listing.get('bedrooms', '?')} • Bains: {listing.get('bathrooms', '?')}</small>
                </div>
        """
    
    html += f"""
            </div>
        </div>
        
        <!-- Statistiques détaillées -->
        <div class="panel" style="margin-top: 2rem;">
            <h2>📈 Statistiques</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                <div style="text-align: center;">
                    <h4>Prix Min</h4>
                    <p style="font-size: 1.5rem; color: #059669;">{min_price:,.0f}$</p>
                </div>
                <div style="text-align: center;">
                    <h4>Prix Max</h4>
                    <p style="font-size: 1.5rem; color: #dc2626;">{max_price:,.0f}$</p>
                </div>
                <div style="text-align: center;">
                    <h4>Total Listings</h4>
                    <p style="font-size: 1.5rem; color: #2563eb;">{len(all_listings)}</p>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Initialisation de la carte
        const map = L.map('map').setView([45.445, -73.675], 11);
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '© OpenStreetMap contributors'
        }}).addTo(map);
        
        // Données des marqueurs
        const markers = {map_data};
        
        // Ajout des marqueurs sur la carte
        markers.forEach(marker => {{
            const popup = `
                <b>${{marker.price.toLocaleString()}}$</b><br>
                ${{marker.address}}<br>
                <small>Source: ${{marker.source}}</small>
            `;
            
            L.marker([marker.lat, marker.lon])
                .addTo(map)
                .bindPopup(popup);
        }});
        
        // Auto-refresh toutes les 30 secondes
        setInterval(() => {{
            location.reload();
        }}, 30000);
    </script>
</body>
</html>
    """
    
    return html

def main():
    parser = argparse.ArgumentParser(description="Générateur de dashboard de scraping")
    parser.add_argument('--output', default='logs/dashboard.html', help='Fichier de sortie HTML')
    args = parser.parse_args()
    
    print("🔍 Chargement des données de preview...")
    previews = load_preview_files()
    
    if not previews:
        print("❌ Aucun fichier preview trouvé dans logs/")
        return 1
    
    print(f"📊 Génération du dashboard pour {len(previews)} sources...")
    html = generate_html_dashboard(previews)
    
    # Écriture du fichier
    output_path = Path(__file__).resolve().parents[1] / args.output
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(html, encoding='utf-8')
    
    print(f"✅ Dashboard généré: {output_path}")
    print(f"🌐 Ouvrir: file://{output_path}")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
