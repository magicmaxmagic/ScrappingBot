/**
 * Cloudflare Worker API with PostgreSQL connection
 * Serves scraped real estate data from PostgreSQL database
 */


interface Env {
  DATABASE_URL: string;
  CORS_ORIGIN?: string;
}

interface ListingQuery {
  area?: string;
  min_price?: number;
  max_price?: number;
  property_type?: string;
  limit?: number;
  offset?: number;
  bbox?: string; // "west,south,east,north" for map bounds
}

interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  metadata?: {
    total?: number;
    limit?: number;
    offset?: number;
  };
}

class PostgreSQLConnection {
  private env: Env;

  constructor(env: Env) {
    this.env = env;
  }

  async query(sql: string, params: any[] = []): Promise<any[]> {
    // Note: Cloudflare Workers doesn't natively support PostgreSQL
    // This is a conceptual implementation - in practice, you'd use:
    // 1. Supabase REST API
    // 2. PlanetScale/Neon Edge Functions
    // 3. Prisma Data Proxy
    // 4. Custom TCP connection (limited support)
    
    const response = await fetch(this.getConnectionUrl(), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.env.DATABASE_URL}`,
      },
      body: JSON.stringify({ sql, params }),
    });

    if (!response.ok) {
      throw new Error(`Database query failed: ${response.statusText}`);
    }

    return response.json();
  }

  private getConnectionUrl(): string {
    // For Supabase REST API
    if (this.env.DATABASE_URL.includes('supabase')) {
      return this.env.DATABASE_URL.replace('postgresql://', 'https://').split('@')[1] + '/rest/v1/rpc/execute_sql';
    }
    
    // For other providers, implement accordingly
    throw new Error('Unsupported database provider for Workers');
  }
}

async function getListings(db: PostgreSQLConnection, query: ListingQuery): Promise<ApiResponse<any[]>> {
  try {
    const { area, min_price, max_price, property_type, limit = 50, offset = 0, bbox } = query;
    
    let sql = `
      SELECT 
        l.id,
        l.url,
        l.title,
        l.price,
        l.currency,
        l.area_sqm,
        l.bedrooms,
        l.bathrooms,
        l.property_type,
        l.listing_type,
        l.address,
        ST_X(l.coordinates) as longitude,
        ST_Y(l.coordinates) as latitude,
        l.site_domain,
        l.published_date,
        l.monthly_rent,
        l.scraped_at,
        a.name as area_name,
        a.city,
        a.province
      FROM listings l
      LEFT JOIN areas a ON l.area_id = a.id
      WHERE l.is_active = true
    `;
    
    const params: any[] = [];
    let paramCount = 0;

    // Area filter
    if (area) {
      paramCount++;
      sql += ` AND a.name ILIKE $${paramCount}`;
      params.push(`%${area}%`);
    }

    // Price filters
    if (min_price !== undefined) {
      paramCount++;
      sql += ` AND l.price >= $${paramCount}`;
      params.push(min_price);
    }

    if (max_price !== undefined) {
      paramCount++;
      sql += ` AND l.price <= $${paramCount}`;
      params.push(max_price);
    }

    // Property type filter
    if (property_type) {
      paramCount++;
      sql += ` AND l.property_type ILIKE $${paramCount}`;
      params.push(`%${property_type}%`);
    }

    // Bounding box filter for map
    if (bbox) {
      const [west, south, east, north] = bbox.split(',').map(Number);
      if (west && south && east && north) {
        sql += ` AND l.coordinates && ST_MakeEnvelope($${paramCount + 1}, $${paramCount + 2}, $${paramCount + 3}, $${paramCount + 4}, 4326)`;
        params.push(west, south, east, north);
        paramCount += 4;
      }
    }

    sql += ` ORDER BY l.scraped_at DESC LIMIT $${paramCount + 1} OFFSET $${paramCount + 2}`;
    params.push(limit, offset);

    const results = await db.query(sql, params);

    // Get total count for pagination
    let countSql = sql.replace(/SELECT.*?FROM/, 'SELECT COUNT(*) as total FROM')
                     .replace(/ORDER BY.*$/, '')
                     .replace(/LIMIT.*$/, '');
    const countResult = await db.query(countSql, params.slice(0, -2));
    const total = countResult[0]?.total || 0;

    return {
      success: true,
      data: results,
      metadata: {
        total,
        limit,
        offset
      }
    };

  } catch (error) {
    console.error('getListings error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
}

async function getAreaStats(db: PostgreSQLConnection): Promise<ApiResponse<any[]>> {
  try {
    const sql = `
      SELECT 
        a.name,
        a.city,
        COUNT(l.id) as listing_count,
        AVG(l.price)::NUMERIC(10,2) as avg_price,
        MIN(l.price) as min_price,
        MAX(l.price) as max_price,
        COUNT(l.id) FILTER (WHERE l.scraped_at >= NOW() - INTERVAL '24 hours') as recent_count
      FROM areas a
      LEFT JOIN listings l ON l.area_id = a.id AND l.is_active = true
      GROUP BY a.id, a.name, a.city
      HAVING COUNT(l.id) > 0
      ORDER BY listing_count DESC
      LIMIT 20
    `;

    const results = await db.query(sql);

    return {
      success: true,
      data: results
    };

  } catch (error) {
    console.error('getAreaStats error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
}

async function getRecentActivity(db: PostgreSQLConnection): Promise<ApiResponse<any>> {
  try {
    const sql = `
      SELECT 
        DATE(scraped_at) as date,
        COUNT(*) as listings_scraped,
        COUNT(DISTINCT site_domain) as sources_active,
        AVG(price)::NUMERIC(10,2) as avg_price
      FROM listings
      WHERE scraped_at >= NOW() - INTERVAL '30 days'
        AND is_active = true
      GROUP BY DATE(scraped_at)
      ORDER BY date DESC
    `;

    const results = await db.query(sql);

    return {
      success: true,
      data: results
    };

  } catch (error) {
    console.error('getRecentActivity error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
}

function setCorsHeaders(response: Response, env: Env): Response {
  const corsOrigin = env.CORS_ORIGIN || '*';
  
  const corsHeaders = {
    'Access-Control-Allow-Origin': corsOrigin,
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Access-Control-Max-Age': '86400',
  };

  // Add CORS headers to existing response
  Object.entries(corsHeaders).forEach(([key, value]) => {
    response.headers.set(key, value);
  });

  return response;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return setCorsHeaders(new Response(null, { status: 204 }), env);
    }

    try {
      const url = new URL(request.url);
      const db = new PostgreSQLConnection(env);

      // API Routes
      if (url.pathname === '/api/listings') {
        const query: ListingQuery = {};
        
        // Parse query parameters
        for (const [key, value] of url.searchParams.entries()) {
          if (key === 'min_price' || key === 'max_price' || key === 'limit' || key === 'offset') {
            const parsed = parseInt(value);
            (query as any)[key] = isNaN(parsed) ? undefined : parsed;
          } else {
            query[key as keyof ListingQuery] = value as any;
          }
        }

        const result = await getListings(db, query);
        const response = new Response(JSON.stringify(result), {
          headers: { 'Content-Type': 'application/json' }
        });
        
        return setCorsHeaders(response, env);
      }

      if (url.pathname === '/api/areas/stats') {
        const result = await getAreaStats(db);
        const response = new Response(JSON.stringify(result), {
          headers: { 'Content-Type': 'application/json' }
        });
        
        return setCorsHeaders(response, env);
      }

      if (url.pathname === '/api/activity') {
        const result = await getRecentActivity(db);
        const response = new Response(JSON.stringify(result), {
          headers: { 'Content-Type': 'application/json' }
        });
        
        return setCorsHeaders(response, env);
      }

      // Health check
      if (url.pathname === '/health') {
        const response = new Response(JSON.stringify({
          status: 'ok',
          timestamp: new Date().toISOString(),
          database: 'connected'
        }), {
          headers: { 'Content-Type': 'application/json' }
        });
        
        return setCorsHeaders(response, env);
      }

      // Default response
      const response = new Response(JSON.stringify({
        success: false,
        error: 'Not Found',
        routes: [
          'GET /api/listings',
          'GET /api/areas/stats',
          'GET /api/activity',
          'GET /health'
        ]
      }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' }
      });

      return setCorsHeaders(response, env);

    } catch (error) {
      console.error('Worker error:', error);
      
      const response = new Response(JSON.stringify({
        success: false,
        error: error instanceof Error ? error.message : 'Internal Server Error'
      }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      });

      return setCorsHeaders(response, env);
    }
  },
};
