import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { TypeOrmModule } from '@nestjs/typeorm';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { ListingsModule } from './listings/listings.module';
import { Listing } from './listings/listing.entity';
import { HealthController } from './health/health.controller';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
    }),
    TypeOrmModule.forRoot({
      type: 'postgres',
      host: process.env.DATABASE_HOST || 'localhost',
      port: parseInt(process.env.DATABASE_PORT || '5432'),
      username: process.env.DATABASE_USERNAME || 'scrappingbot_user',
      password: process.env.DATABASE_PASSWORD || 'scrappingbot_pass',
      database: process.env.DATABASE_NAME || 'scrappingbot',
      entities: [Listing],
      synchronize: false, // Don't auto-sync to preserve existing data
      logging: process.env.NODE_ENV === 'development',
    }),
    ListingsModule,
  ],
  controllers: [AppController, HealthController],
  providers: [AppService],
})
export class AppModule {}
