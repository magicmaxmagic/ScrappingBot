'use client';

import { useState, useEffect } from 'react';
import { Search, Filter, X, SlidersHorizontal, MapPin, Home, Euro } from 'lucide-react';

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

interface SearchSuggestion {
  type: 'location' | 'property_type' | 'recent';
  value: string;
  icon: React.ReactNode;
  count?: number;
}

interface AdvancedSearchProps {
  onFiltersChange: (filters: SearchFilters) => void;
  initialFilters?: Partial<SearchFilters>;
  listings: any[];
}

export default function AdvancedSearch({ onFiltersChange, initialFilters, listings }: AdvancedSearchProps) {
  const [filters, setFilters] = useState<SearchFilters>({
    query: '',
    minPrice: '',
    maxPrice: '',
    propertyType: '',
    minRooms: '',
    maxRooms: '',
    minSurface: '',
    maxSurface: '',
    location: '',
    ...initialFilters,
  });

  const [showAdvanced, setShowAdvanced] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([]);

  // Générer des suggestions basées sur les données
  useEffect(() => {
    if (!listings || listings.length === 0) return;

    const locationCounts = listings.reduce((acc: any, listing: any) => {
      acc[listing.location] = (acc[listing.location] || 0) + 1;
      return acc;
    }, {});

    const typeCounts = listings.reduce((acc: any, listing: any) => {
      acc[listing.property_type] = (acc[listing.property_type] || 0) + 1;
      return acc;
    }, {});

    const newSuggestions: SearchSuggestion[] = [
      ...Object.entries(locationCounts).map(([location, count]) => ({
        type: 'location' as const,
        value: location,
        icon: <MapPin className="h-4 w-4" />,
        count: count as number,
      })),
      ...Object.entries(typeCounts).map(([type, count]) => ({
        type: 'property_type' as const,
        value: type,
        icon: <Home className="h-4 w-4" />,
        count: count as number,
      })),
    ];

    setSuggestions(newSuggestions.slice(0, 8));
  }, [listings]);

  const updateFilters = (newFilters: Partial<SearchFilters>) => {
    const updatedFilters = { ...filters, ...newFilters };
    setFilters(updatedFilters);
    onFiltersChange(updatedFilters);
  };

  const clearFilters = () => {
    const emptyFilters: SearchFilters = {
      query: '',
      minPrice: '',
      maxPrice: '',
      propertyType: '',
      minRooms: '',
      maxRooms: '',
      minSurface: '',
      maxSurface: '',
      location: '',
    };
    setFilters(emptyFilters);
    onFiltersChange(emptyFilters);
    setShowAdvanced(false);
  };

  const hasActiveFilters = Object.values(filters).some(value => value !== '');

  const applySuggestion = (suggestion: SearchSuggestion) => {
    if (suggestion.type === 'location') {
      updateFilters({ location: suggestion.value });
    } else if (suggestion.type === 'property_type') {
      updateFilters({ propertyType: suggestion.value });
    }
    setShowSuggestions(false);
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
      {/* Barre de recherche principale */}
      <div className="relative mb-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
          <input
            type="text"
            placeholder="Rechercher par titre, description, lieu..."
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            value={filters.query}
            onChange={(e) => updateFilters({ query: e.target.value })}
            onFocus={() => setShowSuggestions(true)}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
          />
        </div>

        {/* Suggestions */}
        {showSuggestions && suggestions.length > 0 && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-50 max-h-64 overflow-y-auto">
            <div className="p-2">
              <h4 className="text-sm font-medium text-gray-500 mb-2">Suggestions</h4>
              {suggestions.map((suggestion, index) => (
                <button
                  key={index}
                  className="w-full flex items-center gap-3 px-3 py-2 text-left hover:bg-gray-50 rounded"
                  onClick={() => applySuggestion(suggestion)}
                >
                  <span className="text-gray-400">{suggestion.icon}</span>
                  <span className="flex-1">{suggestion.value}</span>
                  {suggestion.count && (
                    <span className="text-xs text-gray-400 bg-gray-100 px-2 py-1 rounded">
                      {suggestion.count}
                    </span>
                  )}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Boutons de contrôle */}
      <div className="flex items-center gap-3 mb-4">
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg border transition-colors ${
            showAdvanced
              ? 'bg-blue-50 border-blue-200 text-blue-700'
              : 'bg-gray-50 border-gray-200 text-gray-700 hover:bg-gray-100'
          }`}
        >
          <SlidersHorizontal className="h-4 w-4" />
          Filtres avancés
        </button>

        {hasActiveFilters && (
          <button
            onClick={clearFilters}
            className="flex items-center gap-2 px-4 py-2 rounded-lg border border-red-200 text-red-700 bg-red-50 hover:bg-red-100 transition-colors"
          >
            <X className="h-4 w-4" />
            Effacer
          </button>
        )}

        {hasActiveFilters && (
          <span className="text-sm text-gray-500">
            {Object.values(filters).filter(v => v !== '').length} filtre(s) actif(s)
          </span>
        )}
      </div>

      {/* Filtres avancés */}
      {showAdvanced && (
        <div className="border-t pt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Prix */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Euro className="inline h-4 w-4 mr-1" />
                Prix
              </label>
              <div className="flex gap-2">
                <input
                  type="number"
                  placeholder="Min"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  value={filters.minPrice}
                  onChange={(e) => updateFilters({ minPrice: e.target.value })}
                />
                <input
                  type="number"
                  placeholder="Max"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  value={filters.maxPrice}
                  onChange={(e) => updateFilters({ maxPrice: e.target.value })}
                />
              </div>
            </div>

            {/* Type de bien */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Home className="inline h-4 w-4 mr-1" />
                Type de bien
              </label>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                value={filters.propertyType}
                onChange={(e) => updateFilters({ propertyType: e.target.value })}
              >
                <option value="">Tous les types</option>
                <option value="appartement">Appartement</option>
                <option value="maison">Maison</option>
                <option value="studio">Studio</option>
                <option value="villa">Villa</option>
                <option value="duplex">Duplex</option>
                <option value="loft">Loft</option>
              </select>
            </div>

            {/* Localisation */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <MapPin className="inline h-4 w-4 mr-1" />
                Localisation
              </label>
              <input
                type="text"
                placeholder="Ville, quartier..."
                className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                value={filters.location}
                onChange={(e) => updateFilters({ location: e.target.value })}
              />
            </div>

            {/* Nombre de pièces */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Nombre de pièces
              </label>
              <div className="flex gap-2">
                <input
                  type="number"
                  placeholder="Min"
                  min="1"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  value={filters.minRooms}
                  onChange={(e) => updateFilters({ minRooms: e.target.value })}
                />
                <input
                  type="number"
                  placeholder="Max"
                  min="1"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  value={filters.maxRooms}
                  onChange={(e) => updateFilters({ maxRooms: e.target.value })}
                />
              </div>
            </div>

            {/* Surface */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Surface (m²)
              </label>
              <div className="flex gap-2">
                <input
                  type="number"
                  placeholder="Min"
                  min="1"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  value={filters.minSurface}
                  onChange={(e) => updateFilters({ minSurface: e.target.value })}
                />
                <input
                  type="number"
                  placeholder="Max"
                  min="1"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  value={filters.maxSurface}
                  onChange={(e) => updateFilters({ maxSurface: e.target.value })}
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
