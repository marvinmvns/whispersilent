#!/usr/bin/env python3
"""
Script de teste para o JsonTranscriber
Testa a funcionalidade de transcrição contínua com saída JSON
"""

import sys
import os
import time
import signal
import json
from pathlib import Path

# Adicionar o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Importar módulos necessários
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'transcription'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'core'))

from transcription.jsonTranscriber import JsonTranscriber

class JsonTranscriberTest:
    def __init__(self):
        self.transcriber = None
        self.test_file = Path("test_transcriptions.json")
        
        # Configurar handler para CTRL+C
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handler para parar graciosamente com CTRL+C"""
        print(f"\n🛑 [SIGNAL] Recebido sinal {signum}, parando...")
        if self.transcriber:
            self.transcriber.stop()
        sys.exit(0)
    
    def print_header(self):
        """Exibe header do teste"""
        print("=" * 60)
        print("🎤 TESTE DO JSON TRANSCRIBER")
        print("=" * 60)
        print("📋 Este teste irá:")
        print("   1. Inicializar o JsonTranscriber com API do Google")
        print("   2. Capturar áudio do microfone")
        print("   3. Transcrever em tempo real")
        print("   4. Salvar resultados em JSON")
        print("   5. Exibir estatísticas ao final")
        print()
        print("⚠️  INSTRUÇÕES:")
        print("   - Fale claramente no microfone")
        print("   - Use CTRL+C para parar o teste")
        print("   - O arquivo JSON será atualizado em tempo real")
        print()
        print(f"📄 Arquivo de saída: {self.test_file.absolute()}")
        print("=" * 60)
    
    def test_initialization(self):
        """Testa a inicialização do JsonTranscriber"""
        print("🔧 [INIT] Inicializando JsonTranscriber...")
        
        try:
            self.transcriber = JsonTranscriber(str(self.test_file))
            
            print(f"✅ [INIT] JsonTranscriber inicializado com sucesso")
            print(f"   🎯 Engine: {self.transcriber.speech_service.engine.value}")
            print(f"   🌍 Idioma: {self.transcriber.speech_service.language}")
            print(f"   📄 Arquivo: {self.test_file.absolute()}")
            
            return True
            
        except Exception as e:
            print(f"❌ [INIT] Erro na inicialização: {e}")
            return False
    
    def test_audio_capture(self):
        """Testa a captura de áudio"""
        print("\n🎤 [AUDIO] Testando captura de áudio...")
        
        try:
            # Simular um teste rápido de áudio
            audio_queue = self.transcriber.audio_capture.start()
            
            print("✅ [AUDIO] Captura de áudio iniciada")
            print("   Testando por 2 segundos...")
            
            # Verificar se estamos recebendo dados
            chunks_received = 0
            for _ in range(20):  # 2 segundos aproximadamente
                try:
                    chunk = audio_queue.get(timeout=0.1)
                    chunks_received += 1
                except:
                    pass
            
            self.transcriber.audio_capture.stop()
            
            if chunks_received > 0:
                print(f"✅ [AUDIO] Recebidos {chunks_received} chunks de áudio")
                return True
            else:
                print("❌ [AUDIO] Nenhum chunk de áudio recebido")
                return False
                
        except Exception as e:
            print(f"❌ [AUDIO] Erro na captura: {e}")
            return False
    
    def run_continuous_test(self, duration_seconds=30):
        """Executa o teste contínuo por um período especificado"""
        print(f"\n🚀 [TEST] Iniciando teste contínuo por {duration_seconds} segundos...")
        print("💬 Comece a falar no microfone!")
        print("🔄 Transcrições serão exibidas em tempo real...")
        print("📄 JSON será atualizado automaticamente...")
        print("\n" + "="*50)
        
        try:
            # Iniciar transcrição
            self.transcriber.start()
            
            start_time = time.time()
            last_stats_time = start_time
            
            while True:
                current_time = time.time()
                elapsed = current_time - start_time
                
                # Verificar se passou o tempo de teste
                if elapsed > duration_seconds:
                    print(f"\n⏰ [TIME] Tempo de teste ({duration_seconds}s) finalizado")
                    break
                
                # Exibir estatísticas a cada 10 segundos
                if current_time - last_stats_time > 10:
                    stats = self.transcriber.get_stats()
                    print(f"\n📊 [STATS] {elapsed:.0f}s - Chunks: {stats['total_audio_chunks']}, "
                          f"Transcrições: {stats['successful_transcriptions']}, "
                          f"Vazias: {stats['empty_transcriptions']}")
                    last_stats_time = current_time
                
                time.sleep(0.1)
            
        except KeyboardInterrupt:
            print(f"\n⚡ [INTERRUPT] Teste interrompido pelo usuário")
        except Exception as e:
            print(f"\n❌ [ERROR] Erro durante o teste: {e}")
        finally:
            # Parar transcrição
            if self.transcriber.is_running:
                self.transcriber.stop()
    
    def display_results(self):
        """Exibe os resultados do teste"""
        print("\n" + "="*60)
        print("📊 RESULTADOS DO TESTE")
        print("="*60)
        
        # Estatísticas
        stats = self.transcriber.get_stats()
        print("📈 ESTATÍSTICAS:")
        print(f"   ⏱️  Sessão iniciada: {stats.get('session_start', 'N/A')}")
        print(f"   🎤 Total de chunks: {stats.get('total_audio_chunks', 0)}")
        print(f"   ✅ Transcrições bem-sucedidas: {stats.get('successful_transcriptions', 0)}")
        print(f"   🔇 Transcrições vazias: {stats.get('empty_transcriptions', 0)}")
        print(f"   ❌ Erros: {stats.get('errors', 0)}")
        print(f"   🔧 Engine usado: {stats.get('engine_used', 'N/A')}")
        
        # Últimas transcrições
        transcriptions = self.transcriber.get_transcriptions(limit=5)
        if transcriptions:
            print("\n📝 ÚLTIMAS 5 TRANSCRIÇÕES:")
            for i, t in enumerate(transcriptions[-5:], 1):
                timestamp = t['timestamp'][:19].replace('T', ' ')  # Formato legível
                text = t['text'][:50] + "..." if len(t['text']) > 50 else t['text']
                print(f"   {i}. [{timestamp}] \"{text}\"")
        else:
            print("\n📝 Nenhuma transcrição realizada")
        
        # Arquivo JSON
        if self.test_file.exists():
            size_kb = self.test_file.stat().st_size / 1024
            print(f"\n📄 ARQUIVO JSON:")
            print(f"   📍 Local: {self.test_file.absolute()}")
            print(f"   📏 Tamanho: {size_kb:.1f} KB")
            print(f"   ✅ Status: Arquivo criado com sucesso")
            
            # Verificar conteúdo
            try:
                with open(self.test_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"   📊 Transcrições no arquivo: {len(data.get('transcriptions', []))}")
            except Exception as e:
                print(f"   ❌ Erro ao ler arquivo: {e}")
        else:
            print(f"\n📄 ARQUIVO JSON:")
            print(f"   ❌ Arquivo não foi criado: {self.test_file.absolute()}")
    
    def cleanup(self):
        """Limpeza final"""
        print(f"\n🧹 [CLEANUP] Limpando recursos...")
        
        if self.transcriber and self.transcriber.is_running:
            self.transcriber.stop()
        
        # Perguntar se quer manter o arquivo de teste
        try:
            if self.test_file.exists():
                response = input(f"\n❓ Manter arquivo de teste '{self.test_file.name}'? (s/N): ").strip().lower()
                if response not in ['s', 'sim', 'y', 'yes']:
                    self.test_file.unlink()
                    print(f"🗑️  Arquivo {self.test_file.name} removido")
                else:
                    print(f"💾 Arquivo mantido: {self.test_file.absolute()}")
        except KeyboardInterrupt:
            print(f"\n💾 Arquivo mantido: {self.test_file.absolute()}")
    
    def run_full_test(self):
        """Executa o teste completo"""
        self.print_header()
        
        # Teste de inicialização
        if not self.test_initialization():
            print("❌ Falha na inicialização. Abortando teste.")
            return False
        
        # Teste de captura de áudio
        if not self.test_audio_capture():
            print("❌ Falha na captura de áudio. Abortando teste.")
            return False
        
        # Aguardar confirmação do usuário
        try:
            input("\n⏯️  Pressione Enter para iniciar o teste contínuo (ou CTRL+C para cancelar)...")
        except KeyboardInterrupt:
            print("\n🚫 Teste cancelado pelo usuário")
            return False
        
        # Executar teste contínuo
        self.run_continuous_test(duration_seconds=30)
        
        # Exibir resultados
        self.display_results()
        
        # Limpeza
        self.cleanup()
        
        print("\n✅ Teste concluído!")
        return True

def main():
    """Função principal"""
    print("🎯 Iniciando teste do JsonTranscriber...")
    
    # Verificar se estamos no diretório correto
    if not os.path.exists('src'):
        print("❌ Erro: Execute este script a partir do diretório raiz do projeto")
        print("   Uso: python scripts/test_json_transcriber.py")
        sys.exit(1)
    
    # Executar teste
    test = JsonTranscriberTest()
    
    try:
        success = test.run_full_test()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n🚨 Erro crítico: {e}")
        test.cleanup()
        sys.exit(1)

if __name__ == "__main__":
    main()