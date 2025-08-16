import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001';

export interface RealListing {
  id: string;
  title: string;
  price: number;
  property_type: string;
  address: string;
  area_sqm?: number;
  bedrooms?: number;
  bathrooms?: number;
  latitude?: number;
  longitude?: number;
  url?: string;
  created_at: string;
  updated_at: string;
}

export interface ListingResponse {
  listings: RealListing[];
  total: number;
}

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const listingsApi = {
  // Get all listings with coordinates
  getListings: async (): Promise<ListingResponse> => {
    try {
      const response = await api.get<ListingResponse>('/listings');
      return response.data;
    } catch (error) {
      console.warn('API not available, falling back to mock data');
      
      // Mock data de fallback
      const mockListings: RealListing[] = [
        {
          id: '1',
          title: 'Superbe condo 2BR dans Ville-Marie',
          price: 450000,
          property_type: 'Condo',
          address: '1234 Rue Saint-Denis, Ville-Marie, QC',
          area_sqm: 85,
          bedrooms: 2,
          bathrooms: 1,
          latitude: 45.5088,
          longitude: -73.5878,
          url: 'https://example.com/listing/1',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          id: '2',
          title: 'Appartement 3BR Plateau-Mont-Royal',
          price: 525000,
          property_type: 'Apartment',
          address: '5678 Boulevard Saint-Laurent, Le Plateau-Mont-Royal, QC',
          area_sqm: 120,
          bedrooms: 3,
          bathrooms: 2,
          latitude: 45.5276,
          longitude: -73.5825,
          url: 'https://example.com/listing/2',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          id: '3',
          title: 'Maison 4BR Outremont',
          price: 850000,
          property_type: 'House',
          address: '9876 Avenue du Parc, Outremont, QC',
          area_sqm: 200,
          bedrooms: 4,
          bathrooms: 3,
          latitude: 45.5234,
          longitude: -73.6078,
          url: 'https://example.com/listing/3',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          id: '4',
          title: 'Loft 1BR Griffintown',
          price: 320000,
          property_type: 'Condo',
          address: '1111 Rue Notre-Dame, Le Sud-Ouest, QC',
          area_sqm: 60,
          bedrooms: 1,
          bathrooms: 1,
          latitude: 45.4942,
          longitude: -73.5597,
          url: 'https://example.com/listing/4',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          id: '5',
          title: 'Townhouse 3BR Verdun',
          price: 475000,
          property_type: 'Townhouse',
          address: '2222 Rue Wellington, Verdun, QC',
          area_sqm: 140,
          bedrooms: 3,
          bathrooms: 2,
          latitude: 45.4533,
          longitude: -73.5673,
          url: 'https://example.com/listing/5',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ];

      return {
        listings: mockListings,
        total: mockListings.length,
      };
    }
  },

  // Get a single listing by ID
  getListing: async (id: string): Promise<RealListing | null> => {
    try {
      const response = await api.get<RealListing>(`/listings/${id}`);
      return response.data;
    } catch (error) {
      console.warn(`Failed to fetch listing ${id}`);
      return null;
    }
  },
};
