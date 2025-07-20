const https = require('https');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const { promisify } = require('util');

const execAsync = promisify(exec);

const MODELS = {
  'tiny': 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin',
  'base': 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin',
  'small': 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin',
  'medium': 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin'
};

async function downloadModel(modelName = 'base') {
  const modelsDir = path.join(__dirname, 'models');
  
  // Criar diretório de modelos
  if (!fs.existsSync(modelsDir)) {
    fs.mkdirSync(modelsDir, { recursive: true });
  }

  const modelPath = path.join(modelsDir, `ggml-${modelName}.bin`);
  
  // Verificar se o modelo já existe
  if (fs.existsSync(modelPath)) {
    console.log(`Modelo ${modelName} já existe em ${modelPath}`);
    return;
  }

  const url = MODELS[modelName];
  if (!url) {
    throw new Error(`Modelo desconhecido: ${modelName}`);
  }

  console.log(`Baixando modelo ${modelName}...`);
  
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(modelPath);
    
    https.get(url, (response) => {
      const totalSize = parseInt(response.headers['content-length'], 10);
      let downloadedSize = 0;

      response.on('data', (chunk) => {
        downloadedSize += chunk.length;
        const percentage = ((downloadedSize / totalSize) * 100).toFixed(2);
        process.stdout.write(`\rProgresso: ${percentage}% (${downloadedSize}/${totalSize} bytes)`);
      });

      response.pipe(file);

      file.on('finish', () => {
        file.close();
        console.log(`\nModelo ${modelName} baixado com sucesso!`);
        resolve();
      });
    }).on('error', (err) => {
      fs.unlink(modelPath, () => {});
      reject(err);
    });
  });
}

async function installWhisperCpp() {
  console.log('Verificando instalação do whisper.cpp...');
  
  try {
    // Verificar se whisper.cpp já está instalado
    await execAsync('which whisper');
    console.log('whisper.cpp já está instalado');
  } catch (error) {
    console.log('Instalando whisper.cpp...');
    
    // Clonar e compilar whisper.cpp
    const commands = [
      'git clone https://github.com/ggerganov/whisper.cpp /tmp/whisper.cpp',
      'cd /tmp/whisper.cpp && make',
      'sudo cp /tmp/whisper.cpp/whisper /usr/local/bin/',
      'rm -rf /tmp/whisper.cpp'
    ];

    for (const cmd of commands) {
      console.log(`Executando: ${cmd}`);
      try {
        const { stdout, stderr } = await execAsync(cmd);
        if (stdout) console.log(stdout);
        if (stderr) console.error(stderr);
      } catch (error) {
        console.error(`Erro ao executar comando: ${error.message}`);
        throw error;
      }
    }
    
    console.log('whisper.cpp instalado com sucesso!');
  }
}

async function main() {
  console.log('=== Configuração do Sistema de Transcrição ===\n');
  
  try {
    // Instalar whisper.cpp
    await installWhisperCpp();
    
    // Baixar modelo
    const modelName = process.argv[2] || 'base';
    await downloadModel(modelName);
    
    // Criar diretórios necessários
    const dirs = ['temp', 'logs'];
    for (const dir of dirs) {
      const dirPath = path.join(__dirname, dir);
      if (!fs.existsSync(dirPath)) {
        fs.mkdirSync(dirPath, { recursive: true });
        console.log(`Diretório ${dir} criado`);
      }
    }
    
    console.log('\n✅ Configuração concluída com sucesso!');
    console.log('\nPróximos passos:');
    console.log('1. Configure as variáveis no arquivo .env');
    console.log('2. Execute: npm install');
    console.log('3. Execute: npm start');
  } catch (error) {
    console.error('\n❌ Erro durante a configuração:', error.message);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}
