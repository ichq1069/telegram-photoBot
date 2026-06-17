import httpx
from typing import Optional, Dict, Any
from app.core.config import settings


class TelegramAdapter:
    OFFICIAL_BASE = "https://api.telegram.org"

    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=settings.TG_API_TIMEOUT)
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    def _get_base_url(self, api_mode: str = None, self_build_url: str = None) -> str:
        if api_mode == "self_build" and self_build_url:
            return self_build_url.rstrip("/")
        if settings.TG_SELF_BUILD_API_URL:
            return settings.TG_SELF_BUILD_API_URL.rstrip("/")
        return self.OFFICIAL_BASE

    def _get_headers(self, api_mode: str = None, self_build_key: str = None) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        key = self_build_key or settings.TG_SELF_BUILD_API_KEY
        if api_mode == "self_build" and key:
            headers["X-API-Key"] = key
        elif settings.TG_SELF_BUILD_API_KEY:
            headers["X-API-Key"] = settings.TG_SELF_BUILD_API_KEY
        return headers

    async def call_method(
        self,
        bot_token: str,
        method: str,
        params: Dict[str, Any] = None,
        api_mode: str = "official",
        self_build_url: str = None,
        self_build_key: str = None,
        files: Dict[str, tuple] = None,
    ) -> Dict[str, Any]:
        base_url = self._get_base_url(api_mode, self_build_url)
        url = f"{base_url}/bot{bot_token}/{method}"
        headers = self._get_headers(api_mode, self_build_key)
        client = await self._get_client()

        try:
            if files:
                response = await client.post(
                    url, data=params or {}, files=files, headers=headers,
                )
            else:
                response = await client.post(
                    url, json=params or {}, headers=headers,
                )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            try:
                body = e.response.json()
                desc = body.get("description", str(e))
            except Exception:
                desc = f"HTTP {e.response.status_code}"
            return {"ok": False, "error_code": e.response.status_code, "description": desc}
        except httpx.RequestError as e:
            return {"ok": False, "error_code": 500, "description": f"网络请求失败: {str(e)}"}

    async def get_me(self, bot_token: str, api_mode: str = "official",
                      self_build_url: str = None, self_build_key: str = None) -> Dict[str, Any]:
        return await self.call_method(bot_token, "getMe", api_mode=api_mode,
                                      self_build_url=self_build_url, self_build_key=self_build_key)

    async def send_message(
        self,
        bot_token: str,
        chat_id: str,
        text: str,
        parse_mode: str = "HTML",
        api_mode: str = "official",
        self_build_url: str = None,
        self_build_key: str = None,
        **kwargs,
    ) -> Dict[str, Any]:
        params = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode, **kwargs}
        return await self.call_method(bot_token, "sendMessage", params,
                                      api_mode=api_mode, self_build_url=self_build_url,
                                      self_build_key=self_build_key)

    async def send_photo(
        self,
        bot_token: str,
        chat_id: str,
        photo,
        caption: str = None,
        parse_mode: str = "HTML",
        api_mode: str = "official",
        self_build_url: str = None,
        self_build_key: str = None,
        **kwargs,
    ) -> Dict[str, Any]:
        params = {"chat_id": chat_id, "parse_mode": parse_mode, **kwargs}
        if isinstance(photo, bytes):
            from io import BytesIO
            photo = BytesIO(photo)
        if hasattr(photo, 'read'):
            params["caption"] = caption
            return await self.call_method(
                bot_token, "sendPhoto", params,
                api_mode=api_mode, self_build_url=self_build_url,
                self_build_key=self_build_key,
                files={"photo": ("photo.jpg", photo)},
            )
        params["photo"] = photo
        if caption:
            params["caption"] = caption
        return await self.call_method(bot_token, "sendPhoto", params,
                                      api_mode=api_mode, self_build_url=self_build_url,
                                      self_build_key=self_build_key)

    async def send_document(
        self,
        bot_token: str,
        chat_id: str,
        document,
        caption: str = None,
        api_mode: str = "official",
        self_build_url: str = None,
        self_build_key: str = None,
        **kwargs,
    ) -> Dict[str, Any]:
        params = {"chat_id": chat_id, **kwargs}
        if hasattr(document, 'read'):
            params["caption"] = caption
            return await self.call_method(
                bot_token, "sendDocument", params,
                api_mode=api_mode, self_build_url=self_build_url,
                self_build_key=self_build_key,
                files={"document": ("document", document)},
            )
        params["document"] = document
        if caption:
            params["caption"] = caption
        return await self.call_method(bot_token, "sendDocument", params,
                                      api_mode=api_mode, self_build_url=self_build_url,
                                      self_build_key=self_build_key)

    async def get_file(self, bot_token: str, file_id: str,
                       api_mode: str = "official", self_build_url: str = None,
                       self_build_key: str = None) -> Dict[str, Any]:
        return await self.call_method(bot_token, "getFile", {"file_id": file_id},
                                      api_mode=api_mode, self_build_url=self_build_url,
                                      self_build_key=self_build_key)

    async def get_file_url(self, bot_token: str, file_id: str,
                           api_mode: str = "official", self_build_url: str = None,
                           self_build_key: str = None) -> Optional[str]:
        result = await self.get_file(bot_token, file_id, api_mode=api_mode,
                                     self_build_url=self_build_url, self_build_key=self_build_key)
        if result.get("ok") and result["result"].get("file_path"):
            file_path = result["result"]["file_path"]
            base_url = self._get_base_url(api_mode, self_build_url)
            return f"{base_url}/file/bot{bot_token}/{file_path}"
        return None

    async def broadcast_message(
        self,
        bot_token: str,
        chat_ids: list[str],
        text: str,
        parse_mode: str = "HTML",
        api_mode: str = "official",
        self_build_url: str = None,
        self_build_key: str = None,
    ) -> Dict[str, Any]:
        results = {"success": [], "failed": []}
        for chat_id in chat_ids:
            resp = await self.send_message(bot_token, chat_id, text, parse_mode,
                                           api_mode=api_mode, self_build_url=self_build_url,
                                           self_build_key=self_build_key)
            if resp.get("ok"):
                results["success"].append(chat_id)
            else:
                results["failed"].append({"chat_id": chat_id, "error": resp.get("description")})
        return results


tg_adapter = TelegramAdapter()
