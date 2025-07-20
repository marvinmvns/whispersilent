const record = require('node-record-lpcm16');
const { PassThrough } = require('stream');
const config = require('./config');
const logger = require('./logger');

class AudioCapture {
  constructor() {
    this.recording = null;
    this.audioStream = null;
    this.isRecording = false;
  }

  start() {
    return new Promise((resolve, reject) => {
      try {
        this.audioStream = new PassThrough();
        
        this.recording = record.record({
          sampleRate: config.audio.sampleRate,
          channels: config.audio.channels,
          device: config.audio.device,
          audioType: config.audio.fileType,
          encoding: config.audio.encoding,
          bitDepth: config.audio.bitDepth,
          recorder: 'arecord', // Para Raspberry Pi
          silence: '0.0', // Desabilitar detecção de silêncio do arecord
          thresholdStart: null,
          thresholdEnd: null
        });

        this.recording.stream()
          .on('error', (err) => {
            logger.error('Erro no stream de áudio:', err);
            reject(err);
          })
          .pipe(this.audioStream);

        this.isRecording = true;
        logger.info('Captura de áudio iniciada');
        resolve(this.audioStream);
      } catch (error) {
        logger.error('Erro ao iniciar captura:', error);
        reject(error);
      }
    });
  }

  stop() {
    if (this.recording && this.isRecording) {
      this.recording.stop();
      this.isRecording = false;
      logger.info('Captura de áudio parada');
    }
  }

  getStream() {
    return this.audioStream;
  }
}

module.exports = AudioCapture;
