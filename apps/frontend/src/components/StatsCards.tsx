interface StatsCard {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  change?: string;
  changeType?: 'increase' | 'decrease' | 'neutral';
}

interface StatsCardsProps {
  totalListings: number;
  avgPrice: number;
  newToday: number;
  avgPricePerM2?: number;
}

import { Home, Euro, TrendingUp, Activity } from 'lucide-react';

export default function StatsCards({
  totalListings,
  avgPrice,
  newToday,
  avgPricePerM2
}: StatsCardsProps) {
  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(price);
  };

  const stats: StatsCard[] = [
    {
      title: 'Total des annonces',
      value: totalListings.toLocaleString('fr-FR'),
      icon: <Home className="h-6 w-6 text-blue-600" />,
    },
    {
      title: 'Prix moyen',
      value: formatPrice(avgPrice),
      icon: <Euro className="h-6 w-6 text-green-600" />,
    },
    {
      title: 'Nouvelles aujourd\'hui',
      value: newToday,
      icon: <TrendingUp className="h-6 w-6 text-purple-600" />,
    },
    ...(avgPricePerM2 ? [{
      title: 'Prix moyen/m²',
      value: formatPrice(avgPricePerM2),
      icon: <Activity className="h-6 w-6 text-orange-600" />,
    }] : []),
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {stats.map((stat, index) => (
        <div
          key={index}
          className="bg-white overflow-hidden shadow rounded-lg"
        >
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                {stat.icon}
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    {stat.title}
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {stat.value}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
