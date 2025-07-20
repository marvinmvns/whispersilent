# Sistema de Transcrição em Tempo Real - Raspberry Pi

Sistema completo para captura de áudio, transcrição local via Whisper.cpp e envio para API usando Raspberry Pi 2W com Seeed VoiceCard.

## Características

- 🎤 Captura de áudio em tempo real usando ALSA
- 🧠 Transcrição local usando Whisper.cpp (sem dependência de API externa)
- 🚀 Otimizado para Raspberry Pi 2W
- 🔊 Detecção automática de fala/silêncio
- 📡 Envio automático de transcrições para sua API
- 📝 Sistema de logs completo
- 🔄 Retry automático em caso de falhas

## Requisitos de Hardware

- Raspberry Pi 2W (ou superior)
- Seeed VoiceCard (2-Mic ou 4-Mic)
- Cartão SD de pelo menos 8GB
- Conexão com internet

## Instalação

### 1. Configuração Inicial do Raspberry Pi

Execute o script de configuração automática:

```bash
wget https://raw.githubusercontent.com/seu-usuario/seu-repo/main/setup.sh
chmod +x setup.sh
./setup.sh
```

### 2. Instalação do Projeto

```bash
cd ~/raspberry-whisper-realtime
npm install
```

### 3. Download do Modelo Whisper

```bash
# Baixar modelo base (recomendado para Raspberry Pi 2W)
npm run setup

# Ou escolher um modelo específico:
npm run setup -- tiny   # 39 MB - mais rápido
npm run setup -- base   # 142 MB - equilibrado
npm run setup -- small  # 466 MB - mais preciso
```

### 4. Configuração

Crie o arquivo `.env` com suas configurações:

```env
# API Configuration
API_ENDPOINT=https://sua-api.com/transcription
API_KEY=sua_chave_api

# Whisper Configuration
WHISPER_MODEL_PATH=./models/ggml-base.bin
WHISPER_LANGUAGE=pt

# Audio Configuration
SAMPLE_RATE=16000
CHANNELS=1
CHUNK_DURATION_MS=3000
SILENCE_THRESHOLD=500
SILENCE_DURATION_MS=1500

# Performance
ENABLE_GPU=false
```

## Uso

### Iniciar o Sistema

```bash
npm start
```

### Modo Desenvolvimento

```bash
npm run dev
```

## Arquitetura do Sistema

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Microfone │────▶│ Audio Buffer │────▶│   Detector  │
│  (ALSA/Sox) │     │   (Stream)   │     │  de Silêncio│
└─────────────┘     └──────────────┘     └─────────────┘
                                                  │
                                                  ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│     API     │◀────│ Whisper.cpp  │◀────│ Audio Chunk │
│   Externa   │     │ (Transcrição)│     │   (WAV)     │
└─────────────┘     └──────────────┘     └─────────────┘
```

### Componentes Principais

1. **AudioCapture**: Interface com ALSA para captura de áudio
2. **AudioProcessor**: Detecta fala e segmenta áudio em chunks
3. **WhisperService**: Gerencia transcrição local via whisper.cpp
4. **ApiService**: Envia transcrições para API externa com retry
5. **TranscriptionPipeline**: Orquestra todo o fluxo

## Configurações Avançadas

### Ajuste de Performance

Para Raspberry Pi 2W, recomendamos:

```env
# Usar modelo tiny ou base
WHISPER_MODEL_PATH=./models/ggml-tiny.bin

# Desabilitar GPU (não disponível no Pi 2W)
ENABLE_GPU=false

# Chunks menores para processar mais rápido
CHUNK_DURATION_MS=2000
```

### Ajuste de Sensibilidade

```env
# Aumentar para ambientes barulhentos
SILENCE_THRESHOLD=800

# Reduzir para capturar falas mais curtas
SILENCE_DURATION_MS=1000
```

## Troubleshooting

### Verificar Dispositivos de Áudio

```bash
# Listar dispositivos de captura
arecord -l

# Listar configuração ALSA
cat /proc/asound/cards
```

### Testar Captura de Áudio

```bash
# Gravar 5 segundos
arecord -D plughw:2,0 -f S16_LE -r 16000 -c 1 test.wav -d 5

# Reproduzir
aplay test.wav
```

### Verificar Logs

```bash
# Logs em tempo real
tail -f logs/combined.log

# Apenas erros
tail -f logs/error.log
```

### Problemas Comuns

1. **"Modelo não encontrado"**
   - Execute `npm run setup` para baixar o modelo

2. **"Dispositivo de áudio não encontrado"**
   - Verifique se o Seeed VoiceCard está instalado
   - Reinicie o Raspberry Pi após instalar o driver

3. **"Transcrição muito lenta"**
   - Use o modelo `tiny` em vez do `base`
   - Reduza `CHUNK_DURATION_MS`

4. **"Muitos falsos positivos"**
   - Aumente `SILENCE_THRESHOLD`
   - Ajuste `SILENCE_DURATION_MS`

## Performance

### Consumo de Recursos (Raspberry Pi 2W)

- **CPU**: ~40-70% durante transcrição
- **RAM**: ~200-400MB
- **Latência**: 1-3 segundos (modelo base)

### Otimizações Aplicadas

1. **Buffer Circular**: Minimiza alocações de memória
2. **Processamento Assíncrono**: Não bloqueia captura
3. **Detecção de Silêncio**: Evita processar áudio vazio
4. **Queue de Processamento**: Garante ordem das transcrições
5. **Cleanup Automático**: Remove arquivos temporários

## Desenvolvimento

### Estrutura de Arquivos

```
raspberry-whisper-realtime/
├── index.js              # Ponto de entrada
├── config.js             # Configurações centralizadas
├── audioCapture.js       # Captura de áudio ALSA
├── audioProcessor.js     # Processamento e detecção
├── whisperService.js     # Interface whisper.cpp
├── apiService.js         # Cliente API
├── transcriptionPipeline.js # Orquestração
├── logger.js             # Sistema de logs
├── setup.js              # Download de modelos
├── models/               # Modelos Whisper
├── temp/                 # Arquivos temporários
└── logs/                 # Arquivos de log
```

### Contribuindo

1. Fork o projeto
2. Crie sua branch (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

## Agradecimentos

- [Whisper.cpp](https://github.com/ggerganov/whisper.cpp) - Implementação em C++ do Whisper
- [nodejs-whisper](https://github.com/ChetanXpro/nodejs-whisper) - Bindings Node.js
- [Seeed VoiceCard](https://github.com/HinTak/seeed-voicecard) - Driver de áudio
