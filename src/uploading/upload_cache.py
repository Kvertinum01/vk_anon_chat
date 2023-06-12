from vkbottle import PhotoMessageUploader, API
from typing import Dict


class CacheAssistant:
    def __init__(self):
        self._cache: Dict[str, str] = {}

    async def get_photo(self, api: API, path: str):
        if path not in self._cache:
            photo_uploader = PhotoMessageUploader(api)
            res_attachment = await photo_uploader.upload(path)
            self._cache[path] = res_attachment
        return self._cache.get(path)

