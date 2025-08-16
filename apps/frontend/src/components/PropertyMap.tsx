'use client';

import { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Configuration des icônes Leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

interface PropertyMapData {
  id: string;
  title: string;
  price: number;
  property_type: string;
  address: string;
  latitude: number;
  longitude: number;
  area_sqm?: number;
  bedrooms?: number;
  bathrooms?: number;
  url?: string;
}

interface PropertyMapProps {
  listings: PropertyMapData[];
  selectedListingId?: string;
  onMarkerClick?: (listing: PropertyMapData) => void;
  height?: string;
  className?: string;
}

// Composant pour ajuster la vue de la carte
function MapController({ listings, selectedListingId }: { listings: PropertyMapData[]; selectedListingId?: string }) {
  const map = useMap();

  useEffect(() => {
    if (listings.length > 0) {
      // Créer un groupe de tous les marqueurs pour ajuster la vue
      const group = new L.FeatureGroup(
        listings
          .filter(listing => listing.latitude && listing.longitude)
          .map(listing => L.marker([listing.latitude, listing.longitude]))
      );

      if (group.getLayers().length > 0) {
        map.fitBounds(group.getBounds(), { padding: [20, 20] });
      }
    }
  }, [listings, map]);

  useEffect(() => {
    if (selectedListingId) {
      const selectedListing = listings.find(l => l.id === selectedListingId);
      if (selectedListing && selectedListing.latitude && selectedListing.longitude) {
        map.setView([selectedListing.latitude, selectedListing.longitude], 15);
      }
    }
  }, [selectedListingId, listings, map]);

  return null;
}

// Icônes personnalisées selon le type de propriété
const getPropertyIcon = (propertyType: string, price: number) => {
  const getPriceColor = (price: number) => {
    if (price < 300000) return '#22c55e'; // vert
    if (price < 500000) return '#f59e0b'; // orange
    if (price < 700000) return '#ef4444'; // rouge
    return '#8b5cf6'; // violet pour les plus chers
  };

  const getTypeIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'house':
      case 'maison':
        return '🏠';
      case 'condo':
      case 'apartment':
      case 'appartement':
        return '🏢';
      case 'townhouse':
        return '🏘️';
      default:
        return '🏠';
    }
  };

  const color = getPriceColor(price);
  const icon = getTypeIcon(propertyType);

  return L.divIcon({
    html: `
      <div style="
        background-color: ${color};
        width: 40px;
        height: 40px;
        border-radius: 50%;
        border: 3px solid white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
      ">
        ${icon}
      </div>
    `,
    className: 'custom-marker',
    iconSize: [40, 40],
    iconAnchor: [20, 20],
    popupAnchor: [0, -20],
  });
};

export default function PropertyMap({ 
  listings, 
  selectedListingId, 
  onMarkerClick,
  height = '500px',
  className = ''
}: PropertyMapProps) {
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  if (!isClient) {
    return (
      <div className={`flex items-center justify-center bg-gray-100 rounded-lg ${className}`} style={{ height }}>
        <div className="text-gray-500">Chargement de la carte...</div>
      </div>
    );
  }

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('fr-CA', {
      style: 'currency',
      currency: 'CAD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(price);
  };

  // Filtrer les annonces avec coordonnées valides
  const validListings = listings.filter(
    listing => listing.latitude && listing.longitude && 
    !isNaN(listing.latitude) && !isNaN(listing.longitude)
  );

  if (validListings.length === 0) {
    return (
      <div className={`flex items-center justify-center bg-gray-100 rounded-lg ${className}`} style={{ height }}>
        <div className="text-center text-gray-500">
          <div className="mb-2">📍</div>
          <div>Aucune propriété avec coordonnées disponible</div>
        </div>
      </div>
    );
  }

  // Position par défaut (centre de Montréal)
  const defaultCenter: [number, number] = [45.5017, -73.5673];

  return (
    <div className={`relative rounded-lg overflow-hidden ${className}`} style={{ height }}>
      <MapContainer
        center={defaultCenter}
        zoom={11}
        style={{ height: '100%', width: '100%' }}
        className="z-0"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        <MapController listings={validListings} selectedListingId={selectedListingId} />

        {validListings.map((listing) => (
          <Marker
            key={listing.id}
            position={[listing.latitude, listing.longitude]}
            icon={getPropertyIcon(listing.property_type, listing.price)}
            eventHandlers={{
              click: () => onMarkerClick?.(listing),
            }}
          >
            <Popup maxWidth={300} className="custom-popup">
              <div className="p-2">
                <h3 className="font-semibold text-lg mb-2 text-gray-900">
                  {listing.title}
                </h3>
                
                <div className="space-y-1 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-xl text-blue-600">
                      {formatPrice(listing.price)}
                    </span>
                    <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
                      {listing.property_type}
                    </span>
                  </div>
                  
                  <div className="text-gray-600">
                    📍 {listing.address}
                  </div>
                  
                  {(listing.bedrooms || listing.area_sqm || listing.bathrooms) && (
                    <div className="flex gap-3 text-gray-500 mt-2">
                      {listing.bedrooms && (
                        <span>🛏️ {listing.bedrooms} ch.</span>
                      )}
                      {listing.bathrooms && (
                        <span>🚿 {listing.bathrooms} sdb.</span>
                      )}
                      {listing.area_sqm && (
                        <span>📐 {listing.area_sqm} m²</span>
                      )}
                    </div>
                  )}
                  
                  {listing.url && (
                    <div className="mt-3">
                      <a
                        href={listing.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-block bg-blue-600 text-white px-3 py-1 rounded text-xs hover:bg-blue-700 transition-colors"
                      >
                        Voir l'annonce →
                      </a>
                    </div>
                  )}
                </div>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
      
      {/* Légende */}
      <div className="absolute bottom-4 left-4 bg-white rounded-lg shadow-lg p-3 z-10">
        <h4 className="font-semibold text-sm mb-2">Prix</h4>
        <div className="space-y-1 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-green-500"></div>
            <span>&lt; 300k CAD</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-orange-500"></div>
            <span>300k - 500k CAD</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-red-500"></div>
            <span>500k - 700k CAD</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-purple-500"></div>
            <span>&gt; 700k CAD</span>
          </div>
        </div>
      </div>
    </div>
  );
}
