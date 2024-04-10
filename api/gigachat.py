import uuid
import base64
import requests
import json
from urllib3.exceptions import InsecureRequestWarning
from datetime import datetime
from loguru import logger
import sys
# отключение предупреждения об отключенной валидации TLS сертификата
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

logger.remove()
# logger.add('journal.json', level='INFO', serialize=True, rotation='1 MB')
logger.add(sys.stderr, level='INFO')

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

    @logger.catch
    def __init__(self, client_secret: str, client_id: str):
        """
        Конструктор класса
        :param client_secret: client_secret
        :param client_id: client_id
        """
        logger.debug(f'Вызван конструктур класса')

        self.auth_data = self.__get_auth_data__(client_id, client_secret)
        self.access_token_request_id = str(uuid.uuid4())
        self.access_token = self.__get_access_token__()
        logger.debug(f'''значения переменных класса
        {self.auth_data=}
        {self.access_token_request_id=}
        {self.access_token=}
        ''')

    @logger.catch
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

    @logger.catch
    def __get_access_token__(self) -> dict:
        """
        Метод получает сессионный токен для работы с api
        :return: dict {'access_token': token, 'expires_at': unixtime
        """
        logger.debug('Вызван метод запроса токена')

        url = 'https://ngw.devices.sberbank.ru:9443/api/v2/oauth'
        payload = 'scope=GIGACHAT_API_PERS'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'RqUID': self.access_token_request_id,
            'Authorization': f'Basic {self.auth_data}'
        }
        ct = int(datetime.now().timestamp())
        logger.debug(f'{ct=}')
        if self.access_token is None:
            token_expires_at = 0
        else:
            token_expires_at = self.access_token.get('expires_at')

        logger.debug(f'{token_expires_at=}')

        if token_expires_at < ct:
            logger.debug(f'''Запрошен новый токен, т.к.:
            {self.access_token=}
            {ct=}
            {token_expires_at=}
            ''')
            try:
                response = requests.request('POST', url, headers=headers, data=payload, verify=False, timeout=1)
            except requests.RequestException as e:
                # print("Ошибка при получении токена:", e)
                logger.exception('Ошибка при получении токена.')
                logger.debug('Ошибка при получении токена.')
            finally:
                logger.info('Успешно получен токен авторизации')
            return json.loads(response.content)
        logger.debug('Использован ранее выданный токен')
        return self.access_token

    @logger.catch
    def api_request(self,
                    content: str,
                    promt: str,
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
                    "content": promt
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
        try:
            response = requests.request("POST", url, headers=headers, data=payload, verify=False)
        except requests.RequestException as e:
            logger.exception(f'Ошибка выполнения запроса к api {url}')
            self.response = None
        finally:
            logger.info(f'успешно выполнен запрос к api, код ответа: {response.status_code}')
        self.response = response

    @logger.catch
    def get_response(self):
        return self.response.text