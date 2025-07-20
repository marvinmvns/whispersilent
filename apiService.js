const axios = require('axios');
const config = require('./config');
const logger = require('./logger');

class ApiService {
  constructor() {
    this.client = axios.create({
      baseURL: config.api.endpoint,
      timeout: config.api.timeout,
      headers: {
        'Authorization': `Bearer ${config.api.key}`,
        'Content-Type': 'application/json'
      }
    });

    // Interceptor para log de requisições
    this.client.interceptors.request.use(
      request => {
        logger.debug('API Request:', {
          method: request.method,
          url: request.url
        });
        return request;
      },
      error => {
        logger.error('API Request Error:', error);
        return Promise.reject(error);
      }
    );

    // Interceptor para log de respostas
    this.client.interceptors.response.use(
      response => {
        logger.debug('API Response:', {
          status: response.status,
          data: response.data
        });
        return response;
      },
      error => {
        logger.error('API Response Error:', error.response?.data || error.message);
        return Promise.reject(error);
      }
    );
  }

  async sendTranscription(transcription, metadata = {}) {
    const data = {
      transcription,
      timestamp: new Date().toISOString(),
      metadata: {
        sampleRate: config.audio.sampleRate,
        channels: config.audio.channels,
        language: config.whisper.language,
        model: 'whisper.cpp',
        device: 'raspberry-pi-2w',
        ...metadata
      }
    };

    for (let attempt = 0; attempt < config.api.retryAttempts; attempt++) {
      try {
        const response = await this.client.post('/', data);
        logger.info('Transcrição enviada com sucesso');
        return response.data;
      } catch (error) {
        const isLastAttempt = attempt === config.api.retryAttempts - 1;
        logger.error(`Erro ao enviar transcrição (tentativa ${attempt + 1}/${config.api.retryAttempts}):`, 
          error.message);
        
        if (!isLastAttempt) {
          const delay = config.api.retryDelay * (attempt + 1);
          logger.info(`Aguardando ${delay}ms antes da próxima tentativa...`);
          await this.delay(delay);
        } else {
          throw error;
        }
      }
    }
  }

  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

module.exports = ApiService;
