from vkbottle import PhotoMessageUploader, API
from typing import Dict


class CacheAssistant:
    def __init__(self):
        self._cache: Dict[API, Dict[str, str]] = {}

    async def get_photo(self, api: API, path: str):
        if (api not in self._cache) or (path not in self._cache[api]):
            photo_uploader = PhotoMessageUploader(api)
            res_attachment = await photo_uploader.upload(path)
            self._cache[api] = {path: res_attachment}

        return self._cache[api][path]

