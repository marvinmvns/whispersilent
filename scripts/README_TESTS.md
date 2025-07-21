# 🧪 WhisperSilent - Comprehensive Test Suite

Este documento descreve o sistema de testes centralizado do WhisperSilent.

## 🚀 Quick Start

```bash
# Executar o menu de testes interativo
./scripts/run_all_tests.sh

# Ou diretamente
bash scripts/run_all_tests.sh
```

## 📋 Categorias de Testes

### 1. 🚀 Quick Tests (Essencial)
Testes rápidos para validação básica:
- ✅ Validação de instalação
- 🎙️ Teste básico de microfone (2s)
- 📄 Estrutura dos arquivos principais

**Duração:** ~3-5 minutos
**Ideal para:** Verificação rápida após instalação

### 2. 🔧 Installation & Setup Tests
Validação completa de instalação:
- 📦 Validação de dependências
- 🎧 Detecção de dispositivos de áudio
- 📄 Estrutura e funcionalidade dos arquivos principais

**Duração:** ~5-8 minutos
**Ideal para:** Após instalação ou mudanças no ambiente

### 3. 🎙️ Audio & Microphone Tests
Testes focados em áudio:
- 🎤 Detecção de dispositivos
- 📊 Captura básica (2s)
- 📈 Captura extendida com análise

**Duração:** ~3-5 minutos
**Ideal para:** Problemas de áudio ou novos dispositivos

### 4. 🗣️ Transcription Tests
Testes de transcrição:
- 🌐 Teste de todas as engines de transcrição
- 📝 JSON Transcriber
- ⚡ Teste simples
- 🔄 Sistema completo (20s+)

**Duração:** ~10-15 minutos
**Ideal para:** Validação de funcionalidade de transcrição

### 5. 🌐 System & HTTP Tests
Testes de sistema e API:
- 🏃 Funcionalidade básica dos arquivos principais
- 🌍 Todos os endpoints HTTP
- 🧪 Suite pytest

**Duração:** ~8-12 minutos
**Ideal para:** Validação de API e integração

### 6. 🧪 Complete Test Suite (All)
Executa todos os testes em sequência:
- ✅ Cobertura completa
- 📊 Relatório abrangente
- 🎯 Validação total do sistema

**Duração:** ~25-35 minutos
**Ideal para:** Validação completa antes de deploy

## 🎯 Testes Individuais

### Estrutura e Instalação
- **Installation Validation** - Verifica dependências e configuração
- **Audio Device Detection** - Lista e valida dispositivos de áudio
- **Main Files Structure** - Valida estrutura dos arquivos principais

### Audio e Captura
- **Basic Microphone Test** - Teste rápido de 2 segundos
- **Microphone Capture Test** - Teste extendido com análise
- **Main Files Basic Functionality** - Teste de startup dos arquivos principais

### Transcrição
- **Transcription API Test** - Testa todas as engines disponíveis
- **JSON Transcriber Test** - Funcionalidade do transcriber JSON
- **JSON Simple Test** - Teste simples do transcriber
- **Complete System Test** - Sistema completo com áudio real (20s+)

### Sistema e API
- **HTTP Endpoints Test** - Todos os 22+ endpoints da API HTTP
- **Pytest Suite** - Suite de testes unitários e integração

## 📊 Sequência Personalizada

Use a opção **8) Custom Test Sequence** para executar testes específicos:

```
Números dos testes:
1=Installation 2=Microphone 3=Capture 4=Audio-Device
5=Transcription-API 6=JSON-Transcriber 7=JSON-Simple
8=Complete-System 9=Structure 10=Basic-Functionality
11=HTTP-Endpoints 12=Pytest

Exemplo: 1 2 9 10  (testes básicos de setup)
```

## 🔍 Recursos do Script

### Features Principais
- 🎨 **Interface colorida** com emojis e status visual
- ⏱️ **Timeouts inteligentes** para cada tipo de teste
- 📊 **Relatórios detalhados** com estatísticas
- 🔄 **Menu interativo** para fácil navegação
- ⚡ **Tratamento de interrupções** (Ctrl+C)

### Tracking de Resultados
- ✅ **Contagem de sucessos/falhas**
- ⏱️ **Tempo de execução** de cada teste
- 📈 **Taxa de sucesso** percentual
- 📋 **Relatório final** com recomendações

### Validações Automáticas
- 📁 **Verificação de diretório** do projeto
- 🐍 **Detecção de Python** disponível
- 📄 **Validação de arquivos** necessários
- 🛡️ **Tratamento de erros** robusto

## 💡 Casos de Uso Recomendados

### Para Desenvolvedor
```bash
# Desenvolvimento diário
./scripts/run_all_tests.sh  # Opção 1 (Quick Tests)

# Após mudanças significativas
./scripts/run_all_tests.sh  # Opção 2 (Installation & Setup)

# Antes de commit/push
./scripts/run_all_tests.sh  # Opção 6 (Complete Suite)
```

### Para Deploy/Produção
```bash
# Validação completa
./scripts/run_all_tests.sh  # Opção 6 (Complete Suite)

# Validação específica de API
./scripts/run_all_tests.sh  # Opção 5 (System & HTTP Tests)
```

### Para Troubleshooting
```bash
# Problema de áudio
./scripts/run_all_tests.sh  # Opção 3 (Audio & Microphone Tests)

# Problema de transcrição
./scripts/run_all_tests.sh  # Opção 4 (Transcription Tests)

# Teste específico
./scripts/run_all_tests.sh  # Opção 7 (Individual Test Menu)
```

## 🛠️ Customização

### Variáveis de Ambiente
```bash
# Comando Python personalizado
PYTHON_CMD="python3.12" ./scripts/run_all_tests.sh

# Timeout personalizado (em segundos)
TEST_TIMEOUT=300 ./scripts/run_all_tests.sh
```

### Modificação de Testes
Edite `scripts/run_all_tests.sh` para:
- Adicionar novos testes
- Modificar timeouts
- Customizar categorias
- Alterar mensagens

## 📈 Interpretando Resultados

### Status dos Testes
- ✅ **PASS** - Teste executado com sucesso
- ❌ **FAIL** - Teste falhou ou teve erro
- ⚠️ **WARNING** - Teste teve problemas mas não críticos

### Taxa de Sucesso
- **100%** - 🎉 Sistema perfeito
- **80-99%** - ✅ Sistema funcional, verificar falhas menores
- **60-79%** - ⚠️ Problemas significativos, investigar
- **<60%** - 🚨 Problemas críticos, revisar configuração

### Próximos Passos
O script fornece recomendações específicas baseadas nos resultados:
- 🎯 **Sistema OK**: Como usar em produção
- ⚠️ **Problemas**: Passos específicos para correção
- 🛠️ **Configuração**: Arquivos e variáveis para verificar

## 🔧 Troubleshooting

### Problemas Comuns
```bash
# Permissão negada
chmod +x scripts/run_all_tests.sh

# Python não encontrado
sudo apt-get install python3
# ou especifique: PYTHON_CMD="python3.x" ./scripts/run_all_tests.sh

# Dependências faltando
pip install -r requirements.txt

# Problemas de áudio
sudo apt-get install alsa-utils portaudio19-dev
```

### Logs e Debug
- Os testes individuais geram output detalhado
- Use o menu individual para focar em testes específicos
- Verifique `logs/` para logs detalhados dos componentes

---

**💡 Dica:** Execute primeiro os **Quick Tests** para validação rápida, depois use testes específicos conforme necessário!