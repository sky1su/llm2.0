import uuid
import base64
import requests
import json
from urllib3.exceptions import InsecureRequestWarning


requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)


class GIGACHAT:
    auth_data = None
    access_token = None
    response = None
    access_token_request_id = None

    def __init__(self, client_secret: str, client_id: str):
        self.auth_data = self.__get_auth_data__(client_id, client_secret)
        self.access_token_request_id = str(uuid.uuid4())
        self.access_token = self.__get_access_token__()
    def __get_auth_data__(self, client_id: str, client_secret: str) -> str:
        auth_str = ':'.join([client_id,client_secret])
        data = bytes(auth_str, 'utf-8')
        auth_data = base64.b64encode(data)
        return auth_data.decode('utf-8')
    def __get_access_token__(self) -> object:
        url = 'https://ngw.devices.sberbank.ru:9443/api/v2/oauth'
        payload = 'scope=GIGACHAT_API_PERS'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'RqUID': self.access_token_request_id,
            'Authorization': f'Basic {self.auth_data}'
        }
        response = requests.request('POST', url, headers=headers, data=payload, verify=False, timeout=1)
        return json.loads(response.content)

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
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.access_token.get('access_token')}'
        }
        response = requests.request("POST", url, headers=headers, data=payload, verify=False)
        self.response = response

    def get_response(self):
        return self.response.text