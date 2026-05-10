import { useEffect, useState } from 'react'
import './App.css'

type OddsData = Record<string, { over: number; under: number; point: number }>

function formatOdds(value: number): string {
  return value > 0 ? `+${value}` : `${value}`
}

// Returns a set of "Player|side" keys that have Big or Insane moves
function getBigAlerts(flags: string[]): Set<string> {
  const alerts = new Set<string>()
  for (const flag of flags) {
    if (!flag.includes('30 - 40 CHANGE') && !flag.includes('41 - 50+ CHANGE!')) continue
    // format: "Player Name over: ..."
    const match = flag.match(/^(.+?) (over|under):/)
    if (match) alerts.add(`${match[1]}|${match[2]}`)
  }
  return alerts
}

function App() {
  const [odds, setOdds] = useState<OddsData>({})
  const [flags, setFlags] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  useEffect(() => {
    async function fetchData() {
      try {
        const [oddsRes, flagsRes] = await Promise.all([
          fetch('/api/odds'),
          fetch('/api/flags'),
        ])
        const oddsJson = await oddsRes.json()
        const flagsJson = await flagsRes.json()
        setOdds(oddsJson)
        setFlags(flagsJson.flags)
        setLastUpdated(new Date())
      } catch (e) {
        setError('Failed to fetch data. Is the server running?')
      } finally {
        setLoading(false)
      }
    }
    fetchData()
    const interval = setInterval(fetchData, 10 * 60 * 1000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="app">
      <header>
        <h1>NBA Player Props</h1>
        <div className="header-meta">
          <span className="subtitle">FanDuel · Player Points · Updated every 10 min during games</span>
          {lastUpdated && <span className="last-updated">Last updated: {lastUpdated.toLocaleTimeString()}</span>}
        </div>
      </header>

      {loading && <p className="empty">Loading...</p>}
      {error && <p className="empty">{error}</p>}

      {!loading && !error && (
        <>
          <section className="section">
            <h2>Odds</h2>
            {(() => {
              const alerts = getBigAlerts(flags)
              return (
                <table>
                  <thead>
                    <tr>
                      <th>Player</th>
                      <th>Line</th>
                      <th>Over</th>
                      <th>Under</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(odds).map(([player, o]) => (
                      <tr key={player}>
                        <td>{player}</td>
                        <td>{o.point}</td>
                        <td className={o.over > 0 ? 'positive' : 'negative'}>
                          {formatOdds(o.over)}
                          {alerts.has(`${player}|over`) && <span className="alert">!</span>}
                        </td>
                        <td className={o.under > 0 ? 'positive' : 'negative'}>
                          {formatOdds(o.under)}
                          {alerts.has(`${player}|under`) && <span className="alert">!</span>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )
            })()}
          </section>

          <section className="section">
            <h2>Line Movements</h2>
            {flags.length === 0 ? (
              <p className="empty">No significant line movements detected.</p>
            ) : (
              <ul className="flags">
                {flags.map((flag, i) => (
                  <li key={i}>{flag}</li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </div>
  )
}

export default App
