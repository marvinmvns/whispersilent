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

        for attempt in range(self.retry_attempts):
            try:
                url = self.base_url # Assuming the endpoint is the full URL
                self._log_request('POST', url, data)
                response = requests.post(url, json=data, headers=self.headers, timeout=self.timeout)
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                self._log_response(response.status_code, response.json())
                log.info('Transcrição enviada com sucesso')
                return response.json()
            except requests.exceptions.RequestException as e:
                is_last_attempt = (attempt == self.retry_attempts - 1)
                error_message = str(e)
                if hasattr(e, 'response') and e.response is not None:
                    error_message = f"{e.response.status_code} - {e.response.text}"
                
                self._log_error(f"Erro ao enviar transcrição (tentativa {attempt + 1}/{self.retry_attempts}): {error_message}")
                
                if not is_last_attempt:
                    delay = self.retry_delay * (attempt + 1) / 1000 # Convert ms to seconds
                    log.info(f"Aguardando {delay}s antes da próxima tentativa...")
                    time.sleep(delay)
                else:
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
