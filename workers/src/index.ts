import { Hono } from 'hono'
import type { Context } from 'hono'
import { z } from 'zod'

// Import D1Database type from Cloudflare types if available
// If using Cloudflare Workers, install @cloudflare/workers-types for D1Database
import type { D1Database, KVNamespace } from '@cloudflare/workers-types'

export type Env = {
  DB: D1Database
  CACHE: KVNamespace
}

const app = new Hono<{ Bindings: Env }>()

const SearchQuery = z.object({
  where: z.string().optional(),
  what: z.string().optional(),
  when: z.string().optional(),
  polygon: z.string().optional(),
})

const handleSearch = async (c: Context<{ Bindings: Env }>) => {
  try {
    // Robust query parsing
  const url = new URL(c.req.url)
      const paramsObj: Record<string, string> = {}
  url.searchParams.forEach((value, key) => { paramsObj[key] = value })
    const q = SearchQuery.safeParse(paramsObj)
    if (!q.success) return c.json({ error: 'bad_query' }, 400)

    // polygon is optional; searchParams are already decoded
    const polygon = q.data.polygon ? JSON.parse(q.data.polygon) : null
    const when = q.data.when || ''

    // Try KV cache first
      const nocache = c.req.query('nocache') === '1'
    const cacheKey = `search:${q.data.where || ''}:${q.data.what || ''}:${when}:${q.data.polygon || ''}`
      if (!nocache) {
        const cached = await c.env.CACHE.get(cacheKey)
        if (cached) return c.json(JSON.parse(cached))
      }

    // Very simple SQL example: filter by date and maybe spatial if polygon provided
    // Note: spatial filtering would require precomputed neighborhood assignment or an extension; here we filter by neighborhood if provided via 'where'
    const params: any[] = []
    let sql = `SELECT * FROM listings WHERE 1=1`
    if (when) {
      sql += ` AND extracted_at >= ?`
      params.push(when)
    }
    // naive filter by text match
    if (q.data.where) {
      sql += ` AND (address LIKE ? OR neighborhood LIKE ?)`
      params.push(`%${q.data.where}%`, `%${q.data.where}%`)
    }

    const rs = await c.env.DB.prepare(sql).bind(...params).all()
    const listings = rs.results || []

    // simple metrics example
    const metrics = {
      count: listings.length,
      avg_price: listings.length ? listings.reduce((a: number, b: any) => a + (b.price || 0), 0) / listings.length : 0,
    }
    const payload = { listings, metrics }

      if (!nocache) {
        await c.env.CACHE.put(cacheKey, JSON.stringify(payload), { expirationTtl: 300 })
      }
    return c.json(payload)
  } catch (err: any) {
    return c.json({ error: 'internal_error', message: String(err?.message || err) }, 500)
  }
}

app.get('/api/search', handleSearch)
app.get('/search', handleSearch)

const handleImportNeighborhoods = async (c: Context<{ Bindings: Env }>) => {
  const body = await c.req.json()
  // store as a separate table or JSON blob
  await c.env.DB.prepare(`DELETE FROM neighborhoods`).run()
  if (Array.isArray(body.features)) {
    for (const f of body.features) {
      await c.env.DB.prepare(`INSERT INTO neighborhoods (name, geojson) VALUES (?, ?)`).bind(
        f.properties?.name || 'unknown', JSON.stringify(f)
      ).run()
    }
  }
  return c.json({ ok: true })
}

app.post('/api/admin/import/neighborhoods', handleImportNeighborhoods)
app.post('/admin/import/neighborhoods', handleImportNeighborhoods)

// Admin: clear KV cache by prefix (default: search:)
const handleCacheClear = async (c: Context<{ Bindings: Env }>) => {
  const prefix = c.req.query('prefix') || 'search:'
  let deleted = 0
  let cursor: string | undefined = undefined
  // @ts-ignore KV list is available at runtime; types may vary per version
  do {
    // @ts-ignore
    const list: any = await c.env.CACHE.list({ prefix, cursor })
    for (const k of list.keys || []) {
      await c.env.CACHE.delete(k.name)
      deleted++
    }
    cursor = list.cursor
    if (list.list_complete) break
  } while (cursor)
  return c.json({ ok: true, deleted, prefix })
}

app.post('/api/admin/cache/clear', handleCacheClear)
app.get('/api/admin/cache/clear', handleCacheClear)
const handleAreaMetrics = async (c: Context<{ Bindings: Env }>) => {
  const asOf = c.req.query('asOf') || ''
  const rs = await c.env.DB.prepare(`SELECT * FROM area_metrics WHERE as_of = ?`).bind(asOf).all()
  return c.json({ rows: rs.results || [] })
}

app.get('/api/area-metrics', handleAreaMetrics)
app.get('/area-metrics', handleAreaMetrics)

const handleListings = async (c: Context<{ Bindings: Env }>) => {
  const filters = c.req.query()
  let sql = `SELECT * FROM listings WHERE 1=1`
  const params: any[] = []
  if (filters?.kind) { sql += ` AND kind = ?`; params.push(filters.kind) }
  if (filters?.min_price) { sql += ` AND price >= ?`; params.push(Number(filters.min_price)) }
  if (filters?.max_price) { sql += ` AND price <= ?`; params.push(Number(filters.max_price)) }
  if (filters?.min_size) { sql += ` AND area_sqm >= ?`; params.push(Number(filters.min_size)) }
  if (filters?.max_size) { sql += ` AND area_sqm <= ?`; params.push(Number(filters.max_size)) }
  const rs = await c.env.DB.prepare(sql).bind(...params).all()
  return c.json({ rows: rs.results || [] })
}

app.get('/api/listings', handleListings)
app.get('/listings', handleListings)

export default app
