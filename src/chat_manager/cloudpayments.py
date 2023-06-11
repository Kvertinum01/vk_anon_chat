from aiohttp import ClientSession, BasicAuth
from typing import Optional, Union, Any, Dict


class CloudPaymentsApiError(Exception):
    pass


class CloudPayments:
    def __init__(self, token: str, session: Optional[ClientSession] = None) -> None:
        self._auth = BasicAuth(*token.split(":"))
        self._session = session
        self._endpoint = "https://api.cloudpayments.ru/"


    async def setup(self, session: Optional[ClientSession] = None):
        if self._session is None:
            self._session = ClientSession() or session


    async def method(
        self, name: str, data: Dict[str, Union[str, int]], method = "POST"
    ) -> Dict[str, Any]:
        assert self._session is not None

        async with self._session.request(
            method, self._endpoint + name,
            data=data, auth=self._auth
        ) as response:
            res_json: Dict[str, Any] = await response.json()
            if res_json["Success"] != True:
                raise CloudPaymentsApiError(res_json)
            return res_json.get("Model")
