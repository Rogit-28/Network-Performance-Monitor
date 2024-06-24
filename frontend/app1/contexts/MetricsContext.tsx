"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import {
  fetchAllMetrics,
  fetchPerformanceMetrics,
  getAllInterfaces,
  convertHistoricalToChartData,
  getLatestMetrics,
  PerformanceMetric,
  NetworkInterface,
  AllMetrics,
  wsService,
  ChartDataPoint
} from '@/lib/api';

// Define the context type
interface MetricsContextType {
  metrics: PerformanceMetric[];
  interfaces: NetworkInterface[];
  chartData: ChartDataPoint[];
  latestMetrics: {
    latency: number;
    throughput: number;
    packetLoss: number;
    bandwidth: number;
  };
  avgLatency: number;
  avgThroughput: number;
  availableInterfaces: string[];
  loading: boolean;
  error: string | null;
  refreshData: () => Promise<void>;
  setSelectedInterfaces: (interfaces: string[]) => void;
  selectedInterfaces: string[];
}

// Create the context with default values
const MetricsContext = createContext<MetricsContextType | undefined>(undefined);

// Define props type for the provider
interface MetricsProviderProps {
  children: ReactNode;
}

export const MetricsProvider: React.FC<MetricsProviderProps> = ({ children }) => {
  const [metrics, setMetrics] = useState<PerformanceMetric[]>([]);
  const [interfaces, setInterfaces] = useState<NetworkInterface[]>([]);
  const [chartData, setChartData] = useState<ChartDataPoint[]>([]);
  const [latestMetrics, setLatestMetrics] = useState({
    latency: 0,
    throughput: 0,
    packetLoss: 0,
    bandwidth: 0
  });
  const [avgLatency, setAvgLatency] = useState(0);
  const [avgThroughput, setAvgThroughput] = useState(0);
  const [availableInterfaces, setAvailableInterfaces] = useState<string[]>([]);
  const [selectedInterfaces, setSelectedInterfaces] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch initial data
  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch all metrics at once
      const allMetrics: AllMetrics = await fetchAllMetrics();
      
      setMetrics(allMetrics.performance_metrics);
      setInterfaces(allMetrics.interfaces);
      
      // Convert metrics to chart data format
      const chartData = convertHistoricalToChartData([allMetrics]);
      setChartData(chartData);
      
      // Calculate latest metrics with selected interfaces
      const { latestMetric, avgLatency, avgThroughput } = getLatestMetrics(allMetrics.performance_metrics, selectedInterfaces);
      setLatestMetrics(latestMetric);
      setAvgLatency(avgLatency);
      setAvgThroughput(avgThroughput);
      
      // Get available interfaces
      const interfaceNames = allMetrics.interfaces.map(iface => iface.name);
      setAvailableInterfaces(interfaceNames);
    } catch (err) {
      console.error('Error fetching metrics:', err);
      setError('Failed to fetch network metrics');
      // Set empty values to prevent breaking the UI
      setMetrics([]);
      setInterfaces([]);
      setChartData([]);
      setLatestMetrics({ latency: 0, throughput: 0, packetLoss: 0, bandwidth: 0 });
      setAvgLatency(0);
      setAvgThroughput(0);
      setAvailableInterfaces([]);
    } finally {
      setLoading(false);
    }
  };

  // Set up WebSocket subscription for real-time updates
  useEffect(() => {
    // Fetch initial data
    fetchData();

    if (wsService) {
      const handleWebSocketUpdate = (data: any) => {
        // Handle new message format with both current and historical data
        if (data && data.current_data && data.historical_data) {
          // Update metrics and interfaces
          const currentData = data.current_data;
          setMetrics(currentData.performance_metrics);
          setInterfaces(currentData.interfaces);
          
          // Convert historical data to chart format
          const chartData = convertHistoricalToChartData(data.historical_data);
          setChartData(chartData);
          
          // Calculate latest metrics with selected interfaces
          const { latestMetric, avgLatency, avgThroughput } = getLatestMetrics(currentData.performance_metrics, selectedInterfaces);
          setLatestMetrics(latestMetric);
          setAvgLatency(avgLatency);
          setAvgThroughput(avgThroughput);
          
          // Update available interfaces
          const interfaceNames = currentData.interfaces.map((iface: NetworkInterface) => iface.name);
          setAvailableInterfaces(interfaceNames);
          
          // If selected interfaces is empty and we have new interfaces, select all of them
          if (selectedInterfaces.length === 0 && interfaceNames.length > 0) {
            setSelectedInterfaces(interfaceNames);
          }
        }
        // Handle legacy format (for compatibility)
        else if (data && data.performance_metrics && Array.isArray(data.performance_metrics)) {
          // Update metrics and interfaces
          setMetrics(data.performance_metrics);
          setInterfaces(data.interfaces || []);
          
          // Convert metrics to chart format
          const chartData = convertHistoricalToChartData([{
            performance_metrics: data.performance_metrics,
            interfaces: data.interfaces || [],
            timestamp: new Date().toISOString()
          }]);
          setChartData(chartData);
          
          // Calculate latest metrics with selected interfaces
          const { latestMetric, avgLatency, avgThroughput } = getLatestMetrics(data.performance_metrics, selectedInterfaces);
          setLatestMetrics(latestMetric);
          setAvgLatency(avgLatency);
          setAvgThroughput(avgThroughput);
          
          // Update available interfaces
          const interfaceNames = (data.interfaces || []).map((iface: NetworkInterface) => iface.name);
          setAvailableInterfaces(interfaceNames);
          
          // If selected interfaces is empty and we have new interfaces, select all of them
          if (selectedInterfaces.length === 0 && interfaceNames.length > 0) {
            setSelectedInterfaces(interfaceNames);
          }
        } else {
          console.warn("Invalid WebSocket data format:", data);
        }
      };

      wsService.subscribe('metrics-update', handleWebSocketUpdate);

      // Cleanup subscription on component unmount
      return () => {
        if (wsService) {
          wsService.unsubscribe('metrics-update', handleWebSocketUpdate);
        }
      };
    } else {
      console.warn("wsService is not available");
      setLoading(false);
    }
  }, []);
  
  // Effect to update selected interfaces when available interfaces change
  useEffect(() => {
    if (availableInterfaces.length > 0 && selectedInterfaces.length === 0) {
      setSelectedInterfaces(availableInterfaces);
    }
  }, [availableInterfaces, selectedInterfaces.length, setSelectedInterfaces]);

  const refreshData = async () => {
    await fetchData();
  };

   const value: MetricsContextType = {
     metrics,
     interfaces,
     chartData,
     latestMetrics,
     avgLatency,
     avgThroughput,
     availableInterfaces,
     selectedInterfaces,
     setSelectedInterfaces,
     loading,
     error,
     refreshData
   };

  return (
    <MetricsContext.Provider value={value}>
      {children}
    </MetricsContext.Provider>
  );
};

// Custom hook to use the MetricsContext
export const useMetrics = (): MetricsContextType => {
  const context = useContext(MetricsContext);
  if (context === undefined) {
    throw new Error('useMetrics must be used within a MetricsProvider');
  }
  return context;
};