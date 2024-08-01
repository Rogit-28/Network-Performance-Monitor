import json
import os
import csv
import io
from datetime import datetime
from typing import Dict, List, Any, Optional
from backend.comprehensive_logger.comprehensive_logger import ComprehensiveLogger


class LogExporter:
    """
    Export functionality for the comprehensive logging system.
    Provides attribute-based filtering and export capabilities for different formats.
    """
    
    def __init__(self, logger: ComprehensiveLogger):
        """
        Initialize the log exporter with a reference to the logger.
        
        Args:
            logger: ComprehensiveLogger instance to export logs from
        """
        self.logger = logger

    def export_logs(self, export_format: str = "json", attributes: List[str] = None,
                   start_time: datetime = None, end_time: datetime = None,
                   search_term: str = None, level_filter: str = None, metric_type: str = None):
        """
        Export logs in specified format with attribute-based filtering.
        
        Args:
            export_format: Format to export logs ("json" or "csv")
            attributes: List of attributes to include in export (None for all)
            start_time: Start time for filtering logs
            end_time: End time for filtering logs
            search_term: Term to search for in log entries
            level_filter: Log level to filter by (DEBUG, INFO, WARNING, ERROR)
            
        Returns:
            Exported data in the specified format
        """
        try:
            # Flush all pending writes to ensure the file is up-to-date
            for handler in self.logger.logger.handlers:
                if hasattr(handler, 'flush'):
                    handler.flush()
            
            # Create a temporary copy of the log file to avoid race conditions
            import tempfile
            import shutil
            with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.log') as temp_file:
                # Copy the current log file contents to the temporary file
                try:
                    with open(self.logger.log_file, 'r', encoding='utf-8') as original_file:
                        shutil.copyfileobj(original_file, temp_file)
                    temp_filename = temp_file.name
                except FileNotFoundError:
                    return None
            
            # Now read from the temporary copy to avoid file locking issues
            try:
                with open(temp_filename, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                filtered_logs = []
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                        
                    try:
                        log_entry = json.loads(line)
                        
                        # Apply time filtering
                        if start_time or end_time:
                            log_time = datetime.fromisoformat(log_entry['timestamp'].replace('Z', '+00:00'))
                            if start_time and log_time < start_time:
                                continue
                            if end_time and log_time > end_time:
                                continue
                        
                        # Apply search term filtering
                        if search_term:
                            if search_term.lower() not in json.dumps(log_entry).lower():
                                continue
                        
                        # Apply level filtering
                        if level_filter:
                            log_entry_level = log_entry.get('log_level', '').upper()
                            # Handle multiple log levels (comma-separated)
                            if log_entry_level != level_filter.upper():
                                level_filter_list = [level.strip().upper() for level in level_filter.split(',')]
                                if log_entry_level not in level_filter_list:
                                    continue
                                    
                        # Apply metric type filtering
                        if metric_type:
                            log_entry_metric_type = log_entry.get('metric_type', '').lower()
                            # Handle multiple metric types (comma-separated)
                            if log_entry_metric_type != metric_type.lower():
                                metric_types_list = [mt.strip().lower() for mt in metric_type.split(',')]
                                if log_entry_metric_type not in metric_types_list:
                                    continue
                                
                        # Apply attribute filtering
                        if attributes:
                            # Filter the log entry to only include specified attributes
                            filtered_entry = self._filter_attributes(log_entry, attributes)
                            filtered_logs.append(filtered_entry)
                        else:
                            filtered_logs.append(log_entry)
                            
                    except json.JSONDecodeError:
                        # Skip invalid JSON lines
                        continue

                if export_format.lower() == "csv":
                    return self._convert_to_csv(filtered_logs)
                else: # Default to JSON
                    return filtered_logs

            finally:
                # Clean up the temporary file
                os.unlink(temp_filename)

        except FileNotFoundError:
            return None
        except Exception as e:
            return None

    def _filter_attributes(self, log_entry: Dict[str, Any], attributes: List[str]) -> Dict[str, Any]:
        """
        Filter a log entry to only include specified attributes.
        
        Args:
            log_entry: The original log entry
            attributes: List of attributes to include
            
        Returns:
            Filtered log entry containing only specified attributes
        """
        filtered_entry = {}
        
        for attr in attributes:
            # Handle nested attributes using dot notation (e.g., "data.bytes_sent")
            if '.' in attr:
                parts = attr.split('.')
                current = log_entry
                found = True
                
                for part in parts:
                    if isinstance(current, dict) and part in current:
                        current = current[part]
                    else:
                        found = False
                        break
                
                if found:
                    # Reconstruct the nested structure in the filtered entry
                    self._set_nested_value(filtered_entry, attr, current)
            else:
                # Handle top-level attributes
                if attr in log_entry:
                    filtered_entry[attr] = log_entry[attr]
        
        return filtered_entry

    def _set_nested_value(self, data_dict: Dict, key_path: str, value: Any):
        """
        Set a value in a nested dictionary using dot notation.
        
        Args:
            data_dict: The dictionary to update
            key_path: The dot-separated path (e.g., "data.bytes_sent")
            value: The value to set
        """
        keys = key_path.split('.')
        current = data_dict
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value

    def _convert_to_csv(self, logs: List[Dict[str, Any]]) -> str:
        """
        Convert JSON logs to CSV format.
        
        Args:
            logs: List of log entries to convert
            
        Returns:
            CSV formatted string
        """
        if not logs:
            return ""
        
        # Get all possible keys from the logs to create CSV headers
        all_keys = set()
        for log in logs:
            # Add keys from nested 'data' field as well
            all_keys.update(log.keys())
            if 'data' in log and isinstance(log['data'], dict):
                all_keys.update([f"data.{k}" for k in log['data'].keys()])
        
        # Create a CSV string in memory
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=sorted(all_keys))
        writer.writeheader()
        for log in logs:
            # Flatten nested 'data' field to have keys like 'data.key'
            flat_log = {}
            for k, v in log.items():
                if k == 'data' and isinstance(v, dict):
                    for data_k, data_v in v.items():
                        flat_log[f"data.{data_k}"] = data_v
                else:
                    flat_log[k] = v
            writer.writerow(flat_log)
        csv_content = output.getvalue()
        output.close()
        return csv_content

    def export_by_level(self, level: str, export_format: str = "json", start_time: datetime = None, 
                       end_time: datetime = None, search_term: str = None):
        """
        Export logs by predefined level (macro, meso, micro).
        
        Args:
            level: Level of detail ("macro", "meso", "micro")
            export_format: Format to export logs ("json" or "csv")
            start_time: Start time for filtering logs
            end_time: End time for filtering logs
            search_term: Term to search for in log entries
            
        Returns:
            Exported data in the specified format
        """
        level_attributes = {
            "macro": [
                "timestamp",
                "metric_type",
                "data.interfaces.name",
                "data.interfaces.properties.bytes_sent",
                "data.interfaces.properties.bytes_received",
                "data.interfaces.performance.latency_ms",
                "data.interfaces.performance.throughput_mbps"
            ],
            "meso": [
                "timestamp",
                "log_level",
                "metric_type",
                "data.interfaces.name",
                "data.interfaces.type",
                "data.interfaces.status",
                "data.interfaces.properties.bytes_sent",
                "data.interfaces.properties.bytes_received",
                "data.interfaces.properties.packets_sent",
                "data.interfaces.properties.packets_received",
                "data.interfaces.performance.latency_ms",
                "data.interfaces.performance.throughput_mbps",
                "data.interfaces.performance.error_rates"
            ],
            "micro": [
                "log_id",
                "timestamp",
                "timestamp_epoch",
                "timezone",
                "log_level",
                "metric_category",
                "metric_type",
                "version",
                "system_info.platform",
                "system_info.hostname",
                "system_info.os_version",
                "system_info.python_version",
                "session_id",
                "data.interfaces.name",
                "data.interfaces.type",
                "data.interfaces.status",
                "data.interfaces.addresses.ipv4",
                "data.interfaces.addresses.ipv6",
                "data.interfaces.properties.is_up",
                "data.interfaces.properties.is_running",
                "data.interfaces.properties.bytes_sent",
                "data.interfaces.properties.bytes_received",
                "data.interfaces.properties.packets_sent",
                "data.interfaces.properties.packets_received",
                "data.interfaces.performance.latency_ms",
                "data.interfaces.performance.throughput_mbps",
                "data.interfaces.network_config.ipv4",
                "data.interfaces.network_config.ipv6",
                "data.interfaces.network_config.mac_address",
                "metadata.collection_method",
                "metadata.precision",
                "metadata.tags"
            ]
        }
        
        if level.lower() in level_attributes:
            return self.export_logs(
                export_format=export_format,
                attributes=level_attributes[level.lower()],
                start_time=start_time,
                end_time=end_time,
                search_term=search_term
            )
        else:
            raise ValueError(f"Invalid level: {level}. Use 'macro', 'meso', or 'micro'.")

    def export_custom_attributes(self, attributes: List[str], export_format: str = "json", 
                                start_time: datetime = None, end_time: datetime = None, 
                                search_term: str = None):
        """
        Export logs with user-specified attributes.
        
        Args:
            attributes: List of attributes to include in export
            export_format: Format to export logs ("json" or "csv")
            start_time: Start time for filtering logs
            end_time: End time for filtering logs
            search_term: Term to search for in log entries
            
        Returns:
            Exported data in the specified format
        """
        return self.export_logs(
            export_format=export_format,
            attributes=attributes,
            start_time=start_time,
            end_time=end_time,
            search_term=search_term
        )
