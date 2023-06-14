from vkbottle import (
    API,
    PhotoMessageUploader,
    VoiceMessageUploader,
    BaseUploader
)
from typing import Optional


methods = {
    "photo": "photos.saveMessagesPhoto",
    "audio_message": "docs.save",
    "video": None
}


class UploadManager:
    def __init__(self, api: API, peer_id: Optional[int] = None):
        self._api = api
        self.peer_id = peer_id


    def check_document(self, doc_type):
        return doc_type in methods
    

    async def get_bytes(self, doc_url: str):
        return await self._api.http_client.request_content(doc_url)
    

    async def get_by_bytes(self, doc_type: str, doc_bytes: bytes, **params) -> Optional[str]:
        uploader: Optional[BaseUploader] = None
        upload_doc_type = doc_type

        match doc_type:
            case "photo":
                uploader = PhotoMessageUploader(self._api)

            case "audio_message":
                uploader = VoiceMessageUploader(self._api)
                upload_doc_type = "file"

            case _:
                return None

        file_bytes = uploader.get_bytes_io(doc_bytes)

        server = await uploader.get_server(peer_id=self.peer_id)

        up_obj = await uploader.upload_files(server["upload_url"], {upload_doc_type: file_bytes})
        res_obj = await self._api.request(
            methods[doc_type], {**up_obj, **params}
        )

        if doc_type in ["audio_message"]:
            response = res_obj["response"][doc_type]
        else:
            response = res_obj["response"][0]

        return uploader.generate_attachment_string(
            doc_type,
            response["owner_id"],
            response["id"],
            response.get("access_key")
        )


    async def get_attachment(self, doc_type: str, doc_url: str, **params) -> Optional[str]:
        doc_bytes = await self.get_bytes(doc_url)
        return await self.get_by_bytes(doc_type, doc_bytes, **params)
