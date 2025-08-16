import React from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface Listing {
  id: number;
  title: string;
  price: number;
  location: string;
  property_type: string;
  rooms?: number;
  surface?: number;
  created_at: string;
}

interface AnalyticsChartsProps {
  listings: Listing[];
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

export default function AnalyticsCharts({ listings }: AnalyticsChartsProps) {
  // Données pour le graphique des prix par type
  const priceByType = listings.reduce((acc, listing) => {
    const existing = acc.find(item => item.type === listing.property_type);
    if (existing) {
      existing.avgPrice = (existing.avgPrice + listing.price) / 2;
      existing.count += 1;
    } else {
      acc.push({
        type: listing.property_type,
        avgPrice: listing.price,
        count: 1,
        totalValue: listing.price
      });
    }
    return acc;
  }, [] as any[]);

  // Données pour le graphique des prix par mois
  const pricesByMonth = listings.reduce((acc, listing) => {
    const month = new Date(listing.created_at).toLocaleDateString('fr-FR', { 
      month: 'short',
      year: 'numeric'
    });
    const existing = acc.find(item => item.month === month);
    if (existing) {
      existing.avgPrice = (existing.avgPrice + listing.price) / 2;
      existing.count += 1;
    } else {
      acc.push({
        month,
        avgPrice: listing.price,
        count: 1
      });
    }
    return acc;
  }, [] as any[]);

  // Données pour le graphique en secteurs
  const propertyTypeDistribution = listings.reduce((acc, listing) => {
    const existing = acc.find(item => item.name === listing.property_type);
    if (existing) {
      existing.value += 1;
    } else {
      acc.push({
        name: listing.property_type,
        value: 1
      });
    }
    return acc;
  }, [] as any[]);

  // Données pour les prix par nombre de pièces
  const pricesByRooms = listings
    .filter(listing => listing.rooms)
    .reduce((acc, listing) => {
      const rooms = listing.rooms!;
      const existing = acc.find(item => item.rooms === rooms);
      if (existing) {
        existing.avgPrice = (existing.avgPrice + listing.price) / 2;
        existing.count += 1;
      } else {
        acc.push({
          rooms,
          avgPrice: listing.price,
          count: 1
        });
      }
      return acc;
    }, [] as any[])
    .sort((a, b) => a.rooms - b.rooms);

  const formatPrice = (value: number) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  return (
    <div className="space-y-8">
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Analyse des Données Immobilières
        </h3>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Graphique des prix par type */}
          <div>
            <h4 className="text-md font-medium text-gray-700 mb-3">
              Prix Moyen par Type de Bien
            </h4>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={priceByType}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="type" />
                <YAxis tickFormatter={formatPrice} />
                <Tooltip formatter={(value) => [formatPrice(Number(value)), 'Prix moyen']} />
                <Bar dataKey="avgPrice" fill="#3B82F6" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Distribution par type de bien */}
          <div>
            <h4 className="text-md font-medium text-gray-700 mb-3">
              Répartition par Type de Bien
            </h4>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={propertyTypeDistribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent = 0 }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {propertyTypeDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Évolution des prix dans le temps */}
          <div>
            <h4 className="text-md font-medium text-gray-700 mb-3">
              Évolution des Prix
            </h4>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={pricesByMonth}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis tickFormatter={formatPrice} />
                <Tooltip formatter={(value) => [formatPrice(Number(value)), 'Prix moyen']} />
                <Line 
                  type="monotone" 
                  dataKey="avgPrice" 
                  stroke="#10B981" 
                  strokeWidth={2}
                  dot={{ fill: '#10B981' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Prix par nombre de pièces */}
          <div>
            <h4 className="text-md font-medium text-gray-700 mb-3">
              Prix Moyen par Nombre de Pièces
            </h4>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={pricesByRooms}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="rooms" 
                  tickFormatter={(value) => `${value}P`}
                />
                <YAxis tickFormatter={formatPrice} />
                <Tooltip 
                  formatter={(value) => [formatPrice(Number(value)), 'Prix moyen']}
                  labelFormatter={(label) => `${label} pièce${label > 1 ? 's' : ''}`}
                />
                <Bar dataKey="avgPrice" fill="#F59E0B" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
