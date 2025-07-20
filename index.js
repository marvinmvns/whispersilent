const TranscriptionPipeline = require('./transcriptionPipeline');
const logger = require('./logger');
const fs = require('fs');
const path = require('path');

// Verificar configuração
function checkConfiguration() {
  const requiredEnvVars = ['API_ENDPOINT', 'API_KEY'];
  const missing = requiredEnvVars.filter(varName => !process.env[varName]);
  
  if (missing.length > 0) {
    logger.error(`Variáveis de ambiente faltando: ${missing.join(', ')}`);
    logger.info('Configure as variáveis no arquivo .env');
    process.exit(1);
  }

  // Verificar se o modelo existe
  const modelPath = require('./config').whisper.modelPath;
  if (!fs.existsSync(modelPath)) {
    logger.error(`Modelo Whisper não encontrado: ${modelPath}`);
    logger.info('Execute "npm run setup" para baixar o modelo');
    process.exit(1);
  }
}

// Instanciar pipeline
const pipeline = new TranscriptionPipeline();

// Gerenciar sinais do sistema
process.on('SIGINT', async () => {
  logger.info('Recebido SIGINT, encerrando...');
  await pipeline.stop();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  logger.info('Recebido SIGTERM, encerrando...');
  await pipeline.stop();
  process.exit(0);
});

// Tratamento de erros não capturados
process.on('uncaughtException', (error) => {
  logger.error('Erro não capturado:', error);
  pipeline.stop();
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  logger.error('Promise rejeitada não tratada:', reason);
  pipeline.stop();
  process.exit(1);
});

// Iniciar aplicação
async function main() {
  try {
    logger.info('=== Sistema de Transcrição em Tempo Real ===');
    logger.info('Verificando configuração...');
    
    checkConfiguration();
    
    logger.info('Iniciando aplicação...');
    await pipeline.start();
    
    logger.info('\n✅ Sistema pronto!');
    logger.info('🎤 Fale no microfone para transcrever');
    logger.info('📝 As transcrições serão enviadas para sua API');
    logger.info('⏹️  Pressione Ctrl+C para parar\n');
  } catch (error) {
    logger.error('Erro ao iniciar aplicação:', error);
    process.exit(1);
  }
}

main();
