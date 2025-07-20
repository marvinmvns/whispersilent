const NodejsWhisper = require('nodejs-whisper');
const fs = require('fs').promises;
const path = require('path');
const wav = require('wav');
const { Readable } = require('stream');
const config = require('./config');
const logger = require('./logger');

class WhisperService {
  constructor() {
    this.whisper = null;
    this.tempFileCounter = 0;
    this.initializeWhisper();
  }

  async initializeWhisper() {
    try {
      // Criar diretório temporário se não existir
      await fs.mkdir(config.processing.tempDir, { recursive: true });

      // Verificar se o modelo existe
      try {
        await fs.access(config.whisper.modelPath);
      } catch (error) {
        logger.error(`Modelo Whisper não encontrado em: ${config.whisper.modelPath}`);
        logger.info('Execute "npm run setup" para baixar o modelo');
        throw new Error('Modelo Whisper não encontrado');
      }

      this.whisper = new NodejsWhisper(config.whisper.modelPath);
      logger.info('Whisper inicializado com sucesso');
    } catch (error) {
      logger.error('Erro ao inicializar Whisper:', error);
      throw error;
    }
  }

  async transcribe(audioBuffer) {
    const tempFileName = `audio_${Date.now()}_${this.tempFileCounter++}.wav`;
    const tempFilePath = path.join(config.processing.tempDir, tempFileName);

    try {
      // Salvar buffer como arquivo WAV temporário
      await this.saveAsWav(audioBuffer, tempFilePath);

      // Transcrever usando Whisper
      const options = {
        modelName: config.whisper.modelPath,
        language: config.whisper.language,
        gpu: config.whisper.enableGpu,
        threads: config.whisper.threads,
        processors: config.whisper.processors,
        maxLen: config.whisper.maxLen,
        splitOnWord: config.whisper.splitOnWord,
        noFallback: config.whisper.noFallback,
        printProgress: config.whisper.printProgress,
        printRealtime: config.whisper.printRealtime,
        printTimestamps: config.whisper.printTimestamps
      };

      const transcription = await this.whisper.transcribe(tempFilePath, options);
      
      if (transcription && transcription.trim()) {
        logger.info('Transcrição concluída:', transcription);
        return transcription.trim();
      }
      
      return null;
    } catch (error) {
      logger.error('Erro na transcrição Whisper:', error);
      throw error;
    } finally {
      // Limpar arquivo temporário
      try {
        await fs.unlink(tempFilePath);
      } catch (error) {
        logger.warn('Erro ao remover arquivo temporário:', error.message);
      }
    }
  }

  saveAsWav(audioBuffer, filePath) {
    return new Promise((resolve, reject) => {
      const writer = new wav.FileWriter(filePath, {
        sampleRate: config.audio.sampleRate,
        channels: config.audio.channels,
        bitDepth: config.audio.bitDepth
      });

      writer.on('done', () => resolve());
      writer.on('error', reject);

      const readable = new Readable();
      readable.push(audioBuffer);
      readable.push(null);
      readable.pipe(writer);
    });
  }

  async cleanup() {
    try {
      const files = await fs.readdir(config.processing.tempDir);
      for (const file of files) {
        if (file.startsWith('audio_') && file.endsWith('.wav')) {
          await fs.unlink(path.join(config.processing.tempDir, file));
        }
      }
    } catch (error) {
      logger.warn('Erro ao limpar arquivos temporários:', error.message);
    }
  }
}

module.exports = WhisperService;
