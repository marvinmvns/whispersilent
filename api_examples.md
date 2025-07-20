# WhisperSilent API - Exemplos de Uso

Este documento fornece exemplos práticos de como usar a API HTTP do WhisperSilent para monitoramento, controle e recuperação de dados.

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

## 3. Controle do Sistema

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

## 4. Exportação de Dados

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

## 5. Configuração da API Externa

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

## 6. Monitoramento Automático

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

## 7. Integração com Docker

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