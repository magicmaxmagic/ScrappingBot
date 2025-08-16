// Client-side page (map uses Leaflet which depends on window/document)
'use client';

import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import Header from '@/components/Header';
import nextDynamic from 'next/dynamic';
// Charger la carte dynamiquement côté client uniquement pour éviter "window is not defined" au build
const PropertyMap = nextDynamic(() => import('@/components/PropertyMap'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center bg-gray-100 rounded-lg h-full min-h-[300px]">
      <div className="text-gray-500">Chargement de la carte…</div>
    </div>
  ),
});
import { ArrowLeft, Map, List, Filter, Search } from 'lucide-react';
import Link from 'next/link';

interface Listing {
  id: string;
  title: string;
  price: number;
  property_type: string;
  address: string;
  area_sqm?: number;
  bedrooms?: number;
  bathrooms?: number;
  latitude?: number;
  longitude?: number;
  url?: string;
  created_at: string;
  updated_at: string;
}

// Utiliser l'URL fournie via variable d'environnement (dans Docker: http://backend:3001)
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001';

// Forcer le rendu dynamique pour empêcher toute tentative de pré-rendu statique qui exécuterait du code Leaflet côté serveur
// Indiquer à Next que la page est dynamique
export const fetchCache = 'force-no-store';

// Mock data avec coordonnées de Montréal
const mockListings: Listing[] = [
  {
    id: '1',
    title: 'Superbe condo 2BR dans Ville-Marie',
    price: 450000,
    property_type: 'Condo',
    address: '1234 Rue Saint-Denis, Ville-Marie, QC',
    area_sqm: 85,
    bedrooms: 2,
    bathrooms: 1,
    latitude: 45.5088,
    longitude: -73.5878,
    url: 'https://example.com/listing/1',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: '2',
    title: 'Appartement 3BR Plateau-Mont-Royal',
    price: 525000,
    property_type: 'Apartment',
    address: '5678 Boulevard Saint-Laurent, Le Plateau-Mont-Royal, QC',
    area_sqm: 120,
    bedrooms: 3,
    bathrooms: 2,
    latitude: 45.5276,
    longitude: -73.5825,
    url: 'https://example.com/listing/2',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: '3',
    title: 'Maison 4BR Outremont',
    price: 850000,
    property_type: 'House',
    address: '9876 Avenue du Parc, Outremont, QC',
    area_sqm: 200,
    bedrooms: 4,
    bathrooms: 3,
    latitude: 45.5234,
    longitude: -73.6078,
    url: 'https://example.com/listing/3',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: '4',
    title: 'Loft 1BR Griffintown',
    price: 320000,
    property_type: 'Condo',
    address: '1111 Rue Notre-Dame, Le Sud-Ouest, QC',
    area_sqm: 60,
    bedrooms: 1,
    bathrooms: 1,
    latitude: 45.4942,
    longitude: -73.5597,
    url: 'https://example.com/listing/4',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: '5',
    title: 'Townhouse 3BR Verdun',
    price: 475000,
    property_type: 'Townhouse',
    address: '2222 Rue Wellington, Verdun, QC',
    area_sqm: 140,
    bedrooms: 3,
    bathrooms: 2,
    latitude: 45.4533,
    longitude: -73.5673,
    url: 'https://example.com/listing/5',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

async function fetchListings() {
  try {
    const response = await fetch(`${API_URL}/listings`);
    if (!response.ok) {
      throw new Error('Failed to fetch listings');
    }
    return response.json();
  } catch (error) {
    console.warn('API not available, using mock data');
    return {
      listings: mockListings,
      total: mockListings.length,
    };
  }
}

export default function MapPage() {
  const [selectedListingId, setSelectedListingId] = useState<string>();
  const [showSidebar, setShowSidebar] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [priceFilter, setPriceFilter] = useState({ min: '', max: '' });
  const [typeFilter, setTypeFilter] = useState('');

  const { data, isLoading, error } = useQuery({
    queryKey: ['map-listings'],
    queryFn: fetchListings,
    staleTime: 1000 * 60 * 5,
  });

  const allListings = data?.listings || [];

  // Filtrage des annonces
  const filteredListings = allListings.filter((listing: Listing) => {
    const matchesSearch = !searchTerm || 
      listing.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      listing.address.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesPrice = 
      (!priceFilter.min || listing.price >= parseInt(priceFilter.min)) &&
      (!priceFilter.max || listing.price <= parseInt(priceFilter.max));
    
    const matchesType = !typeFilter || listing.property_type === typeFilter;

    return matchesSearch && matchesPrice && matchesType;
  });

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('fr-CA', {
      style: 'currency',
      currency: 'CAD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(price);
  };

  const handleMarkerClick = (listing: any) => {
    setSelectedListingId(listing.id);
  };

  const handleListingClick = (listingId: string) => {
    setSelectedListingId(listingId);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <main className="max-w-full">
        {/* Navigation */}
        <div className="bg-white border-b px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link 
                href="/"
                className="flex items-center text-blue-600 hover:text-blue-800 transition-colors"
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Retour
              </Link>
              
              <h1 className="text-2xl font-bold text-gray-900">
                Carte des Propriétés
              </h1>
              
              <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm">
                {filteredListings.length} propriété(s)
              </span>
            </div>

            <button
              onClick={() => setShowSidebar(!showSidebar)}
              className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            >
              {showSidebar ? <Map className="h-4 w-4" /> : <List className="h-4 w-4" />}
              {showSidebar ? 'Plein écran' : 'Afficher la liste'}
            </button>
          </div>
        </div>

        <div className="flex h-[calc(100vh-140px)]">
          {/* Sidebar avec liste et filtres */}
          {showSidebar && (
            <div className="w-96 bg-white border-r overflow-y-auto">
              {/* Filtres */}
              <div className="p-4 border-b">
                <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <Filter className="h-4 w-4" />
                  Filtres
                </h3>
                
                {/* Recherche */}
                <div className="mb-4">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                    <input
                      type="text"
                      placeholder="Rechercher..."
                      className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                    />
                  </div>
                </div>

                {/* Type de propriété */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Type de propriété
                  </label>
                  <select
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    value={typeFilter}
                    onChange={(e) => setTypeFilter(e.target.value)}
                  >
                    <option value="">Tous les types</option>
                    <option value="House">Maison</option>
                    <option value="Condo">Condo</option>
                    <option value="Apartment">Appartement</option>
                    <option value="Townhouse">Maison de ville</option>
                  </select>
                </div>

                {/* Prix */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Prix (CAD)
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="number"
                      placeholder="Min"
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      value={priceFilter.min}
                      onChange={(e) => setPriceFilter(prev => ({ ...prev, min: e.target.value }))}
                    />
                    <input
                      type="number"
                      placeholder="Max"
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      value={priceFilter.max}
                      onChange={(e) => setPriceFilter(prev => ({ ...prev, max: e.target.value }))}
                    />
                  </div>
                </div>
              </div>

              {/* Liste des propriétés */}
              <div className="p-4">
                <h3 className="font-semibold text-gray-900 mb-3">
                  Propriétés ({filteredListings.length})
                </h3>
                
                <div className="space-y-3">
                  {filteredListings.map((listing: Listing) => (
                    <div
                      key={listing.id}
                      className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                        selectedListingId === listing.id
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                      }`}
                      onClick={() => handleListingClick(listing.id)}
                    >
                      <h4 className="font-medium text-gray-900 text-sm mb-1">
                        {listing.title}
                      </h4>
                      
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-semibold text-blue-600">
                          {formatPrice(listing.price)}
                        </span>
                        <span className="bg-gray-100 text-gray-700 px-2 py-1 rounded text-xs">
                          {listing.property_type}
                        </span>
                      </div>
                      
                      <p className="text-xs text-gray-500 mb-2">
                        {listing.address}
                      </p>
                      
                      {(listing.bedrooms || listing.area_sqm) && (
                        <div className="flex gap-3 text-xs text-gray-500">
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
                    </div>
                  ))}
                  
                  {filteredListings.length === 0 && (
                    <div className="text-center py-8 text-gray-500">
                      <Map className="h-12 w-12 mx-auto mb-2 opacity-50" />
                      <p>Aucune propriété trouvée</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Carte */}
          <div className="flex-1">
            <PropertyMap
              listings={filteredListings}
              selectedListingId={selectedListingId}
              onMarkerClick={handleMarkerClick}
              height="100%"
              className="h-full"
            />
          </div>
        </div>
      </main>
    </div>
  );
}
