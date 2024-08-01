"use client"

import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from "recharts"
import { Wifi, Zap, TrendingUp, Server } from "lucide-react"
import { useMetrics } from "@/contexts/MetricsContext"
import { MultiSelect } from "@/components/ui/multi-select"

export default function Dashboard() {
  const { chartData, latestMetrics, avgLatency, avgThroughput, availableInterfaces, loading, error, selectedInterfaces, setSelectedInterfaces } = useMetrics()

  // Initialize selected interfaces with all available interfaces when they load
  useEffect(() => {
    if (availableInterfaces.length > 0 && selectedInterfaces.length === 0) {
      setSelectedInterfaces(availableInterfaces);
    }
 }, [availableInterfaces, selectedInterfaces.length, setSelectedInterfaces]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">Loading network metrics...</p>
      </div>
    )
  }

 if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-destructive">Error: {error}</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold mb-1">Network Performance Dashboard</h2>
          <p className="text-sm text-muted-foreground">Real-time monitoring of network interfaces and performance metrics</p>
        </div>
        
        <div className="flex flex-wrap gap-3">
          {/* Interface Selection */}
          <div className="flex flex-col gap-2 w-64">
            <label className="text-sm font-medium text-muted-foreground">Select Interfaces</label>
            <MultiSelect
              options={availableInterfaces.map(iface => ({ value: iface, label: iface }))}
              selected={selectedInterfaces}
              onChange={setSelectedInterfaces}
              placeholder="Select interfaces..."
            />
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4 border border-border bg-card/50">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs text-muted-foreground mb-1">Current Latency</p>
              <p className="text-2xl font-semibold">{latestMetrics.latency.toFixed(1)}ms</p>
              <Badge variant="outline" className="mt-2 text-xs">
                {latestMetrics.latency < 50 ? "Optimal" : latestMetrics.latency < 10 ? "Good" : "High"}
              </Badge>
            </div>
            <Zap className="w-5 h-5 text-muted-foreground" />
          </div>
        </Card>

        <Card className="p-4 border border-border bg-card/50">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs text-muted-foreground mb-1">Throughput</p>
              <p className="text-2xl font-semibold">{latestMetrics.throughput.toFixed(0)}Mbps</p>
              <Badge variant="outline" className="mt-2 text-xs">
                {latestMetrics.throughput > 100 ? "High" : latestMetrics.throughput > 50 ? "Medium" : "Low"}
              </Badge>
            </div>
            <TrendingUp className="w-5 h-5 text-muted-foreground" />
          </div>
        </Card>

        <Card className="p-4 border border-border bg-card/50">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs text-muted-foreground mb-1">Packet Loss</p>
              <p className="text-2xl font-semibold">{latestMetrics.packetLoss.toFixed(2)}%</p>
              <Badge variant="outline" className="mt-2 text-xs">
                {latestMetrics.packetLoss < 0.1 ? "Excellent" : latestMetrics.packetLoss < 1 ? "Good" : "High"}
              </Badge>
            </div>
            <Wifi className="w-5 h-5 text-muted-foreground" />
          </div>
        </Card>

        <Card className="p-4 border border-border bg-card/50">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs text-muted-foreground mb-1">Bandwidth</p>
              <p className="text-2xl font-semibold">{latestMetrics.bandwidth.toFixed(0)}MB</p>
              <Badge variant="outline" className="mt-2 text-xs">
                Healthy
              </Badge>
            </div>
            <Server className="w-5 h-5 text-muted-foreground" />
          </div>
        </Card>
      </div>

      {/* Legend for all charts */}
      <div className="flex flex-wrap gap-4 p-4 bg-card border border-border rounded-lg">
        <h3 className="text-sm font-semibold w-full">Legend:</h3>
        {selectedInterfaces.map((iface, index) => (
          <div key={iface} className="flex items-center gap-2">
            <div
              className="w-4 h-4 rounded-full"
              style={{ backgroundColor: `hsl(${index * 137.5}, 70%, 50%)` }}
            ></div>
            <span className="text-sm">{iface}</span>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6 border border-border bg-card/50">
          <h3 className="text-sm font-semibold mb-4">Latency Comparison (ms)</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--tw-bg-opacity: var(--border))" />
              <XAxis dataKey="time" stroke="var(--muted-foreground)" style={{ fontSize: "12px" }} />
              <YAxis stroke="var(--muted-foreground)" style={{ fontSize: "12px" }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "var(--card)",
                  border: "1px solid var(--border)",
                  borderRadius: "4px",
                }}
              />
              {selectedInterfaces.map((iface, index) => (
                <Line
                  key={iface}
                  type="monotone"
                  dataKey={`latency_${iface}`}
                  stroke={`hsl(${index * 137.5}, 70%, 50%)`} // Different color for each interface
                  strokeWidth={2}
                  dot={false}
                  name={iface}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </Card>

        <Card className="p-6 border border-border bg-card/50">
          <h3 className="text-sm font-semibold mb-4">Throughput Comparison (Mbps)</h3>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={chartData}>
              <defs>
                {selectedInterfaces.map((iface, index) => (
                  <linearGradient key={iface} id={`colorThroughput-${iface}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={`hsl(${index * 137.5}, 70%, 50%)`} stopOpacity={0.8} />
                    <stop offset="95%" stopColor={`hsl(${index * 137.5}, 70%, 50%)`} stopOpacity={0} />
                  </linearGradient>
                ))}
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--tw-bg-opacity: var(--border))" />
              <XAxis dataKey="time" stroke="var(--muted-foreground)" style={{ fontSize: "12px" }} />
              <YAxis stroke="var(--muted-foreground)" style={{ fontSize: "12px" }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "var(--card)",
                  border: "1px solid var(--border)",
                  borderRadius: "4px",
                }}
              />
              {selectedInterfaces.map((iface, index) => (
                <Area
                  key={iface}
                  type="monotone"
                  dataKey={`throughput_${iface}`}
                  stroke={`hsl(${index * 137.5}, 70%, 50%)`}
                  fillOpacity={1}
                  fill={`url(#colorThroughput-${iface})`}
                  name={iface}
                />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        </Card>
      </div>
    </div>
  )
}
