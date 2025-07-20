const dotenv = require('dotenv');
const path = require('path');
dotenv.config();

module.exports = {
  audio: {
    sampleRate: parseInt(process.env.SAMPLE_RATE) || 16000,
    channels: parseInt(process.env.CHANNELS) || 1,
    device: 'plughw:2,0', // Seeed VoiceCard device
    fileType: 'wav',
    encoding: 'signed-integer',
    bitDepth: 16
  },
  whisper: {
    modelPath: process.env.WHISPER_MODEL_PATH || path.join(__dirname, 'models', 'ggml-base.bin'),
    language: process.env.WHISPER_LANGUAGE || 'pt',
    enableGpu: process.env.ENABLE_GPU === 'true',
    threads: 4, // Otimizado para Raspberry Pi 2W
    processors: 1,
    maxLen: 0,
    splitOnWord: true,
    noFallback: false,
    printProgress: false,
    printRealtime: false,
    printTimestamps: false
  },
  api: {
    endpoint: process.env.API_ENDPOINT,
    key: process.env.API_KEY,
    timeout: 30000,
    retryAttempts: 3,
    retryDelay: 1000
  },
  processing: {
    chunkDurationMs: parseInt(process.env.CHUNK_DURATION_MS) || 3000,
    silenceThreshold: parseInt(process.env.SILENCE_THRESHOLD) || 500,
    silenceDurationMs: parseInt(process.env.SILENCE_DURATION_MS) || 1500,
    bufferSize: 4096,
    tempDir: path.join(__dirname, 'temp')
  }
};
