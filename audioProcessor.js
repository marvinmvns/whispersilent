const { Transform } = require('stream');
const config = require('./config');
const logger = require('./logger');

class AudioProcessor extends Transform {
  constructor(options = {}) {
    super(options);
    this.buffer = Buffer.alloc(0);
    this.silenceStart = null;
    this.speaking = false;
    this.audioChunk = Buffer.alloc(0);
    this.chunkSize = config.audio.sampleRate * config.audio.channels * 2 * 
                     (config.processing.chunkDurationMs / 1000);
  }

  _transform(chunk, encoding, callback) {
    this.buffer = Buffer.concat([this.buffer, chunk]);
    
    while (this.buffer.length >= config.processing.bufferSize) {
      const frame = this.buffer.slice(0, config.processing.bufferSize);
      this.buffer = this.buffer.slice(config.processing.bufferSize);
      
      const isSilent = this.detectSilence(frame);
      
      if (!isSilent && !this.speaking) {
        // Início da fala
        this.speaking = true;
        this.silenceStart = null;
        this.audioChunk = Buffer.concat([this.audioChunk, frame]);
        logger.debug('Fala detectada');
      } else if (isSilent && this.speaking) {
        // Possível fim da fala
        if (!this.silenceStart) {
          this.silenceStart = Date.now();
        }
        
        this.audioChunk = Buffer.concat([this.audioChunk, frame]);
        
        if (Date.now() - this.silenceStart > config.processing.silenceDurationMs) {
          // Fim da fala confirmado
          this.speaking = false;
          if (this.audioChunk.length > 0) {
            this.push(this.audioChunk);
            logger.debug(`Fim da fala detectado, enviando chunk de ${this.audioChunk.length} bytes`);
            this.audioChunk = Buffer.alloc(0);
          }
        }
      } else if (this.speaking) {
        // Continua falando
        this.audioChunk = Buffer.concat([this.audioChunk, frame]);
        
        // Se o chunk atingir o tamanho máximo, enviar
        if (this.audioChunk.length >= this.chunkSize) {
          this.push(this.audioChunk);
          logger.debug(`Chunk máximo atingido, enviando ${this.audioChunk.length} bytes`);
          this.audioChunk = Buffer.alloc(0);
        }
      }
    }
    
    callback();
  }

  detectSilence(buffer) {
    const samples = new Int16Array(
      buffer.buffer, 
      buffer.byteOffset, 
      buffer.length / 2
    );
    
    let sum = 0;
    for (let i = 0; i < samples.length; i++) {
      sum += Math.abs(samples[i]);
    }
    
    const average = sum / samples.length;
    return average < config.processing.silenceThreshold;
  }

  _flush(callback) {
    if (this.audioChunk.length > 0) {
      this.push(this.audioChunk);
      logger.debug(`Flush: enviando último chunk de ${this.audioChunk.length} bytes`);
    }
    callback();
  }
}

module.exports = AudioProcessor;
