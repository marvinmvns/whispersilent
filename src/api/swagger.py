"""
OpenAPI/Swagger documentation for WhisperSilent HTTP API
"""
import os
from config import Config

def get_swagger_spec():
    """Get OpenAPI/Swagger specification with dynamic server URL"""
    host = Config.HTTP_SERVER["host"]
    port = Config.HTTP_SERVER["port"]
    
    return {
    "openapi": "3.0.0",
    "info": {
        "title": "WhisperSilent API",
        "description": "Real-time transcription system API for monitoring, control, and data retrieval",
        "version": "1.0.0",
        "contact": {
            "name": "WhisperSilent",
            "url": "https://github.com/whispersilent"
        }
    },
    "servers": [
        {
            "url": f"http://{host}:{port}",
            "description": "API Server"
        }
    ],
    "paths": {
        "/health": {
            "get": {
                "summary": "Basic health check",
                "description": "Returns basic system health status and summary metrics",
                "tags": ["Health"],
                "responses": {
                    "200": {
                        "description": "System health status",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HealthSummary"
                                },
                                "example": {
                                    "status": "healthy",
                                    "timestamp": 1704067200.0,
                                    "uptime_seconds": 3600,
                                    "summary": {
                                        "pipeline_running": True,
                                        "total_transcriptions": 45,
                                        "cpu_usage": 25.5,
                                        "memory_usage": 65.2,
                                        "recent_errors_count": 0,
                                        "api_success_rate": 98.5
                                    }
                                }
                            }
                        }
                    },
                    "503": {
                        "description": "Service unavailable"
                    }
                }
            }
        },
        "/health/detailed": {
            "get": {
                "summary": "Detailed health information",
                "description": "Returns comprehensive system health information including component status, metrics, and recent errors",
                "tags": ["Health"],
                "responses": {
                    "200": {
                        "description": "Detailed health information",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/DetailedHealth"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/status": {
            "get": {
                "summary": "Pipeline status",
                "description": "Returns current pipeline and configuration status",
                "tags": ["Status"],
                "responses": {
                    "200": {
                        "description": "Pipeline status",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/PipelineStatus"
                                },
                                "example": {
                                    "pipeline_running": True,
                                    "api_sending_enabled": True,
                                    "uptime_seconds": 3600,
                                    "timestamp": 1704067200.0
                                }
                            }
                        }
                    }
                }
            }
        },
        "/transcriptions": {
            "get": {
                "summary": "List transcriptions",
                "description": "Retrieve transcriptions with optional filtering and pagination",
                "tags": ["Transcriptions"],
                "parameters": [
                    {
                        "name": "limit",
                        "in": "query",
                        "description": "Maximum number of transcriptions to return",
                        "schema": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 1000,
                            "default": 100
                        }
                    },
                    {
                        "name": "recent_minutes",
                        "in": "query",
                        "description": "Only return transcriptions from the last N minutes",
                        "schema": {
                            "type": "integer",
                            "minimum": 1
                        }
                    },
                    {
                        "name": "start_time",
                        "in": "query",
                        "description": "Start time as Unix timestamp",
                        "schema": {
                            "type": "number"
                        }
                    },
                    {
                        "name": "end_time",
                        "in": "query",
                        "description": "End time as Unix timestamp",
                        "schema": {
                            "type": "number"
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "List of transcriptions",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/TranscriptionList"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/transcriptions/search": {
            "get": {
                "summary": "Search transcriptions",
                "description": "Search transcriptions by text content",
                "tags": ["Transcriptions"],
                "parameters": [
                    {
                        "name": "q",
                        "in": "query",
                        "required": True,
                        "description": "Search query",
                        "schema": {
                            "type": "string"
                        }
                    },
                    {
                        "name": "case_sensitive",
                        "in": "query",
                        "description": "Whether search should be case sensitive",
                        "schema": {
                            "type": "boolean",
                            "default": False
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Search results",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/SearchResults"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/transcriptions/statistics": {
            "get": {
                "summary": "Get transcription statistics",
                "description": "Returns statistical information about stored transcriptions",
                "tags": ["Transcriptions"],
                "responses": {
                    "200": {
                        "description": "Transcription statistics",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/TranscriptionStatistics"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/transcriptions/{id}": {
            "get": {
                "summary": "Get specific transcription",
                "description": "Retrieve a specific transcription by ID",
                "tags": ["Transcriptions"],
                "parameters": [
                    {
                        "name": "id",
                        "in": "path",
                        "required": True,
                        "description": "Transcription ID",
                        "schema": {
                            "type": "string"
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Transcription details",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/Transcription"
                                }
                            }
                        }
                    },
                    "404": {
                        "description": "Transcription not found"
                    }
                }
            }
        },
        "/transcriptions/export": {
            "post": {
                "summary": "Export transcriptions",
                "description": "Export all transcriptions to a JSON file",
                "tags": ["Export"],
                "responses": {
                    "200": {
                        "description": "Export successful",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "message": {"type": "string"},
                                        "filename": {"type": "string"},
                                        "timestamp": {"type": "number"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/transcriptions/send-unsent": {
            "post": {
                "summary": "Send unsent transcriptions",
                "description": "Manually send all transcriptions that haven't been sent to the API",
                "tags": ["API Control"],
                "responses": {
                    "200": {
                        "description": "Send operation completed",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "message": {"type": "string"},
                                        "sent_count": {"type": "integer"},
                                        "failed_count": {"type": "integer"},
                                        "timestamp": {"type": "number"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/control/toggle-api-sending": {
            "post": {
                "summary": "Toggle API sending",
                "description": "Enable or disable automatic sending of transcriptions to external API",
                "tags": ["Control"],
                "responses": {
                    "200": {
                        "description": "API sending toggled",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "message": {"type": "string"},
                                        "api_sending_enabled": {"type": "boolean"},
                                        "timestamp": {"type": "number"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/control/start": {
            "post": {
                "summary": "Start pipeline",
                "description": "Start the transcription pipeline",
                "tags": ["Control"],
                "responses": {
                    "200": {
                        "description": "Pipeline started",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ControlResponse"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/control/stop": {
            "post": {
                "summary": "Stop pipeline",
                "description": "Stop the transcription pipeline",
                "tags": ["Control"],
                "responses": {
                    "200": {
                        "description": "Pipeline stopped",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ControlResponse"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/aggregation/status": {
            "get": {
                "summary": "Get aggregation status",
                "description": "Returns current hourly aggregation status and progress",
                "tags": ["Aggregation"],
                "responses": {
                    "200": {
                        "description": "Aggregation status",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/AggregationStatus"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/aggregation/texts": {
            "get": {
                "summary": "List aggregated texts",
                "description": "Retrieve completed hourly aggregated texts",
                "tags": ["Aggregation"],
                "parameters": [
                    {
                        "name": "limit",
                        "in": "query",
                        "description": "Maximum number of aggregated texts to return",
                        "schema": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 100,
                            "default": 10
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "List of aggregated texts",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {
                                        "$ref": "#/components/schemas/AggregatedText"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/aggregation/texts/{hour_timestamp}": {
            "get": {
                "summary": "Get aggregated text by hour",
                "description": "Retrieve aggregated text for a specific hour",
                "tags": ["Aggregation"],
                "parameters": [
                    {
                        "name": "hour_timestamp",
                        "in": "path",
                        "required": true,
                        "description": "Hour timestamp (Unix timestamp)",
                        "schema": {
                            "type": "number"
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Aggregated text",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/AggregatedText"
                                }
                            }
                        }
                    },
                    "404": {
                        "description": "Aggregated text not found"
                    }
                }
            }
        },
        "/aggregation/finalize": {
            "post": {
                "summary": "Force finalize current aggregation",
                "description": "Manually trigger finalization of the current hour's aggregation",
                "tags": ["Aggregation"],
                "responses": {
                    "200": {
                        "description": "Aggregation finalized",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/AggregatedText"
                                }
                            }
                        }
                    },
                    "400": {
                        "description": "No current transcriptions to finalize"
                    }
                }
            }
        },
        "/aggregation/toggle": {
            "post": {
                "summary": "Toggle aggregation",
                "description": "Enable or disable hourly aggregation",
                "tags": ["Aggregation"],
                "parameters": [
                    {
                        "name": "enabled",
                        "in": "query",
                        "required": true,
                        "description": "Whether to enable or disable aggregation",
                        "schema": {
                            "type": "boolean"
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Aggregation toggled",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "message": {"type": "string"},
                                        "enabled": {"type": "boolean"},
                                        "timestamp": {"type": "number"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/aggregation/statistics": {
            "get": {
                "summary": "Get aggregation statistics",
                "description": "Returns statistical information about hourly aggregations",
                "tags": ["Aggregation"],
                "responses": {
                    "200": {
                        "description": "Aggregation statistics",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/AggregationStatistics"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/aggregation/send-unsent": {
            "post": {
                "summary": "Send unsent aggregated texts",
                "description": "Manually send all aggregated texts that haven't been sent to the API",
                "tags": ["Aggregation"],
                "responses": {
                    "200": {
                        "description": "Send operation completed",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "message": {"type": "string"},
                                        "sent_count": {"type": "integer"},
                                        "failed_count": {"type": "integer"},
                                        "timestamp": {"type": "number"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    },
    "components": {
        "schemas": {
            "HealthSummary": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["healthy", "degraded", "unhealthy"]
                    },
                    "timestamp": {"type": "number"},
                    "uptime_seconds": {"type": "number"},
                    "summary": {
                        "type": "object",
                        "properties": {
                            "pipeline_running": {"type": "boolean"},
                            "total_transcriptions": {"type": "integer"},
                            "cpu_usage": {"type": "number"},
                            "memory_usage": {"type": "number"},
                            "recent_errors_count": {"type": "integer"},
                            "api_success_rate": {"type": "number"}
                        }
                    }
                }
            },
            "DetailedHealth": {
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "timestamp": {"type": "number"},
                    "uptime_seconds": {"type": "number"},
                    "system_metrics": {
                        "type": "object",
                        "properties": {
                            "cpu_percent": {"type": "number"},
                            "memory_percent": {"type": "number"},
                            "memory_used_mb": {"type": "number"},
                            "memory_total_mb": {"type": "number"},
                            "disk_usage_percent": {"type": "number"},
                            "process_threads": {"type": "integer"},
                            "process_memory_mb": {"type": "number"}
                        }
                    },
                    "transcription_metrics": {
                        "type": "object",
                        "properties": {
                            "total_chunks_processed": {"type": "integer"},
                            "successful_transcriptions": {"type": "integer"},
                            "failed_transcriptions": {"type": "integer"},
                            "api_requests_sent": {"type": "integer"},
                            "api_requests_failed": {"type": "integer"},
                            "average_processing_time_ms": {"type": "number"},
                            "last_transcription_time": {"type": "number"},
                            "last_api_call_time": {"type": "number"},
                            "uptime_seconds": {"type": "number"}
                        }
                    },
                    "component_status": {
                        "type": "object",
                        "properties": {
                            "audio_capture_active": {"type": "boolean"},
                            "audio_processor_active": {"type": "boolean"},
                            "whisper_service_active": {"type": "boolean"},
                            "api_service_active": {"type": "boolean"},
                            "pipeline_running": {"type": "boolean"},
                            "whisper_model_loaded": {"type": "boolean"}
                        }
                    },
                    "recent_errors": {"type": "array"},
                    "performance_warnings": {"type": "array"}
                }
            },
            "PipelineStatus": {
                "type": "object",
                "properties": {
                    "pipeline_running": {"type": "boolean"},
                    "api_sending_enabled": {"type": "boolean"},
                    "uptime_seconds": {"type": "number"},
                    "timestamp": {"type": "number"}
                }
            },
            "Transcription": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "text": {"type": "string"},
                    "timestamp": {"type": "number"},
                    "processing_time_ms": {"type": "number"},
                    "chunk_size": {"type": "integer"},
                    "api_sent": {"type": "boolean"},
                    "api_sent_timestamp": {"type": "number"},
                    "confidence": {"type": "number"},
                    "language": {"type": "string"}
                }
            },
            "TranscriptionList": {
                "type": "object",
                "properties": {
                    "transcriptions": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/Transcription"}
                    },
                    "total_count": {"type": "integer"},
                    "timestamp": {"type": "number"}
                }
            },
            "SearchResults": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "case_sensitive": {"type": "boolean"},
                    "results": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/Transcription"}
                    },
                    "total_matches": {"type": "integer"},
                    "timestamp": {"type": "number"}
                }
            },
            "TranscriptionStatistics": {
                "type": "object",
                "properties": {
                    "total_records": {"type": "integer"},
                    "sent_to_api": {"type": "integer"},
                    "pending_api_send": {"type": "integer"},
                    "average_processing_time_ms": {"type": "number"},
                    "oldest_timestamp": {"type": "number"},
                    "newest_timestamp": {"type": "number"},
                    "total_characters": {"type": "integer"},
                    "api_send_rate": {"type": "number"}
                }
            },
            "ControlResponse": {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "pipeline_running": {"type": "boolean"},
                    "timestamp": {"type": "number"}
                }
            },
            "AggregationStatus": {
                "type": "object",
                "properties": {
                    "enabled": {"type": "boolean"},
                    "running": {"type": "boolean"},
                    "current_hour_start": {"type": "number"},
                    "current_hour_formatted": {"type": "string"},
                    "current_transcription_count": {"type": "integer"},
                    "current_partial_text": {"type": "string"},
                    "current_partial_length": {"type": "integer"},
                    "last_transcription_time": {"type": "number"},
                    "last_transcription_formatted": {"type": "string"},
                    "minutes_since_last": {"type": "number"},
                    "total_aggregated_hours": {"type": "integer"},
                    "min_silence_gap_minutes": {"type": "integer"}
                }
            },
            "AggregatedText": {
                "type": "object",
                "properties": {
                    "hour_timestamp": {"type": "number"},
                    "start_time": {"type": "number"},
                    "end_time": {"type": "number"},
                    "full_text": {"type": "string"},
                    "transcription_count": {"type": "integer"},
                    "silence_gaps": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "start_time": {"type": "number"},
                                "end_time": {"type": "number"},
                                "duration_seconds": {"type": "number"},
                                "duration_minutes": {"type": "number"}
                            }
                        }
                    },
                    "metadata": {
                        "type": "object",
                        "properties": {
                            "finalization_reason": {"type": "string"},
                            "total_duration_minutes": {"type": "number"},
                            "average_gap_seconds": {"type": "number"},
                            "word_count": {"type": "integer"},
                            "character_count": {"type": "integer"}
                        }
                    },
                    "sent_to_api": {"type": "boolean"},
                    "created_at": {"type": "number"}
                }
            },
            "AggregationStatistics": {
                "type": "object",
                "properties": {
                    "total_aggregated_hours": {"type": "integer"},
                    "total_transcriptions_aggregated": {"type": "integer"},
                    "total_characters_aggregated": {"type": "integer"},
                    "sent_to_api_count": {"type": "integer"},
                    "pending_api_send": {"type": "integer"},
                    "average_transcriptions_per_hour": {"type": "number"},
                    "average_characters_per_hour": {"type": "number"},
                    "current_period_transcriptions": {"type": "integer"},
                    "current_period_characters": {"type": "integer"},
                    "enabled": {"type": "boolean"},
                    "running": {"type": "boolean"}
                }
            }
        }
    },
    "tags": [
        {
            "name": "Health",
            "description": "System health monitoring"
        },
        {
            "name": "Status",
            "description": "Pipeline and configuration status"
        },
        {
            "name": "Transcriptions",
            "description": "Transcription data retrieval and search"
        },
        {
            "name": "Export",
            "description": "Data export functionality"
        },
        {
            "name": "Control",
            "description": "Pipeline control operations"
        },
        {
            "name": "API Control",
            "description": "External API integration control"
        },
        {
            "name": "Aggregation",
            "description": "Hourly text aggregation management"
        }
    ]
}

def get_swagger_html():
    """Generate Swagger UI HTML"""
    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>WhisperSilent API Documentation</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui.css" />
    <style>
        html {{
            box-sizing: border-box;
            overflow: -moz-scrollbars-vertical;
            overflow-y: scroll;
        }}
        *, *:before, *:after {{
            box-sizing: inherit;
        }}
        body {{
            margin:0;
            background: #fafafa;
        }}
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {{
            // Create custom server configuration UI
            const serverConfigDiv = document.createElement('div');
            serverConfigDiv.style.cssText = 'margin: 20px; padding: 15px; background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;';
            serverConfigDiv.innerHTML = `
                <h3 style="margin-top: 0; color: #495057;">🌐 Server Configuration</h3>
                <div style="margin-bottom: 10px;">
                    <label for="server-url" style="display: inline-block; width: 120px; font-weight: bold; color: #495057;">Server URL:</label>
                    <input type="text" id="server-url" value="${{window.location.origin}}" 
                           style="width: 300px; padding: 8px; border: 1px solid #ced4da; border-radius: 4px; font-family: monospace;" 
                           placeholder="http://your-ip:8080" />
                    <button onclick="updateServerUrl()" 
                            style="margin-left: 10px; padding: 8px 15px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">
                        Update
                    </button>
                </div>
                <div style="font-size: 12px; color: #6c757d; margin-top: 5px;">
                    💡 <strong>Tip:</strong> Change this to point to your WhisperSilent server (e.g., http://192.168.1.100:8080)
                </div>
            `;
            
            const ui = SwaggerUIBundle({{
                url: '/api-docs.json',
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout",
                onComplete: function() {{
                    // Insert server config at the top
                    const swaggerContainer = document.querySelector('#swagger-ui');
                    if (swaggerContainer) {{
                        swaggerContainer.insertBefore(serverConfigDiv, swaggerContainer.firstChild);
                    }}
                }}
            }});
            
            // Function to update server URL
            window.updateServerUrl = function() {{
                const newServerUrl = document.getElementById('server-url').value.trim();
                if (!newServerUrl) {{
                    alert('Please enter a valid server URL');
                    return;
                }}
                
                // Validate URL format
                try {{
                    new URL(newServerUrl);
                }} catch (e) {{
                    alert('Please enter a valid URL (e.g., http://192.168.1.100:8080)');
                    return;
                }}
                
                // Fetch the current spec and update servers
                fetch('/api-docs.json')
                    .then(response => response.json())
                    .then(spec => {{
                        spec.servers = [
                            {{
                                url: newServerUrl,
                                description: "Custom Server"
                            }},
                            {{
                                url: window.location.origin,
                                description: "Current Server"
                            }},
                            {{
                                url: "http://localhost:8080",
                                description: "Local Development"
                            }}
                        ];
                        
                        // Recreate SwaggerUI with updated spec
                        document.querySelector('#swagger-ui').innerHTML = '';
                        SwaggerUIBundle({{
                            spec: spec,
                            dom_id: '#swagger-ui',
                            deepLinking: true,
                            presets: [
                                SwaggerUIBundle.presets.apis,
                                SwaggerUIStandalonePreset
                            ],
                            plugins: [
                                SwaggerUIBundle.plugins.DownloadUrl
                            ],
                            layout: "StandaloneLayout",
                            onComplete: function() {{
                                const swaggerContainer = document.querySelector('#swagger-ui');
                                if (swaggerContainer && !document.getElementById('server-url')) {{
                                    swaggerContainer.insertBefore(serverConfigDiv, swaggerContainer.firstChild);
                                }}
                            }}
                        }});
                        
                        // Show success message
                        const successMsg = document.createElement('div');
                        successMsg.style.cssText = 'position: fixed; top: 20px; right: 20px; background: #28a745; color: white; padding: 10px 15px; border-radius: 4px; z-index: 9999; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;';
                        successMsg.textContent = '✅ Server URL updated successfully!';
                        document.body.appendChild(successMsg);
                        setTimeout(() => document.body.removeChild(successMsg), 3000);
                    }})
                    .catch(error => {{
                        console.error('Error updating server:', error);
                        alert('Error updating server URL: ' + error.message);
                    }});
            }};
        }};
    </script>
</body>
</html>
"""