import { useEffect, useMemo, useRef, useState } from 'react'
import maplibregl from 'maplibre-gl'
import MapboxDraw from '@mapbox/mapbox-gl-draw'

const defaultCenter: [number, number] = [2.3522, 48.8566] // Paris

export function App() {
  const mapRef = useRef<maplibregl.Map | null>(null)
  const mapContainer = useRef<HTMLDivElement | null>(null)
  const drawRef = useRef<MapboxDraw | null>(null)
  const [polygon, setPolygon] = useState<any | null>(null)
  const [results, setResults] = useState<any[]>([])
  const [scraping, setScraping] = useState(false)
  const [lastReport, setLastReport] = useState<any | null>(null)
  const [useLive, setUseLive] = useState(false)

  useEffect(() => {
    if (mapRef.current || !mapContainer.current) return

    // Shim: MapboxDraw expects window.mapboxgl; maplibre exposes maplibregl
    if (!(window as any).mapboxgl) {
      ;(window as any).mapboxgl = maplibregl as any
    }

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
      center: defaultCenter,
      zoom: 11,
    })
    mapRef.current = map

    const draw = new MapboxDraw({
      displayControlsDefault: false,
      controls: { polygon: true, trash: true },
    })
    drawRef.current = draw

    map.addControl(draw as any, 'top-left')

    const update = () => {
      const fc = draw.getAll()
      const poly = fc.features.find((f: any) => f.geometry?.type === 'Polygon')
      setPolygon(poly || null)
    }

    map.on('draw.create', update)
    map.on('draw.update', update)
    map.on('draw.delete', update)

    return () => map.remove()
  }, [])

  const onSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    const form = new FormData(e.target as HTMLFormElement)
    const where = String(form.get('where') || '')
    const what = String(form.get('what') || '')
    const when = String(form.get('when') || '')
    const polygonParam = polygon ? encodeURIComponent(JSON.stringify(polygon)) : ''

    const qs = new URLSearchParams({ where, what, when })
    if (polygonParam) qs.set('polygon', polygonParam)

    const res = await fetch(`/api/search?${qs.toString()}`)
    const data = await res.json()
    setResults(data.listings || [])
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

  return (
    <div className="h-screen flex flex-col">
      <header className="p-3 border-b">Real Estate Search</header>
      <main className="flex-1 grid grid-cols-1 md:grid-cols-2">
        <div className="p-3 space-y-3">
          <form onSubmit={onSearch} className="space-y-2">
            <div className="grid grid-cols-3 gap-2">
              <input name="where" placeholder="WHERE (city/neighborhood)" className="border p-2 rounded" />
              <input name="what" placeholder="WHAT (type/size/price)" className="border p-2 rounded" />
              <input name="when" placeholder="WHEN (YYYY-MM-DD)" className="border p-2 rounded" />
            </div>
            <button className="px-4 py-2 bg-black text-white rounded">Search</button>
            <button type="button" onClick={runScrape} disabled={scraping} className="px-4 py-2 bg-blue-600 text-white rounded ml-2">
              {scraping ? 'Running…' : 'Run scrape + ETL'}
            </button>
            <label className="ml-3 inline-flex items-center gap-2 text-sm">
              <input type="checkbox" checked={useLive} onChange={e => setUseLive(e.target.checked)} />
              Use live sources
            </label>
          </form>
          <div className="h-[60vh] border" ref={mapContainer} />
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
    </div>
  )
}
