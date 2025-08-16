import { Controller, Get, Post, Body, Patch, Param, Delete, Query, HttpCode, HttpStatus } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse, ApiParam, ApiQuery } from '@nestjs/swagger';
import { ListingsService } from './listings.service';
import { CreateListingDto, UpdateListingDto, ListingQueryDto } from './dto/listing.dto';
import { Listing } from './listing.entity';

@ApiTags('listings')
@Controller('listings')
export class ListingsController {
  constructor(private readonly listingsService: ListingsService) {}

  @Post()
  @ApiOperation({ summary: 'Create a new listing' })
  @ApiResponse({ status: 201, description: 'The listing has been successfully created.', type: Listing })
  @ApiResponse({ status: 400, description: 'Bad request.' })
  create(@Body() createListingDto: CreateListingDto): Promise<Listing> {
    return this.listingsService.create(createListingDto);
  }

  @Post('bulk')
  @ApiOperation({ summary: 'Create multiple listings at once' })
  @ApiResponse({ status: 201, description: 'The listings have been successfully created.', type: [Listing] })
  @ApiResponse({ status: 400, description: 'Bad request.' })
  bulkCreate(@Body() createListingDtos: CreateListingDto[]): Promise<Listing[]> {
    return this.listingsService.bulkCreate(createListingDtos);
  }

  @Get()
  @ApiOperation({ summary: 'Get all listings with filtering and pagination' })
  @ApiResponse({ status: 200, description: 'Return all listings.' })
  @ApiQuery({ name: 'page', required: false, description: 'Page number' })
  @ApiQuery({ name: 'limit', required: false, description: 'Items per page' })
  @ApiQuery({ name: 'minPrice', required: false, description: 'Minimum price filter' })
  @ApiQuery({ name: 'maxPrice', required: false, description: 'Maximum price filter' })
  @ApiQuery({ name: 'propertyType', required: false, description: 'Property type filter' })
  @ApiQuery({ name: 'bedrooms', required: false, description: 'Number of bedrooms' })
  @ApiQuery({ name: 'areaName', required: false, description: 'Area name filter' })
  @ApiQuery({ name: 'sortBy', required: false, description: 'Sort field' })
  @ApiQuery({ name: 'sortOrder', required: false, description: 'Sort order' })
  findAll(@Query() query: ListingQueryDto) {
    return this.listingsService.findAll(query);
  }

  @Get('stats')
  @ApiOperation({ summary: 'Get statistics about listings' })
  @ApiResponse({ status: 200, description: 'Return statistics.' })
  getStats() {
    return this.listingsService.getStats();
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get a listing by ID' })
  @ApiResponse({ status: 200, description: 'Return the listing.', type: Listing })
  @ApiResponse({ status: 404, description: 'Listing not found.' })
  @ApiParam({ name: 'id', description: 'Listing ID' })
  findOne(@Param('id') id: string): Promise<Listing> {
    return this.listingsService.findOne(id);
  }

  @Patch(':id')
  @ApiOperation({ summary: 'Update a listing' })
  @ApiResponse({ status: 200, description: 'The listing has been successfully updated.', type: Listing })
  @ApiResponse({ status: 404, description: 'Listing not found.' })
  @ApiParam({ name: 'id', description: 'Listing ID' })
  update(@Param('id') id: string, @Body() updateListingDto: UpdateListingDto): Promise<Listing> {
    return this.listingsService.update(id, updateListingDto);
  }

  @Delete(':id')
  @HttpCode(HttpStatus.NO_CONTENT)
  @ApiOperation({ summary: 'Delete a listing' })
  @ApiResponse({ status: 204, description: 'The listing has been successfully deleted.' })
  @ApiResponse({ status: 404, description: 'Listing not found.' })
  @ApiParam({ name: 'id', description: 'Listing ID' })
  remove(@Param('id') id: string): Promise<void> {
    return this.listingsService.remove(id);
  }
}
