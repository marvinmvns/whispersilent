# WhisperSilent - Sistema de Transcrição em Tempo Real

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-linux%20%7C%20macos%20%7C%20windows-lightgrey.svg)](https://github.com/whispersilent)

Sistema completo de transcrição de áudio em tempo real com interface HTTP, otimizado para Raspberry Pi e dispositivos embarcados. Utiliza Whisper.cpp para transcrição local e oferece APIs RESTful para monitoramento e controle.

## 🚀 Características Principais

- 🎤 **Captura de áudio em tempo real** usando ALSA/PortAudio
- 🧠 **Transcrição local** via Whisper.cpp (sem dependência de internet)
- 🌐 **API HTTP RESTful** com documentação Swagger
- 📊 **Monitoramento de saúde** em tempo real
- 💾 **Armazenamento persistente** de transcrições ordenadas cronologicamente
- 🔄 **Envio opcional para API externa** com retry automático
- 🎛️ **Controle dinâmico** via endpoints HTTP
- 📱 **Interface web** para monitoramento
- 🚀 **Otimizado para Raspberry Pi** 2W/3/4
- 🔧 **Instalação automatizada** com detecção de arquitetura

## 📋 Requisitos

### Hardware Mínimo
- **Raspberry Pi 2W** ou superior (x86_64, ARM64, ARMv7 suportados)
- **512MB RAM** disponível
- **2GB espaço livre** em disco
- **Microfone USB** ou **Seeed VoiceCard** (recomendado)
- Conexão de internet (opcional, para API externa)

### Software
- **Python 3.8+**
- **Linux/macOS/Windows** (testado em Ubuntu/Debian)
- Dependências instaladas automaticamente

## ⚡ Instalação Rápida

### Instalação Automatizada (Recomendada)

```bash
# Clone o repositório
git clone https://github.com/your-username/whispersilent.git
cd whispersilent

# Execute a instalação completa
chmod +x install.sh
./install.sh
```

O script de instalação vai:
- ✅ Verificar requisitos do sistema
- ✅ Instalar dependências do sistema
- ✅ Configurar ambiente Python virtual
- ✅ Compilar Whisper.cpp otimizado para sua arquitetura
- ✅ Baixar modelo de transcrição
- ✅ Executar testes de validação
- ✅ Criar scripts auxiliares e serviço systemd

### Instalação Manual

```bash
# 1. Instalar dependências do sistema (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install build-essential cmake git libasound2-dev portaudio19-dev python3-dev python3-pip python3-venv

# 2. Criar ambiente virtual
python3 -m venv .venv
source .venv/bin/activate

# 3. Instalar dependências Python
pip install -r requirements.txt

# 4. Compilar Whisper.cpp e baixar modelo
python3 setup.py base
```

## 🔧 Configuração

### Arquivo `.env`

Crie o arquivo `.env` com suas configurações:

```env
# ===== CONFIGURAÇÃO DA API EXTERNA (OPCIONAL) =====
# Deixe vazio se quiser usar apenas localmente
API_ENDPOINT=https://sua-api.com/transcription
API_KEY=sua_chave_api_opcional

# ===== CONFIGURAÇÃO DO WHISPER =====
WHISPER_MODEL_PATH=./models/ggml-base.bin
WHISPER_LANGUAGE=pt

# ===== CONFIGURAÇÃO DE ÁUDIO =====
SAMPLE_RATE=16000
CHANNELS=1
CHUNK_DURATION_MS=3000
SILENCE_THRESHOLD=500
SILENCE_DURATION_MS=1500

# ===== SERVIDOR HTTP =====
HTTP_HOST=localhost
HTTP_PORT=8080

# ===== PERFORMANCE =====
ENABLE_GPU=false
```

### Configurações Flexíveis

#### 🔄 Modo Local (sem API externa)
```env
# Remova ou comente as linhas da API
# API_ENDPOINT=
# API_KEY=
```

#### 🔑 API sem Autenticação
```env
API_ENDPOINT=https://sua-api.com/transcription
# API_KEY= (deixe vazio)
```

#### 🛡️ API com Autenticação
```env
API_ENDPOINT=https://sua-api.com/transcription
API_KEY=Bearer_sua_chave_aqui
```

## 🎯 Uso

### Iniciar o Sistema

```bash
# Com interface HTTP (recomendado)
./start.sh
# ou
python3 mainWithServer.py

# Apenas transcrição local
python3 main.py
```

### Acessar Interface Web

- **Monitoramento**: http://localhost:8080/health
- **Documentação API**: http://localhost:8080/api-docs
- **Transcrições**: http://localhost:8080/transcriptions

### Scripts Auxiliares

```bash
./test.sh       # Executar testes
./status.sh     # Verificar status do sistema
```

## 🌐 API HTTP

### Endpoints Principais

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/health` | Status básico do sistema |
| `GET` | `/health/detailed` | Informações detalhadas de saúde |
| `GET` | `/transcriptions` | Listar transcrições |
| `GET` | `/transcriptions/search?q=texto` | Buscar transcrições |
| `GET` | `/transcriptions/statistics` | Estatísticas |
| `GET` | `/api-docs` | Documentação Swagger |
| `POST` | `/control/toggle-api-sending` | Ligar/desligar envio para API |
| `POST` | `/transcriptions/send-unsent` | Enviar pendentes |

### Exemplos de Uso

```bash
# Verificar saúde do sistema
curl http://localhost:8080/health

# Listar últimas 10 transcrições
curl "http://localhost:8080/transcriptions?limit=10"

# Buscar transcrições
curl "http://localhost:8080/transcriptions/search?q=palavra"

# Desabilitar envio automático para API
curl -X POST http://localhost:8080/control/toggle-api-sending

# Obter estatísticas
curl http://localhost:8080/transcriptions/statistics
```

### Documentação Completa

Acesse http://localhost:8080/api-docs para documentação interativa Swagger com:
- 📖 Descrição detalhada de todos os endpoints
- 🔧 Interface para testar APIs
- 📋 Exemplos de request/response
- 📊 Schemas de dados

## 🏗️ Arquitetura do Sistema

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│ Microfone   │───▶│ AudioCapture │───▶│AudioProcessor│
│ (USB/ALSA)  │    │   (Thread)   │    │ (VAD/Chunks)│
└─────────────┘    └──────────────┘    └─────────────┘
                                                │
                                                ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│ API Externa │◀───│  ApiService  │◀───│WhisperService│
│ (Opcional)  │    │   (HTTP)     │    │(Whisper.cpp)│
└─────────────┘    └──────────────┘    └─────────────┘
                                                │
                                                ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│HTTP Server  │    │HealthMonitor │    │ File Storage│
│(REST API)   │    │ (Metrics)    │    │(Daily Files)│
└─────────────┘    └──────────────┘    └─────────────┘
```

### Componentes

1. **AudioCapture** - Interface com ALSA/PortAudio para captura de áudio
2. **AudioProcessor** - Detecção de voz ativa (VAD) e segmentação
3. **WhisperService** - Execução do Whisper.cpp para transcrição
4. **ApiService** - Cliente HTTP para API externa (opcional)
5. **TranscriptionPipeline** - Orquestrador principal
6. **HealthMonitor** - Monitoramento de sistema e métricas
7. **TranscriptionStorage** - Armazenamento em memória e busca
8. **TranscriptionFiles** - Persistência em arquivos organizados
9. **HTTPServer** - Servidor web com API RESTful

## 📊 Monitoramento

### Dashboard de Saúde

```json
{
  "status": "healthy",
  "timestamp": 1704067200.0,
  "uptime_seconds": 3600,
  "summary": {
    "pipeline_running": true,
    "total_transcriptions": 150,
    "cpu_usage": 25.5,
    "memory_usage": 65.2,
    "recent_errors_count": 0,
    "api_success_rate": 98.5
  }
}
```

### Métricas Detalhadas

- 📈 **Sistema**: CPU, memória, disco, threads
- 🎤 **Áudio**: Chunks processados, tempo de processamento
- 📝 **Transcrições**: Sucessos, falhas, taxa de caracteres
- 🌐 **API**: Requests enviados, falhas, latência
- ⚠️ **Alertas**: Erros recentes, warnings de performance

## 💾 Armazenamento de Dados

### Estrutura de Arquivos

```
transcriptions/
├── daily/                    # Arquivos diários ordenados
│   ├── transcriptions_20240101.json
│   └── transcriptions_20240102.json
├── sessions/                 # Sessões específicas
│   └── session_20240101_120000.json
└── exports/                  # Exportações
    ├── export_20240101_to_20240107.json
    └── transcript_20240101_to_20240107.txt
```

### Funcionalidades de Dados

- 🔍 **Busca por texto** com filtros avançados
- 📅 **Filtros temporais** por período
- 📊 **Estatísticas** e analytics
- 📤 **Exportação** em JSON e texto legível
- 🧹 **Limpeza automática** de arquivos antigos

## ⚙️ Configurações Avançadas

### Performance para Raspberry Pi

```env
# Modelo mais leve para Pi 2W
WHISPER_MODEL_PATH=./models/ggml-tiny.bin

# Chunks menores para menor latência
CHUNK_DURATION_MS=2000

# Threads otimizadas
WHISPER_THREADS=2
```

### Ambientes Ruidosos

```env
# Aumentar threshold para reduzir falsos positivos
SILENCE_THRESHOLD=800

# Aumentar duração mínima de silêncio
SILENCE_DURATION_MS=2000
```

### GPU Acceleration (se disponível)

```env
ENABLE_GPU=true
```

## 🧪 Testes

### Executar Testes

```bash
# Todos os testes
./test.sh

# Testes específicos
python3 -m pytest tests/test_audioCapture.py -v

# Teste de integração
python3 -c "from transcriptionPipeline import TranscriptionPipeline; print('✅ Importação OK')"
```

### Teste de Áudio

```bash
# Testar captura de áudio
arecord -D plughw:2,0 -f S16_LE -r 16000 -c 1 test.wav -d 5
aplay test.wav

# Verificar dispositivos
arecord -l
```

## 🔧 Troubleshooting

### Problemas Comuns

#### 🎤 "Dispositivo de áudio não encontrado"
```bash
# Listar dispositivos
arecord -l

# Testar dispositivo específico
arecord -D hw:1,0 -f S16_LE -r 16000 -c 1 test.wav -d 2

# Verificar permissões
sudo usermod -a -G audio $USER
```

#### 🧠 "Modelo Whisper não encontrado"
```bash
# Redownload do modelo
python3 setup.py base

# Verificar path
ls -la models/
```

#### 🌐 "Falha na conexão com API"
```bash
# Testar endpoint
curl -X POST https://sua-api.com/transcription \
  -H "Content-Type: application/json" \
  -d '{"test": "connection"}'

# Verificar logs
tail -f logs/combined.log
```

#### 💻 "Alta utilização de CPU"
```bash
# Usar modelo menor
export WHISPER_MODEL_PATH=./models/ggml-tiny.bin

# Reduzir frequência de processamento
export CHUNK_DURATION_MS=5000
```

### Logs e Debug

```bash
# Logs em tempo real
tail -f logs/combined.log

# Apenas erros
tail -f logs/error.log

# Debug específico
grep "ERROR" logs/combined.log | tail -20
```

## 🔒 Segurança

### Boas Práticas

- 🔐 **API Keys**: Armazene em `.env`, nunca no código
- 🌐 **CORS**: Configurado para desenvolvimento local
- 📝 **Logs**: Não logam dados sensíveis
- 🔒 **Permissões**: Execute com usuário não-root
- 🧹 **Cleanup**: Arquivos temporários são removidos automaticamente

### Configuração em Produção

```env
# Bind apenas no localhost em produção
HTTP_HOST=127.0.0.1

# Use proxy reverso (nginx/apache) para HTTPS
# API_ENDPOINT=https://sua-api-segura.com/transcription
```

## 📦 Deploy

### Systemd Service

```bash
# Instalado automaticamente pelo install.sh
sudo systemctl enable whispersilent
sudo systemctl start whispersilent
sudo systemctl status whispersilent
```

### Docker (Futuro)

```bash
# Build
docker build -t whispersilent .

# Run
docker run -d -p 8080:8080 \
  -v $(pwd)/transcriptions:/app/transcriptions \
  whispersilent
```

## 🤝 Desenvolvimento

### Estrutura do Projeto

```
whispersilent/
├── main.py                   # Entry point básico
├── mainWithServer.py         # Entry point com HTTP server
├── install.sh               # Script de instalação automatizada
├── requirements.txt         # Dependências Python
├── setup.py                 # Compilação e download de modelos
├── CLAUDE.md               # Guia para desenvolvimento
├── api_examples.md         # Exemplos de uso da API
├── swagger.py              # Documentação OpenAPI
├── config.py               # Configurações centralizadas
├── logger.py               # Sistema de logs
├── audioCapture.py         # Captura de áudio
├── audioProcessor.py       # Processamento de áudio
├── whisperService.py       # Interface Whisper.cpp
├── apiService.py           # Cliente API HTTP
├── transcriptionPipeline.py # Orquestrador principal
├── healthMonitor.py        # Monitoramento de saúde
├── transcriptionStorage.py # Armazenamento em memória
├── transcriptionFiles.py   # Gerenciamento de arquivos
├── httpServer.py           # Servidor HTTP RESTful
├── tests/                  # Suíte de testes
├── models/                 # Modelos Whisper
├── transcriptions/         # Dados persistentes
├── logs/                   # Arquivos de log
└── temp/                   # Arquivos temporários
```

### Contribuindo

1. **Fork** o repositório
2. **Clone** seu fork: `git clone https://github.com/seu-usuario/whispersilent.git`
3. **Branch**: `git checkout -b feature/nova-funcionalidade`
4. **Desenvolva** com testes: `./test.sh`
5. **Commit**: `git commit -m 'feat: adiciona nova funcionalidade'`
6. **Push**: `git push origin feature/nova-funcionalidade`
7. **Pull Request** com descrição detalhada

### Convenções

- 🐍 **Python**: PEP 8, type hints quando possível
- 📝 **Commits**: Conventional Commits (feat, fix, docs, etc.)
- 🧪 **Testes**: pytest para novos recursos
- 📖 **Docs**: Docstrings em português para funcionalidades principais

## 📈 Performance

### Benchmarks (Raspberry Pi 4)

| Modelo | Tamanho | Latência | CPU | RAM |
|--------|---------|----------|-----|-----|
| tiny   | 39 MB   | 0.5-1s   | 30% | 150MB |
| base   | 142 MB  | 1-2s     | 50% | 250MB |
| small  | 466 MB  | 2-4s     | 70% | 400MB |

### Otimizações Aplicadas

- ⚡ **Detecção de arquitetura** automática na compilação
- 🔧 **Flags de otimização** específicos (AVX, NEON, etc.)
- 🧵 **Threading** otimizado para número de cores
- 💾 **Buffer circular** para eficiência de memória
- 🧹 **Cleanup automático** de arquivos temporários

## 🐛 Problemas Conhecidos

- **Seeed VoiceCard**: Requer driver específico no Raspberry Pi
- **Python 3.12**: Algumas dependências podem requerer compilação
- **ARM 32-bit**: Performance limitada em modelos maiores
- **Windows**: Requer configuração manual de áudio

## 🔄 Roadmap

- [ ] 🐳 **Docker support** completo
- [ ] 📱 **Interface web** rica com gráficos
- [ ] 🔄 **WebSocket** para streaming em tempo real
- [ ] 🌍 **Multi-idioma** automático
- [ ] 🤖 **Integração com LLMs** para pós-processamento
- [ ] 📊 **Analytics avançados** e dashboards
- [ ] 🔐 **Autenticação** e autorização
- [ ] ☁️ **Deploy em cloud** (AWS, GCP, Azure)

## 📄 Licença

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🙏 Agradecimentos

- **[Whisper.cpp](https://github.com/ggerganov/whisper.cpp)** - Implementação otimizada do OpenAI Whisper
- **[OpenAI Whisper](https://github.com/openai/whisper)** - Modelo de transcrição de áudio
- **[Seeed VoiceCard](https://github.com/HinTak/seeed-voicecard)** - Driver de áudio para Raspberry Pi
- **Comunidade Python** - Bibliotecas e ferramentas utilizadas

## 📞 Suporte

- 📧 **Issues**: [GitHub Issues](https://github.com/your-username/whispersilent/issues)
- 📖 **Documentação**: [Wiki do Projeto](https://github.com/your-username/whispersilent/wiki)
- 💬 **Discussões**: [GitHub Discussions](https://github.com/your-username/whispersilent/discussions)

---

**🎤 WhisperSilent** - Transformando voz em texto com precisão e simplicidade.