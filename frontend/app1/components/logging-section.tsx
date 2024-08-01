"use client";

import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Download,
  Search,
  Calendar,
  Filter,
  Clock,
  Eye,
  EyeOff
} from "lucide-react";
import {
  fetchLogs,
   exportLogs,
   getLogLevels,
   getMetricTypes,
   LogEntry,
   LogQueryParams
} from "@/lib/api";
import { MultiSelect } from "@/components/ui/multi-select";
import {
 Popover,
   PopoverContent,
   PopoverTrigger,
} from "@/components/ui/popover";
import { DateTimePicker } from "@/components/ui/date-picker";
import { format } from "date-fns";

interface LoggingSectionProps {
  className?: string;
}

export default function LoggingSection({ className }: LoggingSectionProps) {
   // Filter states
   const programStartTime = new Date('2025-01-01'); // Set to an appropriate program start time
   const [startTime, setStartTime] = useState<Date | undefined>(undefined);
   const [endTime, setEndTime] = useState<Date | undefined>(undefined);
   const [logLevels, setLogLevels] = useState<string[]>([]);
   const [availableLogLevels, setAvailableLogLevels] = useState<string[]>([]);
   const [metricTypes, setMetricTypes] = useState<string[]>([]);
   const [availableMetricTypes, setAvailableMetricTypes] = useState<string[]>([]);
   const [searchTerm, setSearchTerm] = useState<string>("");
  
  // Data states
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  
  // UI states
  const [expandedLogId, setExpandedLogId] = useState<string | null>(null);
  const [exportLoading, setExportLoading] = useState<boolean>(false);

  // Fetch available log levels and metric types on component mount
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [levels, types] = await Promise.all([
          getLogLevels(),
          getMetricTypes()
        ]);
        setAvailableLogLevels(levels);
        setAvailableMetricTypes(types);
      } catch (err) {
        console.error("Error fetching log metadata:", err);
        setError("Failed to fetch log metadata");
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);

  // Fetch logs based on current filters
  const fetchFilteredLogs = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Build query params
     const queryParams: LogQueryParams = {
       start_time: startTime ? startTime.toISOString() : undefined,
       end_time: endTime ? endTime.toISOString() : undefined,
       log_level: logLevels.length > 0 ? logLevels.join(",") : undefined,
       metric_type: metricTypes.length > 0 ? metricTypes.join(",") : undefined,
       search_term: searchTerm || undefined
     };
      
      const fetchedLogs = await fetchLogs(queryParams);
      setLogs(fetchedLogs);
    } catch (err) {
      console.error("Error fetching logs:", err);
      setError("Failed to fetch logs");
    } finally {
      setLoading(false);
    }
  };

  // Handle form submission
 const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchFilteredLogs();
  };

  // Export logs with current filters
  const handleExport = async (format: "json" | "csv" = "json") => {
    setExportLoading(true);
    
    try {
      // Build query params
      const queryParams: LogQueryParams = {
        start_time: startTime ? startTime.toISOString() : undefined,
        end_time: endTime ? endTime.toISOString() : undefined,
        log_level: logLevels.length > 0 ? logLevels.join(",") : undefined,
        metric_type: metricTypes.length > 0 ? metricTypes.join(",") : undefined,
        search_term: searchTerm || undefined
      };
      
      await exportLogs(queryParams, format);
    } catch (err) {
      console.error("Error exporting logs:", err);
      setError("Failed to export logs");
    } finally {
      setExportLoading(false);
    }
 };

  // Toggle log entry expansion
 const toggleLogExpansion = (logId: string) => {
    setExpandedLogId(expandedLogId === logId ? null : logId);
  };

 // Get log level color
  const getLogLevelColor = (level: string) => {
    switch (level?.toUpperCase()) {
      case "ERROR":
        return "bg-red-950/50 text-red-400 border-red-800";
      case "WARNING":
        return "bg-amber-950/50 text-amber-400 border-amber-800";
      case "INFO":
        return "bg-blue-950/50 text-blue-400 border-blue-800";
      case "DEBUG":
        return "bg-purple-950/50 text-purple-400 border-purple-800";
      default:
        return "bg-gray-950/50 text-gray-400 border-gray-800";
    }
  };

  return (
    <div className={className}>
      <div className="mb-6">
        <h2 className="text-2xl font-semibold mb-1">Log Export</h2>
        <p className="text-sm text-muted-foreground">
          View, filter, and export network performance logs and metrics
        </p>
      </div>

      {/* Filter Controls */}
      <Card className="p-4 border border-border bg-card/50 mb-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Date Range */}
            <div className="flex flex-col gap-2">
              <label className="text-sm font-medium text-muted-foreground flex items-center gap-1">
                <Calendar className="w-4 h-4" />
                Start Date
              </label>
              <DateTimePicker
                date={startTime}
                setDate={setStartTime}
                minDate={programStartTime}
                placeholder="Select start date and time"
                className="bg-input border-border text-foreground placeholder:text-muted-foreground"
              />
            </div>
            
            <div className="flex flex-col gap-2">
              <label className="text-sm font-medium text-muted-foreground flex items-center gap-1">
                <Clock className="w-4 h-4" />
                End Date
              </label>
              <DateTimePicker
                date={endTime}
                setDate={setEndTime}
                minDate={programStartTime}
                placeholder="Select end date and time"
                className="bg-input border-border text-foreground placeholder:text-muted-foreground"
              />
            </div>
            
            {/* Log Levels */}
            <div className="flex flex-col gap-2">
              <label className="text-sm font-medium text-muted-foreground flex items-center gap-1">
                <Filter className="w-4 h-4" />
                Log Levels
              </label>
              <MultiSelect
                options={availableLogLevels.map(level => ({ value: level, label: level.toUpperCase() }))}
                selected={logLevels}
                onChange={setLogLevels}
                placeholder="Select log levels..."
              />
            </div>
            
            {/* Metric Types */}
            <div className="flex flex-col gap-2">
              <label className="text-sm font-medium text-muted-foreground flex items-center gap-1">
                <Filter className="w-4 h-4" />
                Metric Types
              </label>
              <MultiSelect
                options={availableMetricTypes.map(type => ({ value: type, label: type.charAt(0).toUpperCase() + type.slice(1) }))}
                selected={metricTypes}
                onChange={setMetricTypes}
                placeholder="Select metric types..."
              />
            </div>
          </div>
          
          {/* Search Term */}
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
            <Input
              placeholder="Search in logs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 bg-input border-border text-foreground placeholder:text-muted-foreground"
            />
          </div>
          
          {/* Action Buttons */}
          <div className="flex flex-wrap gap-3">
            <Button
              type="submit"
              variant="default"
              disabled={loading}
              className="gap-2"
            >
              <Filter className="w-4 h-4" />
              {loading ? "Filtering..." : "Apply Filters"}
            </Button>
            
            <Popover>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  size="sm"
                  className="gap-2"
                  disabled={exportLoading}
                >
                  <Download className="w-4 h-4" />
                  {exportLoading ? "Exporting..." : "Export"}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-48 p-2">
                <div className="flex flex-col gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="justify-start"
                    onClick={() => handleExport("json")}
                    disabled={exportLoading}
                  >
                    Export Logs as JSON
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="justify-start"
                    onClick={() => handleExport("csv")}
                    disabled={exportLoading}
                  >
                    Export Logs as CSV
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="justify-start"
                    onClick={() => exportLogs({ metric_type: "interface_metrics" }, "csv")}
                    disabled={exportLoading}
                  >
                    Export Metrics as CSV
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="justify-start"
                    onClick={() => exportLogs({ metric_type: "interface_metrics" }, "json")}
                    disabled={exportLoading}
                  >
                    Export Metrics as JSON
                  </Button>
                </div>
              </PopoverContent>
            </Popover>
          </div>
        </form>
      </Card>

      {/* Logs Display */}
      {error && (
        <div className="mb-6">
          <Card className="p-4 border border-destructive/50 bg-destructive/10">
            <p className="text-destructive">{error}</p>
          </Card>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <p className="text-muted-foreground">Loading logs...</p>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-medium">Log Entries</h3>
            <p className="text-sm text-muted-foreground">
              Showing {logs.length} log entries
            </p>
          </div>
          
          {logs.length === 0 ? (
            <Card className="p-8 border border-border bg-card/30 text-center">
              <p className="text-muted-foreground">No logs match the current filters</p>
            </Card>
          ) : (
            <div className="space-y-3">
              {logs.map((log) => (
                <Card 
                  key={log.log_id} 
                  className="border border-border bg-card/50 overflow-hidden"
                >
                  <div className="p-4">
                    <div className="flex flex-wrap items-center justify-between gap-3 mb-2">
                      <div className="flex items-center gap-3">
                        <Badge className={`${getLogLevelColor(log.log_level)} capitalize text-xs`}>
                          {log.log_level}
                        </Badge>
                        <span className="text-xs text-muted-foreground font-mono">
                          {log.metric_type}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {format(new Date(log.timestamp), 'yyyy-MM-dd HH:mm:ss')}
                        </span>
                      </div>
                      
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleLogExpansion(log.log_id)}
                        className="h-7 w-7 p-0"
                      >
                        {expandedLogId === log.log_id ? (
                          <EyeOff className="w-4 h-4" />
                        ) : (
                          <Eye className="w-4 h-4" />
                        )}
                      </Button>
                    </div>
                    
                    <div className="text-sm text-muted-foreground mb-2">
                      <span className="font-mono">{log.session_id}</span>
                    </div>
                    
                    {expandedLogId === log.log_id && (
                      <div className="mt-3 pt-3 border-t border-border text-xs">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <h4 className="font-medium mb-2">Data</h4>
                            <pre className="bg-muted p-2 rounded overflow-auto max-h-40">
                              {JSON.stringify(log.data, null, 2)}
                            </pre>
                          </div>
                          
                          <div>
                            <h4 className="font-medium mb-2">System Info</h4>
                            <pre className="bg-muted p-2 rounded overflow-auto max-h-40">
                              {JSON.stringify(log.system_info, null, 2)}
                            </pre>
                          </div>
                        </div>
                        
                        <div className="mt-3">
                          <h4 className="font-medium mb-2">Metadata</h4>
                          <pre className="bg-muted p-2 rounded overflow-auto max-h-32">
                            {JSON.stringify(log.metadata, null, 2)}
                          </pre>
                        </div>
                      </div>
                    )}
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}