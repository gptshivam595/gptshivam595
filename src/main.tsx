import React from "react"
import { createRoot } from "react-dom/client"
import ContributionSkyline, { type ContributionDay } from "../components/ui/contribution-skyline"
import "./styles.css"

function App() {
  const [data, setData] = React.useState<ContributionDay[] | null>(null)
  const [error, setError] = React.useState<string | null>(null)

  React.useEffect(() => {
    fetch("/contributions.json", { cache: "no-store" })
      .then((response) => {
        if (!response.ok) throw new Error("Contribution data is unavailable.")
        return response.json() as Promise<{ days?: ContributionDay[] }>
      })
      .then((payload) => {
        if (!Array.isArray(payload.days) || payload.days.length < 365) {
          throw new Error("Contribution data failed validation.")
        }
        setData(payload.days)
      })
      .catch((reason: unknown) => {
        setError(reason instanceof Error ? reason.message : "Contribution data failed to load.")
      })
  }, [])

  return (
    <main className="min-h-screen bg-[#080b10] px-3 py-8 text-[#f0f6fc] sm:px-6 sm:py-12">
      <div className="mx-auto w-full max-w-[1120px]">
        {error ? (
          <div className="rounded-xl border border-red-900 bg-[#160b0b] p-5 text-sm text-red-200" role="alert">
            {error}
          </div>
        ) : data ? (
          <ContributionSkyline
            data={data}
            defaultView="2d"
            palette="github"
            orbit
            showStats
            showLegend
            showToggle
            className="skyline-theme bg-[#0d1117] text-[#f0f6fc]"
          />
        ) : (
          <div className="rounded-xl border border-[#30363d] bg-[#0d1117] p-5 text-sm text-[#8b949e]">
            Loading contribution activity...
          </div>
        )}
      </div>
    </main>
  )
}

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
