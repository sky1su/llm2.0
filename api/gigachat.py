import uuid
import base64
import requests
import json
from urllib3.exceptions import InsecureRequestWarning
from datetime import datetime

# отключение предупреждения об отключенной валидации TLS сертификата
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)


class GIGACHAT:
    """
    Класс для работы с API gigachat от Сбер.
    при создании объекта необходимо передать client_secret и client_id
    api_request: Отправляет запрос к api
    get_response: Читает ответ на предыдущий запрос к api
    """
    auth_data = None
    access_token = None
    response = None
    access_token_request_id = None

    def __init__(self, client_secret: str, client_id: str):
        """
        Конструктор класса
        :param client_secret: client_secret
        :param client_id: client_id
        """
        self.auth_data = self.__get_auth_data__(client_id, client_secret)
        self.access_token_request_id = str(uuid.uuid4())
        self.access_token = self.__get_access_token__()

    def __get_auth_data__(self, client_id: str, client_secret: str) -> str:
        """
        Метод генерирует авторизационные данные, необходимые для получения сессионного токена
        :param client_id: client_id
        :param client_secret: client_secret
        :return: base64 strint client_id:client_secret
        """
        auth_str = ':'.join([client_id,client_secret])
        data = bytes(auth_str, 'utf-8')
        auth_data = base64.b64encode(data)
        return auth_data.decode('utf-8')

    def __get_access_token__(self) -> dict:
        """
        Метод получает сессионный токен для работы с api
        :return: dict {'access_token': token, 'expires_at': unixtime
        """
        url = 'https://ngw.devices.sberbank.ru:9443/api/v2/oauth'
        payload = 'scope=GIGACHAT_API_PERS'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'RqUID': self.access_token_request_id,
            'Authorization': f'Basic {self.auth_data}'
        }

        if self.access_token is None or datetime.now().timestamp() < self.access_token.get('expires_at'):
            try:
                response = requests.request('POST', url, headers=headers, data=payload, verify=False, timeout=1)
            except requests.RequestException as e:
                print("Ошибка при получении токена:", e)
            return json.loads(response.content)
        return self.access_token

    def api_request(self,
                    content: str,
                    tempeature=0.87,
                    top_p=0.47,
                    n=1,
                    max_tokens=512,
                    repetition_penalty=1,
                    stream=False):
        url = 'https://gigachat.devices.sberbank.ru/api/v1/chat/completions'
        payload = json.dumps({
            "model": "GigaChat",
            "messages": [
                {
                    "role": "system",
                    "content": "Выдели 5 главных фактов и мыслей из этого текста. Сформулируй каждый факт в виде одной строки."
                },
                {
                    "role": "user",
                    "content": content
                }
            ],
            "temperature": tempeature,
            "top_p": top_p,
            "n": n,
            "stream": stream,
            "max_tokens": max_tokens,
            "repetition_penalty": repetition_penalty
        })
        self.__get_access_token__()
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.access_token.get('access_token')}'
        }
        response = requests.request("POST", url, headers=headers, data=payload, verify=False)
        self.response = response

    def get_response(self):
        return self.response.text