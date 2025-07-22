#!/usr/bin/env python3
"""
Teste simples e direto do JsonTranscriber
Roda na raiz do projeto para facilitar o teste
"""

import sys
import os
import time
import signal

# Adicionar paths necessários
sys.path.insert(0, 'src')
sys.path.insert(0, 'src/transcription')
sys.path.insert(0, 'src/core')

# Forçar engine do Google antes de importar
os.environ['SPEECH_RECOGNITION_ENGINE'] = 'google'

from transcription.jsonTranscriber import JsonTranscriber

def signal_handler(signum, frame):
    """Handler para CTRL+C"""
    print(f"\n🛑 Parando o transcriber...")
    if 'transcriber' in globals():
        transcriber.stop()
    sys.exit(0)

def main():
    print("🎤 JSON TRANSCRIBER - TESTE SIMPLES")
    print("="*50)
    print("🎯 Engine: Google Speech Recognition (gratuita)")
    print("📄 Arquivo: transcricoes_teste.json")
    print("⚠️  Use CTRL+C para parar")
    print("💬 Comece a falar no microfone!")
    print("="*50)
    
    # Configurar signal handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Criar e iniciar transcriber
        global transcriber
        transcriber = JsonTranscriber("transcricoes_teste.json")
        
        print(f"✅ Transcriber inicializado")
        print(f"🎯 Engine: {transcriber.speech_service.engine.value}")
        print(f"🌍 Idioma: {transcriber.speech_service.language}")
        
        # Iniciar transcrição
        transcriber.start()
        
        print(f"\n🚀 Transcrição iniciada! Fale no microfone...")
        print(f"📊 Estatísticas serão exibidas a cada 15 segundos")
        
        # Loop principal
        start_time = time.time()
        last_stats = start_time
        
        while True:
            current_time = time.time()
            
            # Mostrar estatísticas periodicamente
            if current_time - last_stats > 15:
                stats = transcriber.get_stats()
                elapsed = current_time - start_time
                
                print(f"\n📊 [{elapsed:.0f}s] ESTATÍSTICAS:")
                print(f"   🎤 Chunks processados: {stats.get('total_audio_chunks', 0)}")
                print(f"   ✅ Transcrições: {stats.get('successful_transcriptions', 0)}")
                print(f"   🔇 Vazias: {stats.get('empty_transcriptions', 0)}")
                print(f"   ❌ Erros: {stats.get('errors', 0)}")
                
                # Mostrar últimas transcrições
                transcriptions = transcriber.get_transcriptions(limit=3)
                if transcriptions:
                    print(f"   📝 Últimas transcrições:")
                    for t in transcriptions[-3:]:
                        timestamp = t['timestamp'][11:19]  # HH:MM:SS
                        text = t['text'][:40] + "..." if len(t['text']) > 40 else t['text']
                        print(f"      [{timestamp}] \"{text}\"")
                
                last_stats = current_time
            
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print(f"\n⚡ Interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
    finally:
        if 'transcriber' in globals():
            print(f"🛑 Parando transcriber...")
            transcriber.stop()
            
            # Mostrar resultados finais
            stats = transcriber.get_stats()
            print(f"\n📊 RESULTADOS FINAIS:")
            print(f"   Total de transcrições: {stats.get('successful_transcriptions', 0)}")
            print(f"   Arquivo JSON: transcricoes_teste.json")
            
        print(f"✅ Teste finalizado!")

if __name__ == "__main__":
    main()