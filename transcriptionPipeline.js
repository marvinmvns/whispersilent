const { pipeline } = require('stream');
const AudioCapture = require('./audioCapture');
const AudioProcessor = require('./audioProcessor');
const WhisperService = require('./whisperService');
const ApiService = require('./apiService');
const logger = require('./logger');

class TranscriptionPipeline {
  constructor() {
    this.audioCapture = new AudioCapture();
    this.audioProcessor = new AudioProcessor();
    this.whisperService = new WhisperService();
    this.apiService = new ApiService();
    this.isRunning = false;
    this.processingQueue = [];
    this.isProcessing = false;
  }

  async start() {
    try {
      logger.info('Iniciando pipeline de transcrição...');
      
      const audioStream = await this.audioCapture.start();
      this.isRunning = true;

      // Configurar processamento de chunks
      this.audioProcessor.on('data', async (chunk) => {
        this.processingQueue.push(chunk);
        if (!this.isProcessing) {
          this.processQueue();
        }
      });

      // Iniciar pipeline
      pipeline(
        audioStream,
        this.audioProcessor,
        (err) => {
          if (err) {
            logger.error('Erro no pipeline:', err);
            this.stop();
          }
        }
      );

      logger.info('Pipeline de transcrição iniciado com sucesso');
      logger.info('Aguardando áudio... Fale no microfone!');
    } catch (error) {
      logger.error('Erro ao iniciar pipeline:', error);
      throw error;
    }
  }

  async processQueue() {
    if (this.processingQueue.length === 0 || this.isProcessing) {
      return;
    }

    this.isProcessing = true;

    while (this.processingQueue.length > 0) {
      const chunk = this.processingQueue.shift();
      try {
        await this.processAudioChunk(chunk);
      } catch (error) {
        logger.error('Erro ao processar chunk de áudio:', error);
      }
    }

    this.isProcessing = false;
  }

  async processAudioChunk(chunk) {
    try {
      const startTime = Date.now();
      
      // Transcrever áudio
      logger.info(`Processando chunk de áudio (${chunk.length} bytes)...`);
      const transcription = await this.whisperService.transcribe(chunk);
      
      if (transcription && transcription.trim()) {
        const processingTime = Date.now() - startTime;
        logger.info(`Transcrição obtida em ${processingTime}ms: "${transcription}"`);
        
        // Enviar para API
        await this.apiService.sendTranscription(transcription, {
          chunkSize: chunk.length,
          processingTimeMs: processingTime
        });
      } else {
        logger.debug('Nenhuma fala detectada no chunk');
      }
    } catch (error) {
      logger.error('Erro ao processar chunk:', error);
      // Continuar processando próximos chunks mesmo em caso de erro
    }
  }

  async stop() {
    if (this.isRunning) {
      this.audioCapture.stop();
      this.isRunning = false;
      
      // Limpar arquivos temporários
      await this.whisperService.cleanup();
      
      logger.info('Pipeline de transcrição parado');
    }
  }
}

module.exports = TranscriptionPipeline;
