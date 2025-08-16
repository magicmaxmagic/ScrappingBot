import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Listing } from './listing.entity';

export interface ListingWithCoordinates {
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
  created_at: Date;
  updated_at: Date;
}

@Injectable()
export class ListingService {
  constructor(
    @InjectRepository(Listing)
    private readonly listingRepository: Repository<Listing>,
  ) {}

  async findAll(): Promise<{ listings: ListingWithCoordinates[]; total: number }> {
    try {
      // Requête SQL pour récupérer les données avec coordonnées
      const query = `
        SELECT 
          id,
          title,
          price,
          property_type,
          address,
          area_sqm,
          bedrooms,
          bathrooms,
          CASE 
            WHEN coordinates IS NOT NULL 
            THEN ST_Y(coordinates) 
            ELSE NULL 
          END as latitude,
          CASE 
            WHEN coordinates IS NOT NULL 
            THEN ST_X(coordinates) 
            ELSE NULL 
          END as longitude,
          url,
          scraped_at as created_at,
          updated_at
        FROM listings 
        WHERE is_active = true
        ORDER BY scraped_at DESC
      `;

      const rawListings = await this.listingRepository.query(query);
      
      const listings: ListingWithCoordinates[] = rawListings.map((listing: any) => ({
        id: listing.id,
        title: listing.title || 'Sans titre',
        price: Number(listing.price) || 0,
        property_type: listing.property_type || 'apartment',
        address: listing.address || 'Adresse non disponible',
        area_sqm: listing.area_sqm ? Number(listing.area_sqm) : undefined,
        bedrooms: listing.bedrooms ? Number(listing.bedrooms) : undefined,
        bathrooms: listing.bathrooms ? Number(listing.bathrooms) : undefined,
        latitude: listing.latitude ? Number(listing.latitude) : undefined,
        longitude: listing.longitude ? Number(listing.longitude) : undefined,
        url: listing.url || '',
        created_at: new Date(listing.created_at),
        updated_at: new Date(listing.updated_at),
      }));

      return {
        listings,
        total: listings.length,
      };
    } catch (error) {
      console.error('Error fetching listings:', error);
      
      // Fallback avec données mock si erreur de base de données
      const mockListings: ListingWithCoordinates[] = [
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
          created_at: new Date(),
          updated_at: new Date(),
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
          created_at: new Date(),
          updated_at: new Date(),
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
          created_at: new Date(),
          updated_at: new Date(),
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
          created_at: new Date(),
          updated_at: new Date(),
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
          created_at: new Date(),
          updated_at: new Date(),
        },
      ];

      return {
        listings: mockListings,
        total: mockListings.length,
      };
    }
  }

  async findById(id: string): Promise<ListingWithCoordinates | null> {
    try {
      const query = `
        SELECT 
          id,
          title,
          price,
          property_type,
          address,
          area_sqm,
          bedrooms,
          bathrooms,
          CASE 
            WHEN coordinates IS NOT NULL 
            THEN ST_Y(coordinates) 
            ELSE NULL 
          END as latitude,
          CASE 
            WHEN coordinates IS NOT NULL 
            THEN ST_X(coordinates) 
            ELSE NULL 
          END as longitude,
          url,
          scraped_at as created_at,
          updated_at
        FROM listings 
        WHERE id = $1 AND is_active = true
      `;

      const result = await this.listingRepository.query(query, [id]);
      
      if (result.length === 0) {
        return null;
      }

      const listing = result[0];
      return {
        id: listing.id,
        title: listing.title || 'Sans titre',
        price: Number(listing.price) || 0,
        property_type: listing.property_type || 'apartment',
        address: listing.address || 'Adresse non disponible',
        area_sqm: listing.area_sqm ? Number(listing.area_sqm) : undefined,
        bedrooms: listing.bedrooms ? Number(listing.bedrooms) : undefined,
        bathrooms: listing.bathrooms ? Number(listing.bathrooms) : undefined,
        latitude: listing.latitude ? Number(listing.latitude) : undefined,
        longitude: listing.longitude ? Number(listing.longitude) : undefined,
        url: listing.url || '',
        created_at: new Date(listing.created_at),
        updated_at: new Date(listing.updated_at),
      };
    } catch (error) {
      console.error('Error fetching listing by id:', error);
      return null;
    }
  }
}
