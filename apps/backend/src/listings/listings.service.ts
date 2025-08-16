import { Injectable, NotFoundException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository, FindManyOptions, Between, MoreThanOrEqual, LessThanOrEqual } from 'typeorm';
import { Listing } from './listing.entity';
import { CreateListingDto, UpdateListingDto, ListingQueryDto } from './dto/listing.dto';

@Injectable()
export class ListingsService {
  constructor(
    @InjectRepository(Listing)
    private listingsRepository: Repository<Listing>,
  ) {}

  async create(createListingDto: CreateListingDto): Promise<Listing> {
    const listing = this.listingsRepository.create(createListingDto);
    return this.listingsRepository.save(listing);
  }

  async findAll(queryDto: ListingQueryDto): Promise<{
    data: Listing[];
    total: number;
    page: number;
    limit: number;
    totalPages: number;
  }> {
    const { 
      page = 1, 
      limit = 10, 
      minPrice, 
      maxPrice, 
      propertyType, 
      bedrooms, 
      areaName, 
      sortBy = 'scraped_at', 
      sortOrder = 'DESC' 
    } = queryDto;
    
    const skip = (page - 1) * limit;
    
    const where: any = {};
    
    // Price filters
    if (minPrice !== undefined && maxPrice !== undefined) {
      where.price = Between(minPrice, maxPrice);
    } else if (minPrice !== undefined) {
      where.price = MoreThanOrEqual(minPrice);
    } else if (maxPrice !== undefined) {
      where.price = LessThanOrEqual(maxPrice);
    }
    
    // Other filters
    if (propertyType) {
      where.property_type = propertyType;
    }
    
    if (bedrooms !== undefined) {
      where.bedrooms = bedrooms;
    }
    
    if (areaName) {
      where.area_name = areaName;
    }
    
    const options: FindManyOptions<Listing> = {
      where,
      skip,
      take: limit,
      order: {
        [sortBy]: sortOrder,
      },
    };
    
    const [data, total] = await this.listingsRepository.findAndCount(options);
    
    return {
      data,
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    };
  }

  async findOne(id: string): Promise<Listing> {
    const listing = await this.listingsRepository.findOne({ where: { id } });
    if (!listing) {
      throw new NotFoundException(`Listing with ID ${id} not found`);
    }
    return listing;
  }

  async update(id: string, updateListingDto: UpdateListingDto): Promise<Listing> {
    const listing = await this.findOne(id);
    Object.assign(listing, updateListingDto);
    return this.listingsRepository.save(listing);
  }

  async remove(id: string): Promise<void> {
    const listing = await this.findOne(id);
    await this.listingsRepository.remove(listing);
  }

  async getStats(): Promise<{
    total: number;
    averagePrice: number;
    minPrice: number;
    maxPrice: number;
    propertyTypes: { type: string; count: number }[];
    recentListings: number;
  }> {
    const total = await this.listingsRepository.count();
    
    const priceStats = await this.listingsRepository
      .createQueryBuilder('listing')
      .select('AVG(listing.price)', 'average')
      .addSelect('MIN(listing.price)', 'minimum')
      .addSelect('MAX(listing.price)', 'maximum')
      .where('listing.price IS NOT NULL')
      .getRawOne();
    
    const propertyTypes = await this.listingsRepository
      .createQueryBuilder('listing')
      .select('listing.property_type', 'type')
      .addSelect('COUNT(*)', 'count')
      .where('listing.property_type IS NOT NULL')
      .groupBy('listing.property_type')
      .getRawMany();
    
    const oneDayAgo = new Date();
    oneDayAgo.setDate(oneDayAgo.getDate() - 1);
    
    const recentListings = await this.listingsRepository
      .createQueryBuilder('listing')
      .where('listing.scraped_at > :date', { date: oneDayAgo })
      .getCount();
    
    return {
      total,
      averagePrice: parseFloat(priceStats?.average) || 0,
      minPrice: parseFloat(priceStats?.minimum) || 0,
      maxPrice: parseFloat(priceStats?.maximum) || 0,
      propertyTypes: propertyTypes.map(pt => ({
        type: pt.type,
        count: parseInt(pt.count),
      })),
      recentListings,
    };
  }

  async bulkCreate(listings: CreateListingDto[]): Promise<Listing[]> {
    const entities = this.listingsRepository.create(listings);
    return this.listingsRepository.save(entities);
  }
}
