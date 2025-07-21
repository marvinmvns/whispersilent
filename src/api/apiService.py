import requests
import time
from config import Config
from logger import log

class ApiService:
    def __init__(self):
        self.base_url = Config.API["endpoint"]
        self.api_key = Config.API["key"]
        self.timeout = Config.API["timeout"] / 1000  # Convert ms to seconds
        self.retry_attempts = Config.API["retry_attempts"]
        self.retry_delay = Config.API["retry_delay"]

        # Only add Authorization header if API key is provided
        self.headers = {'Content-Type': 'application/json'}
        if self.api_key:
            self.headers['Authorization'] = f'Bearer {self.api_key}'

    def _log_request(self, method, url, data=None):
        log.debug(f'API Request: {{ "method": "{method}", "url": "{url}", "data": {data} }}')

    def _log_response(self, status, data):
        log.debug(f'API Response: {{ "status": {status}, "data": {data} }}')

    def _log_error(self, message, error_details=None):
        log.error(f'API Error: {message}', extra={'error_details': error_details})

    def send_transcription(self, transcription, metadata=None):
        if metadata is None:
            metadata = {}

        data = {
            "transcription": transcription,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.gmtime()),
            "metadata": {
                "sampleRate": Config.AUDIO["sample_rate"],
                "channels": Config.AUDIO["channels"],
                "language": Config.WHISPER["language"],
                "model": 'whisper.cpp',
                "device": 'raspberry-pi-2w',
                **metadata
            }
        }

        # Enhanced API request logging
        data_size = len(str(data))
        print(f"🌐 [API REQUEST] Preparando envio...")
        print(f"    📍 URL: {self.base_url}")
        print(f"    📝 Texto: \"{transcription[:50]}{'...' if len(transcription) > 50 else ''}\"")
        print(f"    📊 Payload: {data_size} bytes")
        print(f"    🔑 Auth: {'Sim' if self.api_key else 'Não'}")

        for attempt in range(self.retry_attempts):
            try:
                start_time = time.time()
                url = self.base_url # Assuming the endpoint is the full URL
                self._log_request('POST', url, data)
                
                print(f"🚀 [API] Tentativa {attempt + 1}/{self.retry_attempts} - Enviando...")
                
                response = requests.post(url, json=data, headers=self.headers, timeout=self.timeout)
                response_time_ms = (time.time() - start_time) * 1000
                
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                
                # Enhanced success logging
                response_data = response.json() if response.content else {}
                print(f"✅ [API SUCCESS] Resposta recebida em {response_time_ms:.0f}ms")
                print(f"    📊 Status: {response.status_code}")
                print(f"    📦 Response: {len(response.content)} bytes")
                if response_data:
                    print(f"    📋 Data: {str(response_data)[:100]}{'...' if len(str(response_data)) > 100 else ''}")
                
                self._log_response(response.status_code, response_data)
                log.info(f'Transcrição enviada com sucesso em {response_time_ms:.2f}ms')
                return response_data
                
            except requests.exceptions.RequestException as e:
                response_time_ms = (time.time() - start_time) * 1000
                is_last_attempt = (attempt == self.retry_attempts - 1)
                error_message = str(e)
                
                if hasattr(e, 'response') and e.response is not None:
                    error_message = f"{e.response.status_code} - {e.response.text}"
                    print(f"🚨 [API ERROR] {e.response.status_code} após {response_time_ms:.0f}ms")
                    print(f"    📄 Response: {e.response.text[:200]}{'...' if len(e.response.text) > 200 else ''}")
                else:
                    print(f"🚨 [API ERROR] {type(e).__name__} após {response_time_ms:.0f}ms")
                    print(f"    💬 Erro: {str(e)[:200]}{'...' if len(str(e)) > 200 else ''}")
                
                self._log_error(f"Erro ao enviar transcrição (tentativa {attempt + 1}/{self.retry_attempts}): {error_message}")
                
                if not is_last_attempt:
                    delay = self.retry_delay * (attempt + 1) / 1000 # Convert ms to seconds
                    print(f"⏳ [API RETRY] Aguardando {delay:.1f}s para próxima tentativa...")
                    log.info(f"Aguardando {delay}s antes da próxima tentativa...")
                    time.sleep(delay)
                else:
                    print(f"❌ [API FAILED] Todas as {self.retry_attempts} tentativas falharam")
                    raise # Re-raise the last exception

if __name__ == '__main__':
    # Exemplo de uso (apenas para teste)
    api_service = ApiService()
    try:
        # Substitua com um endpoint e chave de API válidos para testar
        # os.environ['API_ENDPOINT'] = 'http://localhost:3000/transcribe'
        # os.environ['API_KEY'] = 'your_test_api_key'
        # from dotenv import load_dotenv
        # load_dotenv()

        # result = api_service.send_transcription("Olá, isso é um teste de transcrição.")
        # print("Resultado da API:", result)
        pass
    except Exception as e:
        log.error(f"Erro no teste da API: {e}")
