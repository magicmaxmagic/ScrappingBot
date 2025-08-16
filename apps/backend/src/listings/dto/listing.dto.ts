import { IsOptional, IsString, IsNumber, IsDecimal, IsUUID, Min, Max } from 'class-validator';
import { Transform, Type } from 'class-transformer';
import { ApiProperty } from '@nestjs/swagger';

export class CreateListingDto {
  @ApiProperty({ description: 'Original URL of the listing' })
  @IsString()
  url: string;

  @ApiProperty({ description: 'Title of the property', required: false })
  @IsOptional()
  @IsString()
  title?: string;

  @ApiProperty({ description: 'Price of the property', required: false })
  @IsOptional()
  @Type(() => Number)
  @IsNumber({ maxDecimalPlaces: 2 })
  @Min(0)
  price?: number;

  @ApiProperty({ description: 'Currency code', default: 'CAD' })
  @IsOptional()
  @IsString()
  currency?: string = 'CAD';

  @ApiProperty({ description: 'Full address of the property', required: false })
  @IsOptional()
  @IsString()
  address?: string;

  @ApiProperty({ description: 'Number of bedrooms', required: false })
  @IsOptional()
  @Type(() => Number)
  @IsNumber()
  @Min(0)
  @Max(50)
  bedrooms?: number;

  @ApiProperty({ description: 'Number of bathrooms', required: false })
  @IsOptional()
  @Type(() => Number)
  @IsNumber({ maxDecimalPlaces: 1 })
  @Min(0)
  @Max(50)
  bathrooms?: number;

  @ApiProperty({ description: 'Type of property', required: false })
  @IsOptional()
  @IsString()
  property_type?: string;

  @ApiProperty({ description: 'Area in square meters', required: false })
  @IsOptional()
  @Type(() => Number)
  @IsNumber({ maxDecimalPlaces: 2 })
  @Min(0)
  area_sqm?: number;

  @ApiProperty({ description: 'Area/neighborhood name', required: false })
  @IsOptional()
  @IsString()
  area_name?: string;

  @ApiProperty({ description: 'Source domain' })
  @IsString()
  site_domain: string;

  @ApiProperty({ description: 'Longitude coordinate', required: false })
  @IsOptional()
  @Type(() => Number)
  @IsNumber({ maxDecimalPlaces: 7 })
  @Min(-180)
  @Max(180)
  longitude?: number;

  @ApiProperty({ description: 'Latitude coordinate', required: false })
  @IsOptional()
  @Type(() => Number)
  @IsNumber({ maxDecimalPlaces: 7 })
  @Min(-90)
  @Max(90)
  latitude?: number;

  @ApiProperty({ description: 'Raw scraped data', required: false })
  @IsOptional()
  raw_data?: Record<string, any>;
}

export class UpdateListingDto {
  @ApiProperty({ description: 'Title of the property', required: false })
  @IsOptional()
  @IsString()
  title?: string;

  @ApiProperty({ description: 'Price of the property', required: false })
  @IsOptional()
  @Type(() => Number)
  @IsNumber({ maxDecimalPlaces: 2 })
  @Min(0)
  price?: number;

  @ApiProperty({ description: 'Currency code', required: false })
  @IsOptional()
  @IsString()
  currency?: string;

  @ApiProperty({ description: 'Full address of the property', required: false })
  @IsOptional()
  @IsString()
  address?: string;

  @ApiProperty({ description: 'Number of bedrooms', required: false })
  @IsOptional()
  @Type(() => Number)
  @IsNumber()
  @Min(0)
  @Max(50)
  bedrooms?: number;

  @ApiProperty({ description: 'Number of bathrooms', required: false })
  @IsOptional()
  @Type(() => Number)
  @IsNumber({ maxDecimalPlaces: 1 })
  @Min(0)
  @Max(50)
  bathrooms?: number;

  @ApiProperty({ description: 'Type of property', required: false })
  @IsOptional()
  @IsString()
  property_type?: string;

  @ApiProperty({ description: 'Area in square meters', required: false })
  @IsOptional()
  @Type(() => Number)
  @IsNumber({ maxDecimalPlaces: 2 })
  @Min(0)
  area_sqm?: number;

  @ApiProperty({ description: 'Area/neighborhood name', required: false })
  @IsOptional()
  @IsString()
  area_name?: string;

  @ApiProperty({ description: 'Longitude coordinate', required: false })
  @IsOptional()
  @Type(() => Number)
  @IsNumber({ maxDecimalPlaces: 7 })
  @Min(-180)
  @Max(180)
  longitude?: number;

  @ApiProperty({ description: 'Latitude coordinate', required: false })
  @IsOptional()
  @Type(() => Number)
  @IsNumber({ maxDecimalPlaces: 7 })
  @Min(-90)
  @Max(90)
  latitude?: number;

  @ApiProperty({ description: 'Raw scraped data', required: false })
  @IsOptional()
  raw_data?: Record<string, any>;
}

export class ListingQueryDto {
  @ApiProperty({ description: 'Page number for pagination', required: false, default: 1 })
  @IsOptional()
  @Type(() => Number)
  @IsNumber()
  @Min(1)
  page?: number = 1;

  @ApiProperty({ description: 'Number of items per page', required: false, default: 10 })
  @IsOptional()
  @Type(() => Number)
  @IsNumber()
  @Min(1)
  @Max(100)
  limit?: number = 10;

  @ApiProperty({ description: 'Minimum price filter', required: false })
  @IsOptional()
  @Type(() => Number)
  @IsNumber()
  @Min(0)
  minPrice?: number;

  @ApiProperty({ description: 'Maximum price filter', required: false })
  @IsOptional()
  @Type(() => Number)
  @IsNumber()
  @Min(0)
  maxPrice?: number;

  @ApiProperty({ description: 'Property type filter', required: false })
  @IsOptional()
  @IsString()
  propertyType?: string;

  @ApiProperty({ description: 'Number of bedrooms filter', required: false })
  @IsOptional()
  @Type(() => Number)
  @IsNumber()
  @Min(0)
  bedrooms?: number;

  @ApiProperty({ description: 'Area name filter', required: false })
  @IsOptional()
  @IsString()
  areaName?: string;

  @ApiProperty({ description: 'Sort field', required: false, enum: ['price', 'scraped_at', 'area_sqm'] })
  @IsOptional()
  @IsString()
  sortBy?: 'price' | 'scraped_at' | 'area_sqm' = 'scraped_at';

  @ApiProperty({ description: 'Sort order', required: false, enum: ['ASC', 'DESC'] })
  @IsOptional()
  @IsString()
  sortOrder?: 'ASC' | 'DESC' = 'DESC';
}
