'use client';

import { useQuery } from '@tanstack/react-query';
import Header from '@/components/Header';
import StatsCards from '@/components/StatsCards';
import FilterPanel from '@/components/FilterPanel';
import ListingsList from '@/components/ListingsList';
import AdvancedSearch from '@/components/AdvancedSearch';
import PropertyComparison from '@/components/PropertyComparison';
import { useState } from 'react';
import { ArrowLeftRight, BarChart3 } from 'lucide-react';
import Link from 'next/link';

interface Listing {
  id: number;
  title: string;
  description?: string;
  price: number;
  location: string;
  property_type: string;
  rooms?: number;
  surface?: number;
  url: string;
  created_at: string;
  updated_at: string;
}

interface SearchFilters {
  query: string;
  minPrice: string;
  maxPrice: string;
  propertyType: string;
  minRooms: string;
  maxRooms: string;
  minSurface: string;
  maxSurface: string;
  location: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001';

// Mock data enrichi pour développement
const mockListings: Listing[] = [
  {
    id: 1,
    title: "Bel appartement 3 pièces avec balcon",
    description: "Magnifique appartement de 75m² situé au 3ème étage avec ascenseur. Exposition sud-ouest, très lumineux. Cuisine équipée, salle de bains avec baignoire.",
    price: 250000,
    location: "Paris 15e",
    property_type: "appartement",
    rooms: 3,
    surface: 75,
    url: "https://example.com/listing/1",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 2,
    title: "Maison individuelle avec jardin",
    description: "Belle maison de 120m² avec jardin de 300m². Garage pour 2 voitures. Quartier calme et résidentiel.",
    price: 450000,
    location: "Boulogne-Billancourt",
    property_type: "maison",
    rooms: 5,
    surface: 120,
    url: "https://example.com/listing/2",
    created_at: new Date(Date.now() - 86400000).toISOString(),
    updated_at: new Date(Date.now() - 86400000).toISOString(),
  },
  {
    id: 3,
    title: "Studio lumineux centre-ville",
    description: "Studio de 25m² entièrement rénové en plein centre. Métro à 2 minutes. Parfait pour investissement locatif.",
    price: 180000,
    location: "Lyon 2e",
    property_type: "studio",
    rooms: 1,
    surface: 25,
    url: "https://example.com/listing/3",
    created_at: new Date(Date.now() - 172800000).toISOString(),
    updated_at: new Date(Date.now() - 172800000).toISOString(),
  },
  {
    id: 4,
    title: "Appartement 2 pièces avec terrasse",
    description: "Charmant T2 avec terrasse de 15m² exposée sud. Calme et lumineux, proche des commerces.",
    price: 320000,
    location: "Nice Centre",
    property_type: "appartement",
    rooms: 2,
    surface: 55,
    url: "https://example.com/listing/4",
    created_at: new Date(Date.now() - 259200000).toISOString(),
    updated_at: new Date(Date.now() - 259200000).toISOString(),
  },
  {
    id: 5,
    title: "Villa avec piscine",
    description: "Superbe villa de 200m² avec piscine et jardin arboré de 800m². Vue mer panoramique.",
    price: 750000,
    location: "Cannes",
    property_type: "maison",
    rooms: 6,
    surface: 200,
    url: "https://example.com/listing/5",
    created_at: new Date(Date.now() - 345600000).toISOString(),
    updated_at: new Date(Date.now() - 345600000).toISOString(),
  },
  {
    id: 6,
    title: "Duplex moderne avec mezzanine",
    description: "Duplex de 90m² avec mezzanine. Design contemporain, matériaux haut de gamme.",
    price: 380000,
    location: "Marseille 8e",
    property_type: "duplex",
    rooms: 4,
    surface: 90,
    url: "https://example.com/listing/6",
    created_at: new Date(Date.now() - 432000000).toISOString(),
    updated_at: new Date(Date.now() - 432000000).toISOString(),
  },
  {
    id: 7,
    title: "Loft industriel atypique",
    description: "Loft de 140m² dans ancienne usine réhabilitée. Volumes exceptionnels, caractère unique.",
    price: 520000,
    location: "Lille Centre",
    property_type: "loft",
    rooms: 3,
    surface: 140,
    url: "https://example.com/listing/7",
    created_at: new Date(Date.now() - 518400000).toISOString(),
    updated_at: new Date(Date.now() - 518400000).toISOString(),
  },
  {
    id: 8,
    title: "Appartement neuf avec parking",
    description: "T3 neuf de 68m² avec parking et cave. Résidence sécurisée, proche transports.",
    price: 290000,
    location: "Toulouse Capitole",
    property_type: "appartement",
    rooms: 3,
    surface: 68,
    url: "https://example.com/listing/8",
    created_at: new Date(Date.now() - 604800000).toISOString(),
    updated_at: new Date(Date.now() - 604800000).toISOString(),
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

// Fonction de filtrage avancée
function filterListings(listings: Listing[], filters: SearchFilters): Listing[] {
  return listings.filter((listing) => {
    // Recherche textuelle
    if (filters.query) {
      const query = filters.query.toLowerCase();
      const searchableText = `${listing.title} ${listing.description} ${listing.location}`.toLowerCase();
      if (!searchableText.includes(query)) return false;
    }

    // Prix
    if (filters.minPrice && listing.price < parseInt(filters.minPrice)) return false;
    if (filters.maxPrice && listing.price > parseInt(filters.maxPrice)) return false;

    // Type de propriété
    if (filters.propertyType && listing.property_type !== filters.propertyType) return false;

    // Localisation
    if (filters.location && !listing.location.toLowerCase().includes(filters.location.toLowerCase())) return false;

    // Nombre de pièces
    if (filters.minRooms && (!listing.rooms || listing.rooms < parseInt(filters.minRooms))) return false;
    if (filters.maxRooms && (!listing.rooms || listing.rooms > parseInt(filters.maxRooms))) return false;

    // Surface
    if (filters.minSurface && (!listing.surface || listing.surface < parseInt(filters.minSurface))) return false;
    if (filters.maxSurface && (!listing.surface || listing.surface > parseInt(filters.maxSurface))) return false;

    return true;
  });
}

export default function Home() {
  const [searchFilters, setSearchFilters] = useState<SearchFilters>({
    query: '',
    minPrice: '',
    maxPrice: '',
    propertyType: '',
    minRooms: '',
    maxRooms: '',
    minSurface: '',
    maxSurface: '',
    location: '',
  });

  const [legacyFilters, setLegacyFilters] = useState({
    search: '',
    propertyType: '',
    minPrice: '',
    maxPrice: '',
    location: '',
  });

  const [showComparison, setShowComparison] = useState(false);

  const { data, isLoading, error } = useQuery({
    queryKey: ['listings'],
    queryFn: fetchListings,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });

  const allListings = data?.listings || [];
  const filteredListings = filterListings(allListings, searchFilters);

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
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Tableau de Bord Immobilier
              </h1>
              <p className="text-gray-600">
                Découvrez les meilleures opportunités immobilières
              </p>
            </div>
            
            <div className="flex gap-3">
              <Link
                href="/analytics"
                className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
              >
                <BarChart3 className="h-4 w-4" />
                Analytics
              </Link>
              
              <Link
                href="/map"
                className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                Carte
              </Link>
              
              <button
                onClick={() => setShowComparison(true)}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <ArrowLeftRight className="h-4 w-4" />
                Comparer
              </button>
            </div>
          </div>
        </div>

        {/* Calculate stats from filtered listings */}
        {(() => {
          const totalListings = filteredListings.length;
          const avgPrice = totalListings > 0 
            ? filteredListings.reduce((sum, listing) => sum + listing.price, 0) / totalListings 
            : 0;
          const newToday = filteredListings.filter(listing => {
            const today = new Date();
            const createdDate = new Date(listing.created_at);
            return createdDate.toDateString() === today.toDateString();
          }).length;
          const avgPricePerM2 = filteredListings
            .filter(listing => listing.surface)
            .reduce((sum, listing) => sum + (listing.price / (listing.surface || 1)), 0) / 
            filteredListings.filter(listing => listing.surface).length || 0;

          return (
            <StatsCards 
              totalListings={totalListings}
              avgPrice={avgPrice}
              newToday={newToday}
              avgPricePerM2={avgPricePerM2}
            />
          );
        })()}

        {/* Recherche avancée */}
        <AdvancedSearch 
          onFiltersChange={setSearchFilters}
          initialFilters={searchFilters}
          listings={allListings}
        />
        
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div className="lg:col-span-1">
            <FilterPanel 
              onFilterChange={setLegacyFilters} 
              totalCount={filteredListings.length}
            />
          </div>
          
          <div className="lg:col-span-3">
            <ListingsList 
              listings={filteredListings} 
              loading={isLoading}
              error={error?.message || null}
            />
          </div>
        </div>

        {/* Statistiques de filtrage */}
        {filteredListings.length !== allListings.length && (
          <div className="mt-6 text-center">
            <p className="text-gray-600">
              Affichage de {filteredListings.length} résultat(s) sur {allListings.length} annonce(s) totale(s)
            </p>
          </div>
        )}

        {/* Modal de comparaison */}
        <PropertyComparison
          listings={allListings}
          isOpen={showComparison}
          onClose={() => setShowComparison(false)}
        />
      </main>
    </div>
  );
}
