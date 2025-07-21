import sounddevice as sd
import re
from logger import log
from typing import List, Dict, Optional, Tuple

class AudioDeviceDetector:
    """
    Classe para detectar e selecionar automaticamente dispositivos de áudio.
    Prioriza microfones e evita dispositivos de saída/monitor.
    """
    
    def __init__(self):
        self.devices = []
        self.input_devices = []
        self.recommended_device = None
        self._refresh_devices()
    
    def _refresh_devices(self):
        """Atualiza a lista de dispositivos de áudio disponíveis"""
        try:
            self.devices = sd.query_devices()
            self.input_devices = [
                {'index': i, 'info': device} 
                for i, device in enumerate(self.devices) 
                if device['max_input_channels'] > 0
            ]
            log.info(f"Detectados {len(self.input_devices)} dispositivos de entrada de áudio")
        except Exception as e:
            log.error(f"Erro ao detectar dispositivos de áudio: {e}")
            self.devices = []
            self.input_devices = []
    
    def get_input_devices(self) -> List[Dict]:
        """Retorna lista de dispositivos de entrada disponíveis"""
        return self.input_devices
    
    def is_microphone_device(self, device_info: Dict) -> bool:
        """
        Verifica se um dispositivo é provavelmente um microfone baseado no nome.
        
        Args:
            device_info: Informações do dispositivo do sounddevice
            
        Returns:
            True se o dispositivo parece ser um microfone
        """
        device_name = device_info['name'].lower()
        
        # Palavras-chave que indicam microfone
        microphone_keywords = [
            'mic', 'microphone', 'microfone', 'input', 'capture', 'record',
            'usb', 'external', 'headset', 'webcam', 'camera', 'voice',
            'seeed', 'voicecard', 'respeaker', 'audioinjector'
        ]
        
        # Palavras-chave que NÃO são microfones (alto-falantes, monitores, etc.)
        exclude_keywords = [
            'monitor', 'loopback', 'output', 'speaker', 'headphone', 
            'digital output', 'spdif', 'hdmi', 'internal speakers',
            'built-in output', 'line out', 'analog output'
        ]
        
        # Verifica se contém palavras de exclusão
        for keyword in exclude_keywords:
            if keyword in device_name:
                return False
        
        # Verifica se contém palavras-chave de microfone
        for keyword in microphone_keywords:
            if keyword in device_name:
                return True
        
        # Se não tem palavras específicas, considera como possível microfone se tem entrada
        return device_info['max_input_channels'] > 0
    
    def score_device_priority(self, device_info: Dict) -> int:
        """
        Pontua um dispositivo baseado em prioridade para seleção automática.
        
        Args:
            device_info: Informações do dispositivo
            
        Returns:
            Pontuação (maior = melhor prioridade)
        """
        score = 0
        device_name = device_info['name'].lower()
        
        # Prioridade alta para dispositivos específicos conhecidos
        high_priority_devices = [
            'seeed', 'voicecard', 'respeaker', 'audioinjector', 'usb'
        ]
        for device in high_priority_devices:
            if device in device_name:
                score += 50
        
        # Prioridade média para microfones genéricos
        medium_priority_keywords = [
            'mic', 'microphone', 'microfone', 'capture', 'input'
        ]
        for keyword in medium_priority_keywords:
            if keyword in device_name:
                score += 30
        
        # Prioridade baixa para outros dispositivos de entrada
        if device_info['max_input_channels'] > 0:
            score += 10
        
        # Bonus para dispositivos com mais canais (até um limite)
        channels = min(device_info['max_input_channels'], 2)
        score += channels * 5
        
        # Penalidade para dispositivos com nomes que sugerem saída
        output_indicators = ['output', 'speaker', 'monitor', 'loopback']
        for indicator in output_indicators:
            if indicator in device_name:
                score -= 20
        
        return score
    
    def get_recommended_device(self) -> Optional[Tuple[int, Dict]]:
        """
        Retorna o dispositivo recomendado automaticamente.
        
        Returns:
            Tupla (índice, informações_dispositivo) ou None se nenhum encontrado
        """
        if not self.input_devices:
            return None
        
        # Se há apenas um dispositivo de entrada, use-o
        if len(self.input_devices) == 1:
            device = self.input_devices[0]
            log.info(f"Apenas um dispositivo de entrada encontrado: {device['info']['name']}")
            return device['index'], device['info']
        
        # Calcula pontuação para todos os dispositivos
        scored_devices = []
        for device in self.input_devices:
            if self.is_microphone_device(device['info']):
                score = self.score_device_priority(device['info'])
                scored_devices.append((score, device['index'], device['info']))
        
        if not scored_devices:
            # Se nenhum dispositivo foi identificado como microfone, usa o primeiro disponível
            device = self.input_devices[0]
            log.warning(f"Nenhum microfone identificado, usando primeiro dispositivo: {device['info']['name']}")
            return device['index'], device['info']
        
        # Ordena por pontuação (maior primeiro)
        scored_devices.sort(reverse=True, key=lambda x: x[0])
        best_device = scored_devices[0]
        
        log.info(f"Dispositivo recomendado: {best_device[2]['name']} (pontuação: {best_device[0]})")
        return best_device[1], best_device[2]
    
    def list_all_devices(self) -> str:
        """
        Retorna uma string formatada com todos os dispositivos disponíveis.
        
        Returns:
            String formatada com lista de dispositivos
        """
        if not self.devices:
            return "Nenhum dispositivo de áudio encontrado."
        
        output = ["Dispositivos de áudio disponíveis:"]
        output.append("=" * 50)
        
        for i, device in enumerate(self.devices):
            device_type = "Entrada" if device['max_input_channels'] > 0 else "Saída"
            if device['max_input_channels'] > 0 and device['max_output_channels'] > 0:
                device_type = "Entrada/Saída"
            
            is_mic = "📱 " if self.is_microphone_device(device) else "🔊 "
            
            output.append(f"{i:2d}: {is_mic}{device['name']}")
            output.append(f"    Tipo: {device_type}")
            output.append(f"    Canais entrada: {device['max_input_channels']}")
            output.append(f"    Canais saída: {device['max_output_channels']}")
            output.append(f"    Taxa amostra padrão: {device['default_samplerate']} Hz")
            output.append("")
        
        return "\n".join(output)
    
    def interactive_device_selection(self) -> Optional[Tuple[int, Dict]]:
        """
        Permite seleção interativa de dispositivo pelo usuário.
        
        Returns:
            Tupla (índice, informações_dispositivo) ou None se cancelado
        """
        if not self.input_devices:
            print("❌ Nenhum dispositivo de entrada encontrado.")
            return None
        
        print("\n🎤 Dispositivos de entrada disponíveis:")
        print("=" * 50)
        
        for i, device in enumerate(self.input_devices):
            is_mic = "📱" if self.is_microphone_device(device['info']) else "🔊"
            print(f"{i + 1:2d}: {is_mic} {device['info']['name']}")
            print(f"     Canais: {device['info']['max_input_channels']}")
            print(f"     Taxa: {device['info']['default_samplerate']} Hz")
            print()
        
        # Mostra recomendação automática
        recommended = self.get_recommended_device()
        if recommended:
            rec_index = recommended[0]
            # Encontra posição na lista de entrada
            rec_position = next(
                (i + 1 for i, dev in enumerate(self.input_devices) if dev['index'] == rec_index), 
                None
            )
            if rec_position:
                print(f"💡 Recomendado: Opção {rec_position} ({recommended[1]['name']})")
        
        print("0: Usar detecção automática")
        print()
        
        while True:
            try:
                choice = input("Escolha um dispositivo (0 para automático): ").strip()
                
                if choice == "0":
                    return self.get_recommended_device()
                
                choice_int = int(choice)
                if 1 <= choice_int <= len(self.input_devices):
                    selected_device = self.input_devices[choice_int - 1]
                    return selected_device['index'], selected_device['info']
                else:
                    print(f"❌ Opção inválida. Escolha entre 0 e {len(self.input_devices)}")
                    
            except (ValueError, KeyboardInterrupt):
                print("\n❌ Seleção cancelada.")
                return None
    
    def test_device(self, device_index: int, duration: float = 2.0) -> bool:
        """
        Testa se um dispositivo consegue capturar áudio.
        
        Args:
            device_index: Índice do dispositivo para testar
            duration: Duração do teste em segundos
            
        Returns:
            True se o teste foi bem-sucedido
        """
        try:
            log.info(f"Testando dispositivo {device_index} por {duration} segundos...")
            
            # Tenta capturar áudio por um período curto
            recording = sd.rec(
                int(duration * 16000), 
                samplerate=16000, 
                channels=1, 
                device=device_index,
                dtype='int16'
            )
            sd.wait()  # Aguarda a gravação terminar
            
            # Verifica se há dados válidos
            if recording is not None and len(recording) > 0:
                # Verifica se há variação no sinal (não apenas zeros)
                signal_variance = recording.var()
                if signal_variance > 0:
                    log.info(f"✅ Dispositivo {device_index} testado com sucesso (variância: {signal_variance:.2f})")
                    return True
                else:
                    log.warning(f"⚠️ Dispositivo {device_index} captura apenas silêncio")
                    return False
            else:
                log.error(f"❌ Dispositivo {device_index} não retornou dados")
                return False
                
        except Exception as e:
            log.error(f"❌ Erro ao testar dispositivo {device_index}: {e}")
            return False
    
    def auto_detect_best_device(self) -> Optional[Tuple[int, Dict]]:
        """
        Detecta automaticamente o melhor dispositivo, incluindo testes.
        
        Returns:
            Tupla (índice, informações_dispositivo) ou None se nenhum funcional
        """
        # Primeiro tenta a recomendação automática
        recommended = self.get_recommended_device()
        if recommended:
            device_index, device_info = recommended
            log.info(f"Testando dispositivo recomendado: {device_info['name']}")
            
            if self.test_device(device_index, duration=1.0):
                log.info(f"✅ Dispositivo recomendado aprovado: {device_info['name']}")
                return recommended
            else:
                log.warning(f"⚠️ Dispositivo recomendado falhou no teste: {device_info['name']}")
        
        # Se o recomendado falhou, testa outros dispositivos
        log.info("Testando outros dispositivos disponíveis...")
        for device in self.input_devices:
            device_index = device['index']
            device_info = device['info']
            
            # Pula o que já foi testado
            if recommended and device_index == recommended[0]:
                continue
            
            if self.is_microphone_device(device_info):
                log.info(f"Testando: {device_info['name']}")
                if self.test_device(device_index, duration=1.0):
                    log.info(f"✅ Dispositivo funcional encontrado: {device_info['name']}")
                    return device_index, device_info
        
        log.error("❌ Nenhum dispositivo funcional encontrado")
        return None