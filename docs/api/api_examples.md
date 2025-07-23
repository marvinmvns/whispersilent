# WhisperSilent API - Exemplos de Uso

Este documento fornece exemplos práticos de como usar a API HTTP do WhisperSilent para monitoramento, controle e recuperação de dados.

**Nota**: Alguns recursos avançados (Agregação Horária e API em Tempo Real) estão disponíveis no código mas podem requerer configuração específica dependendo do modo de execução do sistema.

## URLs Base

- **Desenvolvimento Local**: `http://localhost:8080`
- **Documentação Swagger**: `http://localhost:8080/api-docs`
- **Especificação OpenAPI**: `http://localhost:8080/api-docs.json`

## 1. Monitoramento de Saúde

### Verificação Básica de Saúde
```bash
curl http://localhost:8080/health
```

**Resposta de Exemplo:**
```json
{
  "status": "healthy",
  "timestamp": 1704067200.0,
  "uptime_seconds": 3600,
  "summary": {
    "pipeline_running": true,
    "total_transcriptions": 45,
    "cpu_usage": 25.5,
    "memory_usage": 65.2,
    "recent_errors_count": 0,
    "api_success_rate": 98.5
  }
}
```

### Informações Detalhadas de Saúde
```bash
curl http://localhost:8080/health/detailed
```

**Resposta de Exemplo:**
```json
{
  "status": "healthy",
  "timestamp": 1704067200.0,
  "uptime_seconds": 3600,
  "system_metrics": {
    "cpu_percent": 25.5,
    "memory_percent": 65.2,
    "memory_used_mb": 8245.3,
    "memory_total_mb": 16384.0,
    "disk_usage_percent": 42.1,
    "process_threads": 8,
    "process_memory_mb": 245.7
  },
  "transcription_metrics": {
    "total_chunks_processed": 150,
    "successful_transcriptions": 145,
    "failed_transcriptions": 5,
    "api_requests_sent": 140,
    "api_requests_failed": 2,
    "average_processing_time_ms": 1450.2,
    "last_transcription_time": 1704067190.0,
    "last_api_call_time": 1704067185.0,
    "uptime_seconds": 3600
  },
  "component_status": {
    "audio_capture_active": true,
    "audio_processor_active": true,
    "whisper_service_active": true,
    "api_service_active": true,
    "pipeline_running": true,
    "whisper_model_loaded": true
  },
  "recent_errors": [],
  "performance_warnings": []
}
```

### Status do Pipeline
```bash
curl http://localhost:8080/status
```

**Resposta de Exemplo:**
```json
{
  "pipeline_running": true,
  "api_sending_enabled": true,
  "uptime_seconds": 3600,
  "timestamp": 1704067200.0
}
```

## 2. Gerenciamento de Transcrições

### Listar Todas as Transcrições
```bash
# Todas as transcrições
curl http://localhost:8080/transcriptions

# Últimas 50 transcrições
curl "http://localhost:8080/transcriptions?limit=50"

# Transcrições da última hora
curl "http://localhost:8080/transcriptions?recent_minutes=60"

# Transcrições por período específico
curl "http://localhost:8080/transcriptions?start_time=1704060000&end_time=1704067200"
```

### Agregação Horária de Transcrições

#### Status da Agregação Atual
```bash
curl http://localhost:8080/aggregation/status
```

**Resposta de Exemplo:**
```json
{
  "enabled": true,
  "running": true,
  "current_hour_start": 1704067200.0,
  "current_hour_formatted": "2024-01-01 12:00",
  "current_transcription_count": 15,
  "current_partial_text": "Esta é uma conversa em andamento que será agregada...",
  "current_partial_length": 250,
  "last_transcription_time": 1704067800.0,
  "minutes_since_last": 2.5,
  "total_aggregated_hours": 24,
  "min_silence_gap_minutes": 5
}
```

#### Listar Textos Agregados
```bash
# Todos os textos agregados
curl http://localhost:8080/aggregation/texts

# Últimos 10 agregados
curl "http://localhost:8080/aggregation/texts?limit=10"
```

#### Obter Texto Agregado Específico por Hora
```bash
curl "http://localhost:8080/aggregation/texts/1704067200"
```

#### Forçar Finalização da Agregação Atual
```bash
curl -X POST http://localhost:8080/aggregation/finalize
```

#### Habilitar/Desabilitar Agregação
```bash
# Desabilitar agregação
curl -X POST "http://localhost:8080/aggregation/toggle?enabled=false"

# Habilitar agregação  
curl -X POST "http://localhost:8080/aggregation/toggle?enabled=true"
```

#### Estatísticas de Agregação
```bash
curl http://localhost:8080/aggregation/statistics
```

**Resposta de Exemplo:**
```json
{
  "total_aggregated_hours": 48,
  "total_transcriptions_aggregated": 1250,
  "total_characters_aggregated": 125000,
  "sent_to_api_count": 46,
  "pending_api_send": 2,
  "average_transcriptions_per_hour": 26.0,
  "average_characters_per_hour": 2604.2,
  "current_period_transcriptions": 8,
  "current_period_characters": 450,
  "enabled": true,
  "running": true
}
```

**Resposta de Exemplo:**
```json
{
  "transcriptions": [
    {
      "id": "trans_1704067200_1",
      "text": "Olá, isso é um teste de transcrição",
      "timestamp": 1704067200.0,
      "processing_time_ms": 1250.5,
      "chunk_size": 48000,
      "api_sent": true,
      "api_sent_timestamp": 1704067201.0,
      "confidence": null,
      "language": "pt"
    }
  ],
  "total_count": 1,
  "timestamp": 1704067250.0
}
```

### Buscar Transcrições por Texto
```bash
# Busca simples
curl "http://localhost:8080/transcriptions/search?q=teste"

# Busca case-sensitive
curl "http://localhost:8080/transcriptions/search?q=Teste&case_sensitive=true"
```

### Obter Transcrição Específica
```bash
curl http://localhost:8080/transcriptions/trans_1704067200_1
```

### Estatísticas de Transcrições
```bash
curl http://localhost:8080/transcriptions/statistics
```

**Resposta de Exemplo:**
```json
{
  "total_records": 150,
  "sent_to_api": 145,
  "pending_api_send": 5,
  "average_processing_time_ms": 1450.2,
  "oldest_timestamp": 1704000000.0,
  "newest_timestamp": 1704067200.0,
  "total_characters": 12500,
  "api_send_rate": 96.7
}
```

### Resumo por Período
```bash
# Resumo das últimas 24 horas
curl http://localhost:8080/transcriptions/summary

# Resumo das últimas 6 horas
curl "http://localhost:8080/transcriptions/summary?hours=6"
```

## 5. Controle do Sistema

### Ligar/Desligar Envio Automático para API
```bash
curl -X POST http://localhost:8080/control/toggle-api-sending
```

**Resposta de Exemplo:**
```json
{
  "message": "API sending disabled",
  "api_sending_enabled": false,
  "timestamp": 1704067200.0
}
```

### Iniciar Pipeline
```bash
curl -X POST http://localhost:8080/control/start
```

### Parar Pipeline
```bash
curl -X POST http://localhost:8080/control/stop
```

### Enviar Transcrições Pendentes Manualmente
```bash
curl -X POST http://localhost:8080/transcriptions/send-unsent
```

**Resposta de Exemplo:**
```json
{
  "message": "Sent 5 transcriptions, 0 failed",
  "sent_count": 5,
  "failed_count": 0,
  "timestamp": 1704067200.0
}
```

### Enviar Textos Agregados Pendentes
```bash
curl -X POST http://localhost:8080/aggregation/send-unsent
```

**Resposta de Exemplo:**
```json
{
  "message": "Sent 3 aggregated texts, 0 failed",
  "sent_count": 3,
  "failed_count": 0,
  "timestamp": 1704067200.0
}
```

## 4. API de Transcrição em Tempo Real (WebSocket)

### Configuração WebSocket

A API em tempo real utiliza WebSockets para streaming de transcrições ao vivo.

```bash
# .env - Habilitar API em tempo real
REALTIME_API_ENABLED=true
REALTIME_WEBSOCKET_PORT=8081
REALTIME_MAX_CONNECTIONS=50
REALTIME_BUFFER_SIZE=100
REALTIME_HEARTBEAT_INTERVAL=30
```

### Conectando via WebSocket

```javascript
// JavaScript/Browser
const websocket = new WebSocket('ws://localhost:8081');

websocket.onopen = function(event) {
    console.log('Conectado ao WhisperSilent');
};

websocket.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Evento recebido:', data);
};
```

```python
# Python com websockets
import asyncio
import websockets
import json

async def listen_transcriptions():
    uri = "ws://localhost:8081"
    async with websockets.connect(uri) as websocket:
        async for message in websocket:
            data = json.loads(message)
            print(f"Evento: {data}")

asyncio.run(listen_transcriptions())
```

### Eventos Disponíveis

#### 1. Evento de Conexão
```json
{
  "event": "connected",
  "client_id": "client_1704067200_12345",
  "timestamp": 1704067200.0,
  "available_events": ["transcription", "speaker_change", "chunk_processed", "error", "heartbeat"],
  "buffer_size": 25
}
```

#### 2. Nova Transcrição
```json
{
  "event_type": "transcription",
  "timestamp": 1704067200.0,
  "data": {
    "text": "Esta é uma nova transcrição em tempo real",
    "metadata": {
      "processing_time_ms": 1250.5,
      "confidence": 0.95,
      "speaker_id": "SPEAKER_01",
      "chunk_size": 48000
    },
    "client_count": 3
  }
}
```

#### 3. Mudança de Falante
```json
{
  "event_type": "speaker_change",
  "timestamp": 1704067205.0,
  "data": {
    "speaker_id": "SPEAKER_02",
    "confidence": 0.87,
    "metadata": {
      "previous_speaker": "SPEAKER_01",
      "transition_time": 1704067204.5
    }
  }
}
```

#### 4. Chunk de Áudio Processado
```json
{
  "event_type": "chunk_processed",
  "timestamp": 1704067210.0,
  "data": {
    "size": 48000,
    "duration_seconds": 3.0,
    "sample_rate": 16000,
    "processing_time_ms": 850.2
  }
}
```

#### 5. Heartbeat
```json
{
  "event": "heartbeat",
  "timestamp": 1704067215.0,
  "server_uptime": 3600,
  "connected_clients": 5
}
```

#### 6. Erro
```json
{
  "event_type": "error",
  "timestamp": 1704067220.0,
  "data": {
    "message": "Falha na transcrição do chunk de áudio",
    "error_type": "transcription_error"
  }
}
```

### Comandos do Cliente

#### Subscrever a Eventos
```json
{
  "action": "subscribe",
  "events": ["transcription", "speaker_change"]
}
```

#### Cancelar Subscrição
```json
{
  "action": "unsubscribe",
  "events": ["chunk_processed"]
}
```

#### Ping/Heartbeat
```json
{
  "action": "ping",
  "timestamp": 1704067200.0
}
```

#### Solicitar Eventos Recentes
```json
{
  "action": "get_buffer"
}
```

#### Definir Metadados do Cliente
```json
{
  "action": "set_metadata",
  "metadata": {
    "user_id": "user123",
    "session_name": "Meeting Room A",
    "language_preference": "pt-BR"
  }
}
```

### Cliente Python Completo

```python
#!/usr/bin/env python3
import asyncio
import json
import websockets
from datetime import datetime

class WhisperSilentClient:
    def __init__(self, server_url="ws://localhost:8081"):
        self.server_url = server_url
        self.websocket = None
        
    async def connect(self):
        try:
            self.websocket = await websockets.connect(self.server_url)
            print(f"Conectado a {self.server_url}")
            
            # Subscrever aos eventos desejados
            await self.subscribe(["transcription", "speaker_change"])
            
            # Escutar mensagens
            async for message in self.websocket:
                await self.handle_message(message)
                
        except Exception as e:
            print(f"Erro de conexão: {e}")
    
    async def subscribe(self, events):
        message = {
            "action": "subscribe",
            "events": events
        }
        await self.websocket.send(json.dumps(message))
    
    async def handle_message(self, message):
        try:
            data = json.loads(message)
            event = data.get('event', data.get('event_type'))
            timestamp = datetime.fromtimestamp(data.get('timestamp', 0))
            
            if event == 'transcription':
                text = data['data']['text']
                speaker = data['data']['metadata'].get('speaker_id', 'Unknown')
                print(f"[{timestamp:%H:%M:%S}] {speaker}: {text}")
                
            elif event == 'speaker_change':
                speaker = data['data']['speaker_id']
                confidence = data['data']['confidence']
                print(f"[{timestamp:%H:%M:%S}] 🎭 Novo falante: {speaker} ({confidence:.1%})")
                
            elif event == 'connected':
                client_id = data['client_id']
                print(f"[{timestamp:%H:%M:%S}] ✅ Conectado como {client_id}")
                
        except Exception as e:
            print(f"Erro processando mensagem: {e}")

# Uso
async def main():
    client = WhisperSilentClient()
    await client.connect()

if __name__ == "__main__":
    asyncio.run(main())
```

### Cliente Web (HTML/JavaScript)

Veja o arquivo `examples/realtime_web_client.html` para uma interface web completa com:
- Conexão WebSocket interativa
- Subscrição seletiva de eventos
- Exibição em tempo real de transcrições
- Log de eventos
- Estatísticas de conexão

### Status da API em Tempo Real

```bash
# Verificar status via HTTP
curl http://localhost:8080/realtime/status
```

**Resposta:**
```json
{
  "enabled": true,
  "running": true,
  "port": 8081,
  "connected_clients": 3,
  "max_connections": 50,
  "buffer_size": 45,
  "max_buffer_size": 100,
  "heartbeat_interval": 30,
  "clients": [
    {
      "client_id": "client_1704067200_12345",
      "connected_at": 1704067200.0,
      "last_heartbeat": 1704067250.0,
      "subscriptions": ["transcription", "speaker_change"],
      "metadata": {"user_id": "user123"}
    }
  ]
}
```

## 6. Exportação de Dados

### Exportar Todas as Transcrições
```bash
curl -X POST http://localhost:8080/transcriptions/export
```

**Resposta de Exemplo:**
```json
{
  "message": "Transcriptions exported successfully",
  "filename": "transcriptions_export_1704067200.json",
  "timestamp": 1704067200.0
}
```

## 7. Configuração da API Externa

### Configuração Opcional de API_KEY

O sistema funciona mesmo sem `API_KEY` configurado. Para usar:

#### Com API Key (Recomendado)
```bash
# .env
API_ENDPOINT=https://sua-api.com/transcription
API_KEY=sua_chave_api_aqui
```

**Requisição enviada:**
```json
{
  "transcription": "Texto transcrito aqui",
  "timestamp": "2024-01-01T12:00:00Z",
  "metadata": {
    "sampleRate": 16000,
    "channels": 1,
    "language": "pt",
    "model": "whisper.cpp",
    "device": "raspberry-pi-2w",
    "chunkSize": 48000,
    "processingTimeMs": 1250.5
  }
}
```

**Headers enviados:**
```
Content-Type: application/json
Authorization: Bearer sua_chave_api_aqui
```

#### Sem API Key
```bash
# .env
API_ENDPOINT=https://sua-api.com/transcription
# API_KEY não definido
```

**Headers enviados:**
```
Content-Type: application/json
```

### Exemplo de Endpoint Receptor (Node.js/Express)

```javascript
const express = require('express');
const app = express();

app.use(express.json());

// Endpoint para receber transcrições
app.post('/transcription', (req, res) => {
  const { transcription, timestamp, metadata } = req.body;
  
  console.log('Nova transcrição recebida:', {
    texto: transcription,
    tempo: timestamp,
    dispositivo: metadata.device,
    tempoProcessamento: metadata.processingTimeMs
  });
  
  // Processar transcrição aqui
  // Salvar no banco de dados, etc.
  
  res.json({ 
    success: true, 
    message: 'Transcrição recebida com sucesso',
    id: Date.now()
  });
});

app.listen(3000, () => {
  console.log('Servidor de transcrições rodando na porta 3000');
});
```

### Exemplo de Endpoint Receptor (Python/Flask)

```python
from flask import Flask, request, jsonify
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route('/transcription', methods=['POST'])
def receive_transcription():
    data = request.get_json()
    
    transcription = data.get('transcription')
    timestamp = data.get('timestamp')
    metadata = data.get('metadata', {})
    
    app.logger.info(f"Nova transcrição: {transcription}")
    app.logger.info(f"Metadados: {metadata}")
    
    # Processar transcrição aqui
    # Salvar no banco de dados, etc.
    
    return jsonify({
        'success': True,
        'message': 'Transcrição recebida com sucesso',
        'id': int(time.time())
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
```

## 8. Monitoramento Automático

### Script de Monitoramento em Shell
```bash
#!/bin/bash
# monitor_whispersilent.sh

API_BASE="http://localhost:8080"

# Verificar saúde do sistema
health=$(curl -s "${API_BASE}/health" | jq -r '.status')

if [ "$health" = "healthy" ]; then
    echo "✅ Sistema saudável"
else
    echo "⚠️  Sistema com problemas: $health"
    
    # Obter detalhes dos erros
    curl -s "${API_BASE}/health/detailed" | jq '.recent_errors'
fi

# Verificar estatísticas
stats=$(curl -s "${API_BASE}/transcriptions/statistics")
total=$(echo "$stats" | jq -r '.total_records')
pending=$(echo "$stats" | jq -r '.pending_api_send')

echo "📊 Total de transcrições: $total"
echo "⏳ Pendentes de envio: $pending"
```

### Script Python para Monitoramento
```python
import requests
import time
import json

class WhisperSilentMonitor:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
        
    def check_health(self):
        try:
            response = requests.get(f"{self.base_url}/health")
            data = response.json()
            return data['status'] == 'healthy'
        except:
            return False
            
    def get_stats(self):
        try:
            response = requests.get(f"{self.base_url}/transcriptions/statistics")
            return response.json()
        except:
            return None
            
    def send_pending_transcriptions(self):
        try:
            response = requests.post(f"{self.base_url}/transcriptions/send-unsent")
            return response.json()
        except:
            return None

# Uso
monitor = WhisperSilentMonitor()

while True:
    if monitor.check_health():
        print("✅ Sistema funcionando")
        
        stats = monitor.get_stats()
        if stats and stats['pending_api_send'] > 0:
            print(f"⏳ Enviando {stats['pending_api_send']} transcrições pendentes...")
            result = monitor.send_pending_transcriptions()
            print(f"📤 Enviadas: {result['sent_count']}")
    else:
        print("❌ Sistema com problemas")
        
    time.sleep(60)  # Verificar a cada minuto
```

## 9. Integração com Docker

### Dockerfile de Exemplo para API Receptora
```dockerfile
FROM node:16-alpine

WORKDIR /app
COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3000
CMD ["node", "server.js"]
```

### Docker Compose para Setup Completo
```yaml
version: '3.8'
services:
  whispersilent:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - ./transcriptions:/app/transcriptions
      - ./logs:/app/logs
    environment:
      - API_ENDPOINT=http://transcription-api:3000/transcription
      - HTTP_HOST=0.0.0.0
      
  transcription-api:
    build: ./api-server
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
```

Este guia fornece exemplos práticos para todas as funcionalidades da API WhisperSilent, permitindo integração fácil com outros sistemas e monitoramento eficaz do serviço de transcrição.