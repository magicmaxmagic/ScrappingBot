'use client';

import { useState } from 'react';
import { X, Plus, TrendingUp, TrendingDown, Minus, Euro, Home, MapPin, Ruler } from 'lucide-react';
import { toast } from 'react-hot-toast';

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

interface PropertyComparisonProps {
  listings: Listing[];
  isOpen: boolean;
  onClose: () => void;
}

export default function PropertyComparison({ listings, isOpen, onClose }: PropertyComparisonProps) {
  const [selectedProperties, setSelectedProperties] = useState<Listing[]>([]);
  const [showAddModal, setShowAddModal] = useState(false);

  if (!isOpen) return null;

  const addProperty = (property: Listing) => {
    if (selectedProperties.length >= 4) {
      toast.error('Maximum 4 propriétés en comparaison');
      return;
    }
    
    if (selectedProperties.find(p => p.id === property.id)) {
      toast.error('Cette propriété est déjà en comparaison');
      return;
    }

    setSelectedProperties([...selectedProperties, property]);
    setShowAddModal(false);
    toast.success('Propriété ajoutée à la comparaison');
  };

  const removeProperty = (propertyId: number) => {
    setSelectedProperties(selectedProperties.filter(p => p.id !== propertyId));
    toast.success('Propriété retirée de la comparaison');
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(price);
  };

  const getPricePerM2 = (listing: Listing) => {
    if (!listing.surface) return null;
    return Math.round(listing.price / listing.surface);
  };

  const getComparisonIndicator = (current: number, others: number[]) => {
    const avg = others.reduce((sum, val) => sum + val, 0) / others.length;
    const difference = ((current - avg) / avg) * 100;
    
    if (Math.abs(difference) < 5) return { icon: <Minus className="h-4 w-4" />, color: 'text-gray-500', text: 'Similaire' };
    if (difference > 0) return { icon: <TrendingUp className="h-4 w-4" />, color: 'text-red-500', text: `+${difference.toFixed(1)}%` };
    return { icon: <TrendingDown className="h-4 w-4" />, color: 'text-green-500', text: `${difference.toFixed(1)}%` };
  };

  const availableProperties = listings.filter(
    listing => !selectedProperties.find(p => p.id === listing.id)
  );

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg max-w-7xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-2xl font-bold text-gray-900">
            Comparaison de Propriétés
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
          {/* Bouton d'ajout */}
          {selectedProperties.length < 4 && (
            <div className="mb-6">
              <button
                onClick={() => setShowAddModal(true)}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Plus className="h-4 w-4" />
                Ajouter une propriété ({selectedProperties.length}/4)
              </button>
            </div>
          )}

          {selectedProperties.length === 0 ? (
            <div className="text-center py-12">
              <Home className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Aucune propriété sélectionnée
              </h3>
              <p className="text-gray-500">
                Ajoutez des propriétés pour commencer la comparaison
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr>
                    <td className="p-4 font-medium text-gray-900 border-b bg-gray-50">
                      Critères
                    </td>
                    {selectedProperties.map((property) => (
                      <td key={property.id} className="p-4 border-b bg-gray-50 min-w-[250px]">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <h3 className="font-medium text-gray-900 text-sm mb-1">
                              {property.title}
                            </h3>
                            <p className="text-xs text-gray-500">
                              {property.location}
                            </p>
                          </div>
                          <button
                            onClick={() => removeProperty(property.id)}
                            className="text-gray-400 hover:text-red-500 transition-colors ml-2"
                          >
                            <X className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {/* Prix */}
                  <tr>
                    <td className="p-4 font-medium text-gray-700 border-b">
                      <div className="flex items-center gap-2">
                        <Euro className="h-4 w-4" />
                        Prix
                      </div>
                    </td>
                    {selectedProperties.map((property) => {
                      const prices = selectedProperties.map(p => p.price);
                      const comparison = getComparisonIndicator(property.price, prices.filter(p => p !== property.price));
                      
                      return (
                        <td key={property.id} className="p-4 border-b">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-lg">
                              {formatPrice(property.price)}
                            </span>
                            {selectedProperties.length > 1 && (
                              <div className={`flex items-center gap-1 text-xs ${comparison.color}`}>
                                {comparison.icon}
                                {comparison.text}
                              </div>
                            )}
                          </div>
                        </td>
                      );
                    })}
                  </tr>

                  {/* Prix au m² */}
                  <tr>
                    <td className="p-4 font-medium text-gray-700 border-b">
                      <div className="flex items-center gap-2">
                        <Ruler className="h-4 w-4" />
                        Prix au m²
                      </div>
                    </td>
                    {selectedProperties.map((property) => {
                      const pricePerM2 = getPricePerM2(property);
                      const prices = selectedProperties
                        .map(p => getPricePerM2(p))
                        .filter(p => p !== null) as number[];
                      
                      return (
                        <td key={property.id} className="p-4 border-b">
                          {pricePerM2 ? (
                            <div className="flex items-center gap-2">
                              <span className="font-semibold">
                                {formatPrice(pricePerM2)}/m²
                              </span>
                              {selectedProperties.length > 1 && prices.length > 1 && (
                                <div className={`flex items-center gap-1 text-xs ${
                                  getComparisonIndicator(pricePerM2, prices.filter(p => p !== pricePerM2)).color
                                }`}>
                                  {getComparisonIndicator(pricePerM2, prices.filter(p => p !== pricePerM2)).icon}
                                </div>
                              )}
                            </div>
                          ) : (
                            <span className="text-gray-400">N/A</span>
                          )}
                        </td>
                      );
                    })}
                  </tr>

                  {/* Type */}
                  <tr>
                    <td className="p-4 font-medium text-gray-700 border-b">
                      <div className="flex items-center gap-2">
                        <Home className="h-4 w-4" />
                        Type
                      </div>
                    </td>
                    {selectedProperties.map((property) => (
                      <td key={property.id} className="p-4 border-b">
                        <span className="capitalize bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm">
                          {property.property_type}
                        </span>
                      </td>
                    ))}
                  </tr>

                  {/* Localisation */}
                  <tr>
                    <td className="p-4 font-medium text-gray-700 border-b">
                      <div className="flex items-center gap-2">
                        <MapPin className="h-4 w-4" />
                        Localisation
                      </div>
                    </td>
                    {selectedProperties.map((property) => (
                      <td key={property.id} className="p-4 border-b">
                        {property.location}
                      </td>
                    ))}
                  </tr>

                  {/* Nombre de pièces */}
                  <tr>
                    <td className="p-4 font-medium text-gray-700 border-b">
                      Nombre de pièces
                    </td>
                    {selectedProperties.map((property) => (
                      <td key={property.id} className="p-4 border-b">
                        {property.rooms ? `${property.rooms} pièces` : 'N/A'}
                      </td>
                    ))}
                  </tr>

                  {/* Surface */}
                  <tr>
                    <td className="p-4 font-medium text-gray-700 border-b">
                      Surface
                    </td>
                    {selectedProperties.map((property) => (
                      <td key={property.id} className="p-4 border-b">
                        {property.surface ? `${property.surface} m²` : 'N/A'}
                      </td>
                    ))}
                  </tr>

                  {/* Description */}
                  <tr>
                    <td className="p-4 font-medium text-gray-700 border-b">
                      Description
                    </td>
                    {selectedProperties.map((property) => (
                      <td key={property.id} className="p-4 border-b">
                        <div className="text-sm text-gray-600 max-w-xs">
                          {property.description || 'Aucune description'}
                        </div>
                      </td>
                    ))}
                  </tr>

                  {/* Lien */}
                  <tr>
                    <td className="p-4 font-medium text-gray-700">
                      Actions
                    </td>
                    {selectedProperties.map((property) => (
                      <td key={property.id} className="p-4">
                        <a
                          href={property.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-block px-3 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
                        >
                          Voir l'annonce
                        </a>
                      </td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Modal d'ajout */}
        {showAddModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-lg max-w-2xl w-full max-h-[80vh] overflow-hidden">
              <div className="flex items-center justify-between p-4 border-b">
                <h3 className="text-lg font-semibold">Ajouter une propriété</h3>
                <button
                  onClick={() => setShowAddModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
              <div className="p-4 overflow-y-auto max-h-[60vh]">
                <div className="grid gap-4">
                  {availableProperties.map((property) => (
                    <div
                      key={property.id}
                      className="border rounded-lg p-4 hover:bg-gray-50 cursor-pointer"
                      onClick={() => addProperty(property)}
                    >
                      <h4 className="font-medium text-gray-900 mb-1">
                        {property.title}
                      </h4>
                      <p className="text-sm text-gray-500 mb-2">
                        {property.location}
                      </p>
                      <div className="flex items-center gap-4 text-sm">
                        <span className="font-semibold text-blue-600">
                          {formatPrice(property.price)}
                        </span>
                        <span className="text-gray-500">
                          {property.property_type}
                        </span>
                        {property.rooms && (
                          <span className="text-gray-500">
                            {property.rooms} pièces
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                  {availableProperties.length === 0 && (
                    <p className="text-center text-gray-500 py-8">
                      Toutes les propriétés sont déjà en comparaison
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
