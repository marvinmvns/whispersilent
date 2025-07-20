#!/bin/bash

echo "=== Configurando Sistema de Transcrição no Raspberry Pi ==="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Função para verificar sucesso
check_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $1 concluído${NC}"
    else
        echo -e "${RED}✗ Erro em $1${NC}"
        exit 1
    fi
}

# Atualizar sistema
echo -e "\n${YELLOW}1. Atualizando sistema...${NC}"
sudo apt-get update -qq
check_status "Atualização do sistema"

# Instalar dependências de áudio
echo -e "\n${YELLOW}2. Instalando dependências de áudio...${NC}"
sudo apt-get install -y alsa-utils libasound2-dev portaudio19-dev sox libsox-fmt-all
check_status "Instalação de dependências de áudio"

# Instalar dependências para whisper.cpp
echo -e "\n${YELLOW}3. Instalando dependências para whisper.cpp...${NC}"
sudo apt-get install -y build-essential cmake git
check_status "Instalação de dependências do whisper.cpp"

# Configurar Seeed VoiceCard
echo -e "\n${YELLOW}4. Configurando Seeed VoiceCard...${NC}"
if [ ! -d "$HOME/seeed-voicecard" ]; then
    cd ~
    git clone https://github.com/HinTak/seeed-voicecard
    cd seeed-voicecard
    sudo ./install.sh
    check_status "Instalação do Seeed VoiceCard"
else
    echo -e "${GREEN}✓ Seeed VoiceCard já instalado${NC}"
fi

# Configurar ALSA
echo -e "\n${YELLOW}5. Configurando ALSA...${NC}"
sudo tee /etc/asound.conf > /dev/null <<EOF
pcm.!default {
    type asym
    playback.pcm {
        type plug
        slave.pcm "hw:2,0"
    }
    capture.pcm {
        type plug
        slave.pcm "hw:2,0"
    }
}

ctl.!default {
    type hw
    card 2
}
EOF
check_status "Configuração do ALSA"

# Instalar Node.js 18
echo -e "\n${YELLOW}6. Instalando Node.js 18...${NC}"
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
    check_status "Instalação do Node.js"
else
    echo -e "${GREEN}✓ Node.js já instalado ($(node --version))${NC}"
fi

# Verificar instalação de áudio
echo -e "\n${YELLOW}7. Verificando dispositivos de áudio...${NC}"
echo "Dispositivos de captura:"
arecord -l
echo -e "\nDispositivos de reprodução:"
aplay -l

# Criar estrutura do projeto
echo -e "\n${YELLOW}8. Criando estrutura do projeto...${NC}"
mkdir -p ~/raspberry-whisper-realtime/{models,temp,logs}
check_status "Criação da estrutura de diretórios"

# Testar captura de áudio
echo -e "\n${YELLOW}9. Testando captura de áudio...${NC}"
echo "Gravando 3 segundos de teste..."
arecord -D plughw:2,0 -f S16_LE -r 16000 -c 1 -d 3 /tmp/test.wav 2>/dev/null
if [ -f /tmp/test.wav ]; then
    echo -e "${GREEN}✓ Captura de áudio funcionando${NC}"
    echo "Reproduzindo áudio de teste..."
    aplay /tmp/test.wav 2>/dev/null
    rm /tmp/test.wav
else
    echo -e "${RED}✗ Erro na captura de áudio${NC}"
fi

echo -e "\n${GREEN}=== Configuração concluída! ===${NC}"
echo -e "\nPróximos passos:"
echo -e "1. Entre no diretório: ${YELLOW}cd ~/raspberry-whisper-realtime${NC}"
echo -e "2. Copie os arquivos do projeto para o diretório"
echo -e "3. Configure o arquivo ${YELLOW}.env${NC} com suas credenciais"
echo -e "4. Execute: ${YELLOW}npm install${NC}"
echo -e "5. Execute: ${YELLOW}npm run setup${NC} para baixar o modelo Whisper"
echo -e "6. Execute: ${YELLOW}npm start${NC} para iniciar o sistema"

echo -e "\n${YELLOW}Modelos disponíveis:${NC}"
echo "- tiny: 39 MB (mais rápido, menos preciso)"
echo "- base: 142 MB (bom equilíbrio) [recomendado]"
echo "- small: 466 MB (mais preciso, mais lento)"
echo -e "\nPara baixar um modelo específico: ${YELLOW}npm run setup -- small${NC}"
