import React, { useState, useEffect } from 'react'

interface Filters {
  area?: string
  min_price?: number
  max_price?: number
  property_type?: string
  listing_type?: string
}

interface FilterPanelProps {
  filters: Filters
  onFiltersChange: (filters: Filters) => void
  loading: boolean
}

export const FilterPanel: React.FC<FilterPanelProps> = ({ 
  filters, 
  onFiltersChange, 
  loading 
}) => {
  const [localFilters, setLocalFilters] = useState<Filters>(filters)

  useEffect(() => {
    setLocalFilters(filters)
  }, [filters])

  const handleInputChange = (field: keyof Filters, value: string) => {
    const newFilters = { ...localFilters }
    
    if (field === 'min_price' || field === 'max_price') {
      newFilters[field] = value ? parseInt(value) : undefined
    } else {
      newFilters[field] = value || undefined
    }
    
    setLocalFilters(newFilters)
  }

  const applyFilters = () => {
    onFiltersChange(localFilters)
  }

  const clearFilters = () => {
    const emptyFilters = {}
    setLocalFilters(emptyFilters)
    onFiltersChange(emptyFilters)
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900">Filters</h3>
      
      {/* Area */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Area
        </label>
        <input
          type="text"
          value={localFilters.area || ''}
          onChange={(e) => handleInputChange('area', e.target.value)}
          placeholder="e.g., Plateau, Downtown"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      {/* Price Range */}
      <div className="grid grid-cols-2 gap-2">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Min Price
          </label>
          <input
            type="number"
            value={localFilters.min_price || ''}
            onChange={(e) => handleInputChange('min_price', e.target.value)}
            placeholder="Min"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Max Price
          </label>
          <input
            type="number"
            value={localFilters.max_price || ''}
            onChange={(e) => handleInputChange('max_price', e.target.value)}
            placeholder="Max"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>

      {/* Property Type */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Property Type
        </label>
        <select
          value={localFilters.property_type || ''}
          onChange={(e) => handleInputChange('property_type', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="">All Types</option>
          <option value="condo">Condo</option>
          <option value="house">House</option>
          <option value="apartment">Apartment</option>
          <option value="townhouse">Townhouse</option>
        </select>
      </div>

      {/* Listing Type */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Listing Type
        </label>
        <select
          value={localFilters.listing_type || ''}
          onChange={(e) => handleInputChange('listing_type', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="">All Types</option>
          <option value="sale">For Sale</option>
          <option value="rent">For Rent</option>
        </select>
      </div>

      {/* Action Buttons */}
      <div className="flex space-x-2 pt-2">
        <button
          onClick={applyFilters}
          disabled={loading}
          className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Loading...' : 'Apply'}
        </button>
        <button
          onClick={clearFilters}
          disabled={loading}
          className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
        >
          Clear
        </button>
      </div>
    </div>
  )
}
