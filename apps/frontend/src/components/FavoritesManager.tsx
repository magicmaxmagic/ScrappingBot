'use client';

import { useState, useEffect } from 'react';
import { Heart, Download, Share2 } from 'lucide-react';
import toast from 'react-hot-toast';

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

interface FavoritesManagerProps {
  listing: Listing;
}

export default function FavoritesManager({ listing }: FavoritesManagerProps) {
  const [isFavorite, setIsFavorite] = useState(false);

  useEffect(() => {
    // Charger les favoris depuis localStorage
    const favorites = JSON.parse(localStorage.getItem('favorites') || '[]');
    setIsFavorite(favorites.some((fav: Listing) => fav.id === listing.id));
  }, [listing.id]);

  const toggleFavorite = () => {
    let favorites = JSON.parse(localStorage.getItem('favorites') || '[]');
    
    if (isFavorite) {
      favorites = favorites.filter((fav: Listing) => fav.id !== listing.id);
      toast.success('Supprimé des favoris');
    } else {
      favorites.push(listing);
      toast.success('Ajouté aux favoris');
    }
    
    localStorage.setItem('favorites', JSON.stringify(favorites));
    setIsFavorite(!isFavorite);
  };

  const exportListing = () => {
    const dataStr = JSON.stringify(listing, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `listing_${listing.id}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
    
    toast.success('Annonce exportée');
  };

  const shareListing = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: listing.title,
          text: `${listing.title} - ${listing.price}€ à ${listing.location}`,
          url: listing.url,
        });
        toast.success('Annonce partagée');
      } catch (error) {
        // Fallback au clipboard si le partage échoue
        copyToClipboard();
      }
    } else {
      copyToClipboard();
    }
  };

  const copyToClipboard = () => {
    const text = `${listing.title}\n${listing.price}€ - ${listing.location}\n${listing.url}`;
    navigator.clipboard.writeText(text).then(() => {
      toast.success('Lien copié dans le presse-papiers');
    });
  };

  return (
    <div className="flex items-center space-x-2">
      <button
        onClick={toggleFavorite}
        className={`p-2 rounded-full transition-colors ${
          isFavorite 
            ? 'bg-red-100 text-red-600 hover:bg-red-200' 
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
        }`}
        title={isFavorite ? 'Supprimer des favoris' : 'Ajouter aux favoris'}
      >
        <Heart 
          className={`h-4 w-4 ${isFavorite ? 'fill-current' : ''}`} 
        />
      </button>
      
      <button
        onClick={exportListing}
        className="p-2 rounded-full bg-blue-100 text-blue-600 hover:bg-blue-200 transition-colors"
        title="Exporter l'annonce"
      >
        <Download className="h-4 w-4" />
      </button>
      
      <button
        onClick={shareListing}
        className="p-2 rounded-full bg-green-100 text-green-600 hover:bg-green-200 transition-colors"
        title="Partager l'annonce"
      >
        <Share2 className="h-4 w-4" />
      </button>
    </div>
  );
}
