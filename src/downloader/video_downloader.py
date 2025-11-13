import os
from dataclasses import dataclass
from typing import List, Optional

from downloader.proxy_handler import ProxyHandler
from extractors.video_parser import VimeoVideoParser
from utils.logger import get_logger

@dataclass
class VideoDownloadResult:
    source_url: str
    download_url: str

class VideoDownloader:
    """
    Coordinates the Vimeo video download pipeline:
    - Resolves direct video URLs via VimeoVideoParser.
    - Optionally downloads files (current implementation returns direct URLs).
    """

    def __init__(
        self,
        quality: str = "highest",
        use_proxy: bool = False,
        proxy_url: str = "",
        output_dir: str = "downloads",
        timeout: int = 30,
        logger=None,
    ) -> None:
        self.logger = logger or get_logger("vimeo_downloader.video_downloader")
        self.output_dir = output_dir
        self.timeout = timeout

        os.makedirs(self.output_dir, exist_ok=True)

        self.logger.debug(
            "Initializing VideoDownloader with quality=%s, use_proxy=%s, proxy_url=%s, output_dir=%s, timeout=%s",
            quality,
            use_proxy,
            proxy_url or "None",
            self.output_dir,
            self.timeout,
        )

        self.session = ProxyHandler.create_session(
            use_proxy=use_proxy,
            proxy_url=proxy_url,
            timeout=timeout,
            logger=self.logger,
        )
        self.parser = VimeoVideoParser(
            session=self.session,
            quality=quality,
            timeout=timeout,
            logger=self.logger,
        )

    def download_videos(self, urls: List[str]) -> List[VideoDownloadResult]:
        """
        For each Vimeo URL, attempts to resolve a direct download URL.
        Returns a list of VideoDownloadResult objects.
        """
        results: List[VideoDownloadResult] = []

        for url in urls:
            self.logger.info("Processing Vimeo URL: %s", url)
            try:
                download_url: Optional[str] = self.parser.get_download_url(url)
                if not download_url:
                    self.logger.warning("Could not resolve download URL for %s", url)
                    continue

                self.logger.info("Resolved download URL for %s", url)
                results.append(VideoDownloadResult(source_url=url, download_url=download_url))
            except Exception as exc:
                self.logger.exception("Failed to process %s: %s", url, exc)

        if not results:
            self.logger.warning("No videos were successfully processed.")

        return results