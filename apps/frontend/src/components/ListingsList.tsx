import { useState } from 'react';
import { ExternalLink, MapPin, Home, Calendar, Euro } from 'lucide-react';

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

interface ListingsListProps {
  listings: Listing[];
  loading: boolean;
  error: string | null;
}

export default function ListingsList({ listings, loading, error }: ListingsListProps) {
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(price);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  };

  const truncateDescription = (description: string, maxLength: number = 150) => {
    if (!description) return '';
    return description.length > maxLength 
      ? description.substring(0, maxLength) + '...'
      : description;
  };

  if (loading) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="text-center text-red-600">
          <p>Erreur lors du chargement des annonces: {error}</p>
        </div>
      </div>
    );
  }

  if (listings.length === 0) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="text-center text-gray-500">
          <Home className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">Aucune annonce</h3>
          <p className="mt-1 text-sm text-gray-500">
            Aucune annonce ne correspond à vos critères de recherche.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg">
      {/* Header with view toggle */}
      <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
        <h3 className="text-lg font-medium text-gray-900">
          {listings.length} annonce{listings.length > 1 ? 's' : ''}
        </h3>
        <div className="flex bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setViewMode('grid')}
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              viewMode === 'grid'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Grille
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              viewMode === 'list'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Liste
          </button>
        </div>
      </div>

      {/* Listings */}
      <div className="p-6">
        {viewMode === 'grid' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {listings.map((listing) => (
              <div
                key={listing.id}
                className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className="space-y-3">
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 line-clamp-2">
                      {listing.title}
                    </h4>
                    <p className="text-xs text-gray-500 mt-1">
                      {truncateDescription(listing.description || '', 100)}
                    </p>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-lg font-bold text-blue-600">
                      {formatPrice(listing.price)}
                    </span>
                    <span className="text-xs bg-gray-100 text-gray-800 px-2 py-1 rounded">
                      {listing.property_type}
                    </span>
                  </div>

                  <div className="space-y-1">
                    <div className="flex items-center text-xs text-gray-500">
                      <MapPin className="h-3 w-3 mr-1" />
                      {listing.location}
                    </div>
                    {listing.rooms && (
                      <div className="flex items-center text-xs text-gray-500">
                        <Home className="h-3 w-3 mr-1" />
                        {listing.rooms} pièce{listing.rooms > 1 ? 's' : ''}
                        {listing.surface && ` • ${listing.surface}m²`}
                      </div>
                    )}
                    <div className="flex items-center text-xs text-gray-500">
                      <Calendar className="h-3 w-3 mr-1" />
                      {formatDate(listing.created_at)}
                    </div>
                  </div>

                  <a
                    href={listing.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="w-full bg-blue-600 text-white px-3 py-2 rounded text-xs font-medium hover:bg-blue-700 transition-colors flex items-center justify-center"
                  >
                    <ExternalLink className="h-3 w-3 mr-1" />
                    Voir l'annonce
                  </a>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="space-y-4">
            {listings.map((listing) => (
              <div
                key={listing.id}
                className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1 space-y-2">
                    <h4 className="text-base font-medium text-gray-900">
                      {listing.title}
                    </h4>
                    <p className="text-sm text-gray-600">
                      {truncateDescription(listing.description || '', 200)}
                    </p>
                    <div className="flex items-center space-x-4 text-sm text-gray-500">
                      <div className="flex items-center">
                        <MapPin className="h-4 w-4 mr-1" />
                        {listing.location}
                      </div>
                      <span className="bg-gray-100 text-gray-800 px-2 py-1 rounded text-xs">
                        {listing.property_type}
                      </span>
                      {listing.rooms && (
                        <div className="flex items-center">
                          <Home className="h-4 w-4 mr-1" />
                          {listing.rooms} pièce{listing.rooms > 1 ? 's' : ''}
                        </div>
                      )}
                      {listing.surface && (
                        <span>{listing.surface}m²</span>
                      )}
                      <div className="flex items-center">
                        <Calendar className="h-4 w-4 mr-1" />
                        {formatDate(listing.created_at)}
                      </div>
                    </div>
                  </div>
                  <div className="ml-6 flex flex-col items-end space-y-2">
                    <span className="text-xl font-bold text-blue-600">
                      {formatPrice(listing.price)}
                    </span>
                    <a
                      href={listing.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="bg-blue-600 text-white px-4 py-2 rounded text-sm font-medium hover:bg-blue-700 transition-colors flex items-center"
                    >
                      <ExternalLink className="h-4 w-4 mr-1" />
                      Voir l'annonce
                    </a>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
