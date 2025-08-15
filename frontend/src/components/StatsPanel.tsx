import React from 'react'

interface AreaStat {
  name: string
  city: string
  listing_count: number
  avg_price: number
  min_price: number
  max_price: number
  recent_count: number
}

interface StatsPanelProps {
  stats: AreaStat[]
}

export const StatsPanel: React.FC<StatsPanelProps> = ({ stats }) => {
  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-CA', {
      style: 'currency',
      currency: 'CAD',
      maximumFractionDigits: 0
    }).format(price)
  }

  const topAreas = stats.slice(0, 5)

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-gray-900">Top Areas</h3>
      
      <div className="space-y-2">
        {topAreas.map((area, index) => (
          <div
            key={`${area.name}-${area.city}`}
            className="bg-gray-50 rounded-lg p-3 text-xs"
          >
            <div className="flex justify-between items-start mb-1">
              <div className="font-medium text-gray-900 truncate">
                {area.name}
              </div>
              <div className="text-blue-600 font-medium ml-2">
                {area.listing_count}
              </div>
            </div>
            
            <div className="text-gray-600 space-y-1">
              <div className="flex justify-between">
                <span>Avg:</span>
                <span className="font-medium">
                  {formatPrice(area.avg_price)}
                </span>
              </div>
              
              <div className="flex justify-between text-xs">
                <span>{formatPrice(area.min_price)}</span>
                <span>→</span>
                <span>{formatPrice(area.max_price)}</span>
              </div>
              
              {area.recent_count > 0 && (
                <div className="text-green-600 text-xs">
                  +{area.recent_count} new (24h)
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {stats.length > 5 && (
        <div className="text-xs text-gray-500 text-center pt-2">
          +{stats.length - 5} more areas
        </div>
      )}
    </div>
  )
}
