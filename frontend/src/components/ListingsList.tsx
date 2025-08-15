import React from 'react'

interface Listing {
  id: string
  url: string
  title?: string
  price?: number
  currency: string
  address?: string
  bedrooms?: number
  bathrooms?: number
  property_type?: string
  area_name?: string
  site_domain: string
  scraped_at: string
}

interface ListingsListProps {
  listings: Listing[]
  selectedListing: Listing | null
  onSelectListing: (listing: Listing | null) => void
}

export const ListingsList: React.FC<ListingsListProps> = ({
  listings,
  selectedListing,
  onSelectListing
}) => {
  const formatPrice = (price?: number, currency = 'CAD') => {
    if (!price) return 'Price not available'
    
    return new Intl.NumberFormat('en-CA', {
      style: 'currency',
      currency: currency,
      maximumFractionDigits: 0
    }).format(price)
  }

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr)
      return date.toLocaleDateString('en-CA', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch {
      return 'Recently'
    }
  }

  if (listings.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500">
        <div className="mb-2">📭</div>
        <p>No listings found</p>
        <p className="text-sm">Try adjusting your filters</p>
      </div>
    )
  }

  return (
    <div className="divide-y divide-gray-200">
      {listings.map((listing) => (
        <div
          key={listing.id}
          onClick={() => onSelectListing(
            selectedListing?.id === listing.id ? null : listing
          )}
          className={`p-4 cursor-pointer transition-colors ${
            selectedListing?.id === listing.id 
              ? 'bg-blue-50 border-r-2 border-blue-500'
              : 'hover:bg-gray-50'
          }`}
        >
          {/* Header */}
          <div className="flex justify-between items-start mb-2">
            <div className="flex-1 min-w-0">
              <h4 className="text-sm font-medium text-gray-900 truncate">
                {listing.title || listing.address || 'Untitled'}
              </h4>
              {listing.area_name && (
                <p className="text-xs text-gray-500 mt-1">
                  📍 {listing.area_name}
                </p>
              )}
            </div>
            <div className="text-right ml-2">
              <div className="text-sm font-semibold text-green-600">
                {formatPrice(listing.price, listing.currency)}
              </div>
            </div>
          </div>

          {/* Property Details */}
          <div className="flex items-center space-x-3 text-xs text-gray-600 mb-2">
            {listing.bedrooms && (
              <span className="flex items-center">
                🛏️ {listing.bedrooms} bed{listing.bedrooms !== 1 ? 's' : ''}
              </span>
            )}
            {listing.bathrooms && (
              <span className="flex items-center">
                🛁 {listing.bathrooms} bath{listing.bathrooms !== 1 ? 's' : ''}
              </span>
            )}
            {listing.property_type && (
              <span className="capitalize">
                🏠 {listing.property_type}
              </span>
            )}
          </div>

          {/* Address */}
          {listing.address && listing.address !== listing.title && (
            <p className="text-xs text-gray-500 mb-2 line-clamp-2">
              {listing.address}
            </p>
          )}

          {/* Footer */}
          <div className="flex justify-between items-center">
            <div className="text-xs text-gray-400">
              {formatDate(listing.scraped_at)}
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-xs text-gray-400">
                {listing.site_domain}
              </span>
              <a
                href={listing.url}
                target="_blank"
                rel="noopener noreferrer"
                onClick={(e) => e.stopPropagation()}
                className="text-xs text-blue-600 hover:text-blue-800"
              >
                View →
              </a>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
