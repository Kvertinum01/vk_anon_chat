from vkbottle import (
    API,
    PhotoMessageUploader,
    VoiceMessageUploader,
    DocMessagesUploader,
    BaseUploader
)
from typing import Optional


methods = {
    "photo": "photos.saveMessagesPhoto",
    "audio": "audio.save",
    "audio_message": "docs.save",
}


class UploadManager:
    def __init__(self, api: API):
        self._api = api


    def check_document(self, doc_type):
        return doc_type in methods


    async def get_attachment(self, doc_type: str, doc_url: str, **params) -> Optional[str]:
        uploader: Optional[BaseUploader] = None
        upload_doc_type = doc_type

        if doc_type == "photo":
            uploader = PhotoMessageUploader(self._api)

        elif doc_type == "audio_message":
            uploader = VoiceMessageUploader(self._api)
            upload_doc_type = "file"

        if uploader is None:
            return None

        file_data = await self._api.http_client.request_content(doc_url)
        file_bytes = uploader.get_bytes_io(file_data)

        server = await uploader.get_server(**params)

        up_obj = await uploader.upload_files(server["upload_url"], {upload_doc_type: file_bytes})
        print(up_obj)
        res_obj = await self._api.request(
            methods[doc_type], {**up_obj}
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
