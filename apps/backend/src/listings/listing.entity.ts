import { Entity, PrimaryGeneratedColumn, Column, UpdateDateColumn } from 'typeorm';
import { ApiProperty } from '@nestjs/swagger';

@Entity('listings')
export class Listing {
  @ApiProperty({ description: 'Unique identifier for the listing' })
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ type: 'integer', nullable: true })
  area_id: number;

  @Column({ type: 'date', nullable: true })
  published_date: Date;

  @Column({ type: 'timestamp with time zone', default: () => 'CURRENT_TIMESTAMP' })
  scraped_at: Date;

  @UpdateDateColumn({ type: 'timestamp with time zone' })
  updated_at: Date;

  @Column({ type: 'jsonb', nullable: true })
  raw_data: any;

  @Column({ type: 'boolean', default: true })
  is_active: boolean;

  @Column({ type: 'decimal', precision: 12, scale: 2, nullable: true })
  yearly_yield: number;

  @Column({ type: 'decimal', precision: 12, scale: 2, nullable: true })
  monthly_rent: number;

  @ApiProperty({ description: 'Price of the property' })
  @Column({ type: 'decimal', precision: 12, scale: 2, nullable: true })
  price: number;

  @Column({ type: 'decimal', precision: 10, scale: 2, nullable: true })
  price_per_sqm: number;

  @Column({ type: 'decimal', precision: 8, scale: 2, nullable: true })
  area_sqm: number;

  @ApiProperty({ description: 'Number of bedrooms', required: false })
  @Column({ type: 'integer', nullable: true })
  bedrooms: number;

  @Column({ type: 'decimal', precision: 3, scale: 1, nullable: true })
  bathrooms: number;

  // PostGIS geometry column - handled as raw data
  @Column({ type: 'geometry', spatialFeatureType: 'Point', srid: 4326, nullable: true })
  coordinates: any;

  @Column({ type: 'varchar', nullable: true })
  url_hash: string;

  @ApiProperty({ description: 'Original URL of the listing' })
  @Column({ type: 'text', nullable: true })
  url: string;

  @ApiProperty({ description: 'Title of the property', required: false })
  @Column({ type: 'text', nullable: true })
  title: string;

  @Column({ type: 'varchar', nullable: true })
  site_domain: string;

  @ApiProperty({ description: 'Currency code (e.g., CAD, USD)' })
  @Column({ type: 'varchar', nullable: true })
  currency: string;

  @ApiProperty({ description: 'Type of property (e.g., apartment, house, condo)' })
  @Column({ type: 'varchar', nullable: true })
  property_type: string;

  @Column({ type: 'varchar', nullable: true })
  listing_type: string;

  @ApiProperty({ description: 'Full address of the property', required: false })
  @Column({ type: 'text', nullable: true })
  address: string;
}
