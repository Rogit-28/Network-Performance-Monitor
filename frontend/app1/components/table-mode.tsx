"use client"

import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Download, Search } from "lucide-react"
import { useMetrics } from "@/contexts/MetricsContext"
import { MultiSelect } from "@/components/ui/multi-select"
import { exportLogs } from "@/lib/api";

interface NetworkMetric {
  id: string
  interface: string
 status: "active" | "inactive" | "warning"
  latency: number
 throughput: number
 packetLoss: number
 bandwidth: number
 timestamp: string
  ipv4?: string
  ipv6?: string
}

export default function TableMode() {
  const { metrics, interfaces, availableInterfaces, selectedInterfaces, setSelectedInterfaces, loading, error } = useMetrics()
  const [search, setSearch] = useState<string>("")

  // Initialize selected interfaces with all available interfaces when they load
  useEffect(() => {
    if (availableInterfaces.length > 0 && selectedInterfaces.length === 0) {
      setSelectedInterfaces(availableInterfaces);
    }
 }, [availableInterfaces, selectedInterfaces.length, setSelectedInterfaces]);

  // Transform the metrics data to match the NetworkMetric interface
  const transformedData: NetworkMetric[] = metrics.map((metric, index: number) => {
    // Find corresponding interface information
    const interfaceInfo = interfaces.find((iface: any) => iface.name === metric.interface)
    
    // Calculate packet loss based on actual packet data (same logic as in lib/api.ts)
    const sent = metric.packets_sent || 0;
    const recv = metric.packets_recv || 0;
    const packetLoss = sent > 0 ? ((sent - recv) / sent) * 100 : 0;
    
    // Calculate bandwidth based on actual bytes received (same logic as in lib/api.ts)
    const bandwidth = (metric.bytes_recv || 0) / (1024 * 1024); // Convert to MB
    
    return {
      id: `${index}`,
      interface: metric.interface,
      status: "active", // Default status, could be improved based on actual interface status
      latency: metric.latency || 0,
      throughput: metric.throughput || 0,
      packetLoss: Math.max(0, packetLoss), // Calculate based on actual packet data
      bandwidth: bandwidth, // Calculate based on actual bytes received
      timestamp: metric.timestamp,
      ipv4: interfaceInfo?.ipv4,
      ipv6: interfaceInfo?.ipv6,
    }
  })

 const filteredData = transformedData.filter(
    (row) =>
      (selectedInterfaces.includes(row.interface) || selectedInterfaces.length === 0) &&
      (row.interface.toLowerCase().includes(search.toLowerCase()) ||
      (row.ipv4 && row.ipv4.includes(search)) ||
      (row.ipv6 && row.ipv6.toLowerCase().includes(search.toLowerCase()))),
  )

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">Loading network interfaces...</p>
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

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active":
        return "bg-green-950/50 text-green-400 border-green-800"
      case "warning":
        return "bg-amber-950/50 text-amber-400 border-amber-800"
      case "inactive":
        return "bg-gray-950/50 text-gray-400 border-gray-800"
      default:
        return ""
    }
 }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold mb-1">Network Interfaces</h2>
        <p className="text-sm text-muted-foreground">Detailed view of all network interfaces and their metrics</p>
      </div>

      {/* Controls */}
      <Card className="p-4 border border-border bg-card/50">
        <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center justify-between">
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
            
            {/* Search */}
            <div className="relative flex-1 max-w-xs">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
              <Input
                placeholder="Search interfaces..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10 bg-input border-border text-foreground placeholder:text-muted-foreground"
              />
            </div>
          </div>
        </div>
      </Card>

      {/* Table */}
      <Card className="border border-border bg-card/50 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-card/30">
                <th className="px-6 py-3 text-left font-semibold text-muted-foreground">Interface</th>
                <th className="px-6 py-3 text-left font-semibold text-muted-foreground">Status</th>
                <th className="px-6 py-3 text-right font-semibold text-muted-foreground">Latency (ms)</th>
                <th className="px-6 py-3 text-right font-semibold text-muted-foreground">Throughput (Mbps)</th>
                <th className="px-6 py-3 text-right font-semibold text-muted-foreground">Packet Loss (%)</th>
                <th className="px-6 py-3 text-right font-semibold text-muted-foreground">Bandwidth (MB)</th>
                <th className="px-6 py-3 text-left font-semibold text-muted-foreground">IPv4</th>
                <th className="px-6 py-3 text-left font-semibold text-muted-foreground">IPv6</th>
              </tr>
            </thead>
            <tbody>
              {filteredData.map((row) => (
                <tr key={row.id} className="border-b border-border/50 hover:bg-card/50 transition-colors">
                  <td className="px-6 py-4 font-mono text-foreground">{row.interface}</td>
                  <td className="px-6 py-4">
                    <Badge variant="outline" className={`${getStatusColor(row.status)} capitalize text-xs`}>
                      {row.status}
                    </Badge>
                  </td>
                  <td className="px-6 py-4 text-right">{row.latency.toFixed(2)}ms</td>
                  <td className="px-6 py-4 text-right">{row.throughput.toFixed(1)}Mbps</td>
                  <td className="px-6 py-4 text-right">{row.packetLoss.toFixed(2)}%</td>
                  <td className="px-6 py-4 text-right">{row.bandwidth.toFixed(0)}MB</td>
                  <td className="px-6 py-4 font-mono text-xs text-muted-foreground">{row.ipv4 || 'N/A'}</td>
                  <td className="px-6 py-4 font-mono text-xs text-muted-foreground">{row.ipv6 || 'N/A'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="px-6 py-3 border-t border-border text-xs text-muted-foreground bg-card/30">
          Showing {filteredData.length} of {transformedData.length} interfaces
        </div>
      </Card>
    </div>
  )
}
