"""
OpenAPI/Swagger documentation for WhisperSilent HTTP API
"""

SWAGGER_SPEC = {
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
            "url": "http://localhost:8080",
            "description": "Local development server"
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
                layout: "StandaloneLayout"
            }});
        }};
    </script>
</body>
</html>
"""