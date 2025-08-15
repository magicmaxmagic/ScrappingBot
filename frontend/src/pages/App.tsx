import { useEffect, useMemo, useRef, useState } from 'react'
import maplibregl from 'maplibre-gl'
import MapboxDraw from '@mapbox/mapbox-gl-draw'
import { Chatbot } from '../components/Chatbot'

const defaultCenter: [number, number] = [-73.5673, 45.5017] // Montreal
const API_BASE = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8787'

export function App() {
  const mapRef = useRef<maplibregl.Map | null>(null)
  const mapContainer = useRef<HTMLDivElement | null>(null)
  const drawRef = useRef<MapboxDraw | null>(null)
  const [polygon, setPolygon] = useState<any | null>(null)
  const [results, setResults] = useState<any[]>([])
  const [scraping, setScraping] = useState(false)
  const [lastReport, setLastReport] = useState<any | null>(null)
  const [useLive, setUseLive] = useState(false)
  const [mapError, setMapError] = useState<string | null>(null)
  const [menuOpen, setMenuOpen] = useState(false)
  const [where, setWhere] = useState('')
  const [what, setWhat] = useState('')
  const [when, setWhen] = useState('')
  const [chatOpen, setChatOpen] = useState(false)
  const [centerLng, setCenterLng] = useState<string>('')
  const [centerLat, setCenterLat] = useState<string>('')
  const [centerZoom, setCenterZoom] = useState<string>('')

  useEffect(() => {
    if (mapRef.current || !mapContainer.current) return

    console.log('Initializing map...')
    setMapError(null)

    try {
      // Simple, reliable map initialization
      const map = new maplibregl.Map({
        container: mapContainer.current,
        style: {
          version: 8,
          sources: {
            'raster-tiles': {
              type: 'raster',
              tiles: [
                'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
              ],
              tileSize: 256,
              attribution: '© OpenStreetMap contributors'
            }
          },
          layers: [
            {
              id: 'simple-tiles',
              type: 'raster',
              source: 'raster-tiles'
            }
          ]
        },
        center: defaultCenter,
        zoom: 11
      })
      
      mapRef.current = map
      console.log('Map created successfully')

      map.on('load', () => {
        console.log('Map loaded successfully')
        
        // Shim for MapboxDraw
        if (!(window as any).mapboxgl) {
          ;(window as any).mapboxgl = maplibregl as any
        }

        try {
          // Minimal styles to avoid MapLibre v3 line-dasharray expression issues
          const drawStyles: any[] = [
            {
              id: 'gl-draw-polygon-fill-inactive',
              type: 'fill',
              filter: ['all', ['==', 'active', 'false'], ['==', '$type', 'Polygon'], ['!=', 'mode', 'static']],
              paint: {
                'fill-color': '#3bb2d0',
                'fill-opacity': 0.1,
              },
            },
            {
              id: 'gl-draw-polygon-stroke-inactive',
              type: 'line',
              filter: ['all', ['==', 'active', 'false'], ['==', '$type', 'Polygon'], ['!=', 'mode', 'static']],
              layout: { 'line-cap': 'round', 'line-join': 'round' },
              paint: {
                'line-color': '#3bb2d0',
                'line-width': 2,
              },
            },
            {
              id: 'gl-draw-polygon-fill-active',
              type: 'fill',
              filter: ['all', ['==', 'active', 'true'], ['==', '$type', 'Polygon']],
              paint: {
                'fill-color': '#fbb03b',
                'fill-opacity': 0.1,
              },
            },
            {
              id: 'gl-draw-polygon-stroke-active',
              type: 'line',
              filter: ['all', ['==', 'active', 'true'], ['==', '$type', 'Polygon']],
              layout: { 'line-cap': 'round', 'line-join': 'round' },
              paint: {
                'line-color': '#fbb03b',
                'line-width': 2,
              },
            },
            {
              id: 'gl-draw-polygon-and-line-vertex-halo-active',
              type: 'circle',
              filter: ['all', ['==', 'meta', 'vertex'], ['==', '$type', 'Point']],
              paint: {
                'circle-radius': 6,
                'circle-color': '#fff',
              },
            },
            {
              id: 'gl-draw-polygon-and-line-vertex-active',
              type: 'circle',
              filter: ['all', ['==', 'meta', 'vertex'], ['==', '$type', 'Point']],
              paint: {
                'circle-radius': 3,
                'circle-color': '#fbb03b',
              },
            },
          ]

          const draw = new MapboxDraw({
            displayControlsDefault: false,
            controls: { polygon: true, trash: true },
            styles: drawStyles,
          })
          drawRef.current = draw

          map.addControl(draw as any, 'top-left')
          console.log('Draw control added successfully')

          const update = () => {
            const fc = draw.getAll()
            const poly = fc.features.find((f: any) => f.geometry?.type === 'Polygon')
            setPolygon(poly || null)
          }

          map.on('draw.create', update)
          map.on('draw.update', update)
          map.on('draw.delete', update)
        } catch (e: any) {
          console.error('Draw control error:', e)
          setMapError(`Draw error: ${e.message}`)
        }
      })

      map.on('error', (e: any) => {
        console.error('Map error:', e)
        setMapError(`Map error: ${e.error?.message || e.message || 'Unknown'}`)
      })

      // Cleanup
      return () => {
        console.log('Cleaning up map...')
        try {
          map.remove()
        } catch (e) {
          console.warn('Error during map cleanup:', e)
        }
      }
    } catch (e: any) {
      console.error('Failed to initialize map:', e)
      setMapError(`Init error: ${e.message}`)
    }
  }, [])

  const onSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    const _where = where
    const _what = what
    const _when = when
    const polygonParam = polygon ? encodeURIComponent(JSON.stringify(polygon)) : ''

    const qs = new URLSearchParams({ where: _where, what: _what, when: _when })
    if (polygonParam) qs.set('polygon', polygonParam)

    const res = await fetch(`/api/search?${qs.toString()}`)
    const data = await res.json()
    setResults(data.listings || [])
  }

  const centerByCity = async () => {
    try {
      setMapError(null)
      const q = where?.trim()
      if (!q) { setMapError('Renseignez une ville'); return }
      const url = `https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&q=${encodeURIComponent(q)}`
      const r = await fetch(url, { headers: { 'Accept': 'application/json' } })
      if (!r.ok) throw new Error(`Geocode HTTP ${r.status}`)
      const arr = await r.json()
      if (!arr || !arr.length) { setMapError('Ville introuvable'); return }
      const it = arr[0]
      const lon = parseFloat(it.lon)
      const lat = parseFloat(it.lat)
      const bbox = it.boundingbox // [south, north, west, east]
      if (bbox && bbox.length === 4) {
        const south = parseFloat(bbox[0])
        const north = parseFloat(bbox[1])
        const west = parseFloat(bbox[2])
        const east = parseFloat(bbox[3])
        if ([south, north, west, east].every(Number.isFinite)) {
          mapRef.current?.fitBounds([[west, south], [east, north]], { padding: 32 })
        } else {
          mapRef.current?.setCenter([lon, lat])
          mapRef.current?.setZoom(11)
        }
      } else {
        mapRef.current?.setCenter([lon, lat])
        mapRef.current?.setZoom(11)
      }
    } catch (e: any) {
      setMapError(`Geocode error: ${e?.message || e}`)
    }
  }

  const runScrape = async () => {
    try {
      setScraping(true)
      setLastReport(null)
  const params = new URLSearchParams()
  // Use a relative path so it works across machines
  if (useLive) params.set('sources', 'sources.yml')
  const res = await fetch(`/dev-scrape/run${params.toString() ? `?${params.toString()}` : ''}`, { method: 'POST' })
      if (res.status === 202) {
        // Poll for completion
        for (let i = 0; i < 60; i++) { // up to ~60s
          await new Promise(r => setTimeout(r, 1000))
          const r2 = await fetch('/dev-scrape/last')
          if (r2.ok) {
            const data = await r2.json()
            setLastReport(data?.report || data)
            break
          }
        }
      } else if (res.ok) {
        const data = await res.json()
        setLastReport(data?.report || data)
      } else {
        setLastReport({ ok: false, error: `HTTP ${res.status}` })
      }
      // Refresh results regardless
      try {
        // Clear KV cache (search:*) and bypass cache once for fresh read
        await fetch('/api/admin/cache/clear', { method: 'POST' })
        const res2 = await fetch('/api/search?where=&what=&when=&nocache=1')
        const data2 = await res2.json()
        setResults(data2.listings || [])
      } catch {}
    } catch (e) {
      setLastReport({ error: String((e as any)?.message || e) })
    } finally {
      setScraping(false)
    }
  }

  const recenter = () => {
    const lng = parseFloat(centerLng)
    const lat = parseFloat(centerLat)
    const z = centerZoom ? parseFloat(centerZoom) : undefined
    if (!isFinite(lng) || !isFinite(lat)) {
      setMapError('Invalid center coordinates')
      return
    }
    try {
      mapRef.current?.setCenter([lng, lat])
      if (z && isFinite(z)) mapRef.current?.setZoom(z)
      setMapError(null)
    } catch (e: any) {
      setMapError(`Center error: ${e?.message || e}`)
    }
  }

  return (
  <div className="h-screen flex flex-col">
      <header className="p-3 border-b flex items-center justify-between">
        <span className="font-medium">Real Estate Search</span>
        <span className="text-xs text-gray-500">Frontend: check logs/frontend.log for port</span>
      </header>
      <main className="flex-1 grid grid-cols-1 md:grid-cols-2">
        <div className="p-3 space-y-3">
          <form onSubmit={onSearch} className="space-y-2 relative">
            <div className="grid grid-cols-1 md:grid-cols-[1fr_auto_auto] gap-2 items-center">
              <input name="where" value={where} onChange={e => setWhere(e.target.value)} placeholder="Ville (ex: Paris)" className="border p-2 rounded" />
              <button type="button" onClick={centerByCity} className="px-3 py-2 border rounded">Centrer</button>
              <button type="button" onClick={() => setMenuOpen(v => !v)} aria-label="Options" className="px-3 py-2 border rounded">⋯</button>
            </div>
            {menuOpen && (
              <div className="absolute z-10 mt-1 w-full md:w-[420px] max-w-[90vw] bg-white border rounded shadow p-3">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                  <input name="what" value={what} onChange={e => setWhat(e.target.value)} placeholder="WHAT (type/prix)" className="border p-2 rounded" />
                  <input name="when" value={when} onChange={e => setWhen(e.target.value)} placeholder="WHEN (YYYY-MM-DD)" className="border p-2 rounded" />
                  <label className="inline-flex items-center gap-2 text-sm border rounded p-2">
                    <input type="checkbox" checked={useLive} onChange={e => setUseLive(e.target.checked)} />
                    Sources live
                  </label>
                </div>
                <div className="flex items-center gap-2 mt-2">
                  <button className="px-4 py-2 bg-black text-white rounded" type="submit">Search</button>
                  <button type="button" onClick={runScrape} disabled={scraping} className="px-4 py-2 bg-blue-600 text-white rounded">
                    {scraping ? 'Running…' : 'Run scrape + ETL'}
                  </button>
                  <button type="button" onClick={() => setMenuOpen(false)} className="px-3 py-2 border rounded">Fermer</button>
                </div>
                {mapError && <div className="text-xs text-red-600 mt-2">Map error: {mapError}</div>}
              </div>
            )}
          </form>
          <div className="h-[60vh] border rounded" ref={mapContainer} />
          {lastReport && (
            <pre className="text-xs bg-gray-50 p-2 rounded border overflow-auto max-h-40">{JSON.stringify(lastReport, null, 2)}</pre>
          )}
        </div>
        <div className="p-3 overflow-auto">
          <h2 className="font-semibold mb-2">Results</h2>
          <ul className="space-y-2">
            {results.map((r, i) => {
              const ppsm = r.area_sqm && r.area_sqm > 0 ? Math.round((r.price || 0) / r.area_sqm) : null
              return (
                <li key={i} className="border rounded p-2">
                  <div className="text-sm text-gray-500 flex items-center gap-2">
                    <span className="uppercase">{r.kind}</span>
                    <span>• {r.currency} {r.price?.toLocaleString?.() ?? r.price}</span>
                    {ppsm && <span>• {r.currency} {ppsm}/m²</span>}
                  </div>
                  <div className="font-medium">{r.title || r.url}</div>
                </li>
              )
            })}
          </ul>
        </div>
      </main>
      {/* Floating chatbot button */}
      <button
        onClick={() => setChatOpen(true)}
        className="fixed bottom-4 right-4 rounded-full bg-black text-white w-12 h-12 shadow-lg"
        aria-label="Open Chatbot"
      >
        💬
      </button>
      {chatOpen && (
        <div className="fixed inset-0 bg-black/30">
          <div className="absolute right-0 top-0 h-full w-full max-w-md bg-white shadow-xl flex flex-col">
            <div className="flex items-center justify-between p-2 border-b">
              <span className="text-sm font-medium">Chatbot</span>
              <button onClick={() => setChatOpen(false)} className="px-3 py-1 border rounded text-sm">Fermer</button>
            </div>
            <div className="flex-1 min-h-0">
              <Chatbot />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
