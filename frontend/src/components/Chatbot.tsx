import { useState } from 'react'

type Msg = { role: 'system' | 'user' | 'assistant'; content: string }

export function Chatbot() {
  const [messages, setMessages] = useState<Msg[]>([
    {
      role: 'system',
      content:
        [
          'Tu es un assistant qui génère des sources de scraping pour notre pipeline.',
          'Toujours répondre avec:',
          '1) Un court plan (3-5 points) en français',
          '2) Un code block ```yaml``` contenant UNIQUEMENT un YAML conforme au schéma suivant:',
          '   sources:',
          '     - name: <nom-du-site>',
          '       start_urls: ["https://exemple.tld/recherche?q=..."]',
          '       listing_patterns: ["/annonce/|listing|property|/condo/"]',
          '       use_js: false',
          'Notes:',
          '- start_urls doit pointer sur des pages publiques pertinentes (recherche condos, filtres, etc.)',
          '- listing_patterns est une ou plusieurs regex simples pour trouver les URLs d’annonce',
          '- Met use_js: true si la page nécessite du rendu JS.',
          'IMPORTANT: le code block doit être balisé comme ```yaml et contenir uniquement le YAML, sans texte additionnel.',
          "NE PAS utiliser 'example.com' ni de domaine placeholder. Si tu ne connais pas le site, demande à l'utilisateur de fournir un URL réel.",
        ].join('\n')
    },
    { role: 'assistant', content: "Explique ce que tu veux scrapper (ex: 'condos Canal Lachine Montréal, prix'). Je générerai le sources.yml et lancerai le scraping avec prévisualisation." }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [model, setModel] = useState('qwen2.5:3b-instruct')

  const send = async () => {
    const text = input.trim()
    if (!text) return
    setError(null)
    const next = [...messages, { role: 'user', content: text } as Msg]
    setMessages(next)
    setInput('')
    setLoading(true)
    try {
      const body = {
        model,
        messages: next.map(m => ({ role: m.role, content: m.content })),
        stream: false,
        options: { temperature: 0.2 }
      }
      const res = await fetch('/ollama/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      const content: string = data?.message?.content || data?.response || '(no content)'
      let extra = ''
      // Try to extract a YAML code block for sources.yml
      const m = content.match(/```(?:ya?ml)?\n([\s\S]*?)```/)
      let preview: any = null
      if (m && m[1]) {
        const yamlText = m[1].trim()
        // Guard against placeholder domains
        if (/example\.com/i.test(yamlText)) {
          setMessages(prev => [...prev, { role: 'assistant', content: content + "\n\nLe YAML contient un domaine placeholder (example.com). Merci de fournir une URL réelle d’une page de listings publique du site que vous souhaitez scraper." }])
          return
        }
        try {
          // Trigger scrape by posting the YAML to the dev scraper server
          const r2 = await fetch('/dev-scrape/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sources_yaml: yamlText })
          })
          if (r2.status === 202) {
            // Poll /last for a short while
            for (let i = 0; i < 30; i++) {
              await new Promise(r => setTimeout(r, 1000))
              const r3 = await fetch('/dev-scrape/last')
              if (r3.ok) {
                const js = await r3.json()
                if (js && js.ok !== undefined) {
                  preview = js.preview || null
                  break
                }
              }
            }
          } else {
            extra = `\n\n(Scrape trigger failed: HTTP ${r2.status})`
          }
        } catch (e: any) {
          extra = `\n\n(Scrape error: ${String(e?.message || e)})`
        }
      }
      const final = preview ? `${content}\n\nPrévisualisation (max 10 items):\n${JSON.stringify(preview, null, 2)}` : content + extra
      setMessages(prev => [...prev, { role: 'assistant', content: final }])
    } catch (e: any) {
      setError(String(e?.message || e))
    } finally {
      setLoading(false)
    }
  }

  const onKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-2 p-2 border-b">
        <span className="text-sm text-gray-600">Chatbot (Ollama)</span>
        <select className="border p-1 rounded text-sm" value={model} onChange={e => setModel(e.target.value)}>
          <option value="qwen2.5:3b-instruct">qwen2.5:3b-instruct</option>
          <option value="mistral:7b-instruct">mistral:7b-instruct</option>
        </select>
        {error && <span className="text-xs text-red-600">{error}</span>}
      </div>
      <div className="flex-1 overflow-auto p-3 space-y-2">
        {messages.map((m, i) => (
          <div key={i} className={m.role === 'user' ? 'text-right' : ''}>
            <div className={`inline-block max-w-[80%] whitespace-pre-wrap rounded px-3 py-2 ${m.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-100'}`}>
              {m.content}
            </div>
          </div>
        ))}
      </div>
      <div className="p-2 border-t flex items-center gap-2">
        <input
          className="border rounded p-2 flex-1"
          placeholder="Décris le scraping souhaité…"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={onKey}
        />
        <button onClick={send} disabled={loading} className="px-4 py-2 bg-black text-white rounded">
          {loading ? '...' : 'Envoyer'}
        </button>
      </div>
    </div>
  )
}
