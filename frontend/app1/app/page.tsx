"use client"

import { useState } from "react"
import { Activity, BarChart3, Table2, FileText } from "lucide-react"
import { Button } from "@/components/ui/button"
import Dashboard from "@/components/dashboard"
import ChartMode from "@/components/chart-mode"
import TableMode from "@/components/table-mode"
import LoggingSection from "@/components/logging-section"
import { MetricsProvider } from "@/contexts/MetricsContext"

export default function Home() {
  const [mode, setMode] = useState<"dashboard" | "chart" | "table" | "logs">("dashboard")
  const [isLoading, setIsLoading] = useState(false)

  return (
    <MetricsProvider>
      <main className="min-h-screen bg-background text-foreground">
        {/* Header */}
        <div className="border-b border-border sticky top-0 z-50 bg-background/80 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded bg-accent/20 flex items-center justify-center">
                <Activity className="w-5 h-5 text-accent" />
              </div>
              <div>
                <h1 className="text-lg font-semibold tracking-tight">Network Monitor</h1>
                <p className="text-xs text-muted-foreground">Real-time performance tracking</p>
              </div>
            </div>

            {/* Mode Switcher */}
            <div className="flex items-center gap-2">
              <Button
                variant={mode === "dashboard" ? "default" : "ghost"}
                size="sm"
                onClick={() => setMode("dashboard")}
                className="gap-2"
              >
                <Activity className="w-4 h-4" />
                Dashboard
              </Button>
              <Button
                variant={mode === "chart" ? "default" : "ghost"}
                size="sm"
                onClick={() => setMode("chart")}
                className="gap-2"
              >
                <BarChart3 className="w-4 h-4" />
                Charts
              </Button>
              <Button
                variant={mode === "table" ? "default" : "ghost"}
                size="sm"
                onClick={() => setMode("table")}
                className="gap-2"
              >
                <Table2 className="w-4 h-4" />
                Table
              </Button>
            </div>
            <Button
              variant={mode === "logs" ? "default" : "ghost"}
              size="sm"
              onClick={() => setMode("logs")}
              className="gap-2"
            >
              <FileText className="w-4 h-4" />
              Log Export
            </Button>
          </div>
        </div>

        {/* Content */}
       <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
         {mode === "dashboard" && <Dashboard />}
         {mode === "chart" && <ChartMode />}
         {mode === "table" && <TableMode />}
         {mode === "logs" && <LoggingSection />}
       </div>
      </main>
    </MetricsProvider>
  )
}
