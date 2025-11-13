from typing import Optional

import requests

from utils.logger import get_logger

class TimeoutSession(requests.Session):
    """
    Requests session that applies a default timeout to all requests
    unless a timeout is explicitly provided.
    """

    def __init__(self, timeout: int = 30):
        super().__init__()
        self._default_timeout = timeout

    def request(self, method, url, **kwargs):
        if "timeout" not in kwargs:
            kwargs["timeout"] = self._default_timeout
        return super().request(method, url, **kwargs)

class ProxyHandler:
    @staticmethod
    def create_session(
        use_proxy: bool = False,
        proxy_url: Optional[str] = None,
        timeout: int = 30,
        logger=None,
    ) -> requests.Session:
        logger = logger or get_logger("vimeo_downloader.proxy_handler")
        session = TimeoutSession(timeout=timeout)

        # Set a realistic default User-Agent
        session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            }
        )

        if use_proxy and proxy_url:
            logger.info("Configuring HTTP/HTTPS proxy: %s", proxy_url)
            session.proxies.update(
                {
                    "http": proxy_url,
                    "https": proxy_url,
                }
            )
        elif use_proxy and not proxy_url:
            logger.warning("use_proxy=True but no proxy_url provided. Proceeding without proxy configuration.")
        else:
            logger.info("Proxy usage disabled.")

        return session