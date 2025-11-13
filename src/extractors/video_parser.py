import json
import re
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup
import requests

from utils.logger import get_logger

class VimeoVideoParser:
    """
    Parses Vimeo video pages to discover a direct downloadable stream URL.

    Vimeo pages typically embed a configuration JSON that contains
    'progressive' video streams in various qualities. This parser makes
    a best-effort attempt to locate that metadata.
    """

    def __init__(
        self,
        session: Optional[requests.Session] = None,
        quality: str = "highest",
        timeout: int = 30,
        logger=None,
    ) -> None:
        self.session = session or requests.Session()
        self.quality = quality
        self.timeout = timeout
        self.logger = logger or get_logger("vimeo_downloader.video_parser")

    def get_download_url(self, video_url: str) -> Optional[str]:
        """
        Fetches the Vimeo page and attempts to resolve a direct video URL.
        Returns None if no valid stream can be found.
        """
        self.logger.debug("Requesting Vimeo page: %s", video_url)

        resp = self.session.get(video_url, timeout=self.timeout)
        resp.raise_for_status()

        html = resp.text
        soup = BeautifulSoup(html, "html.parser")

        # Strategy 1: Look for a JSON blob in a script tag that contains "progressive"
        script_tags = soup.find_all("script")
        for script in script_tags:
            content = script.string or script.get_text() or ""
            if "progressive" in content:
                self.logger.debug("Found candidate script tag containing 'progressive' streams.")
                url = self._extract_from_progressive(content)
                if url:
                    return url

        # Strategy 2: Heuristic search for "downloadUrl" fields
        heuristic_url = self._extract_simple_download_url(html)
        if heuristic_url:
            self.logger.debug("Resolved download URL via heuristic pattern.")
            return heuristic_url

        self.logger.warning("Failed to resolve any download URL from %s", video_url)
        return None

    def _extract_from_progressive(self, script_content: str) -> Optional[str]:
        """
        Attempts to extract the 'progressive' stream list from a JSON blob
        and returns the URL that best matches the configured quality.
        """
        try:
            # Find the substring starting at "progressive": [ ... ]
            match = re.search(r'"progressive"\s*:\s*(\[[^\]]+\])', script_content)
            if not match:
                self.logger.debug("No 'progressive' array found in script content.")
                return None

            progressive_json = match.group(1)
            streams: List[Dict[str, Any]] = json.loads(progressive_json)

            if not isinstance(streams, list):
                self.logger.debug("Parsed 'progressive' data is not a list.")
                return None

            selected = self._select_by_quality(streams)
            if not selected:
                self.logger.warning("No stream matched requested quality setting.")
                return None

            url = selected.get("url")
            if not url:
                self.logger.debug("Selected stream does not contain a 'url' field.")
                return None

            return url
        except Exception as exc:
            self.logger.debug("Error while parsing 'progressive' JSON: %s", exc, exc_info=True)
            return None

    def _select_by_quality(self, streams: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Selects a stream from the list based on quality preference.
        Streams may contain 'height' or 'quality' attributes.
        """
        if not streams:
            return None

        # Normalize stream quality/height
        def get_height(stream: Dict[str, Any]) -> int:
            if "height" in stream and isinstance(stream["height"], int):
                return stream["height"]
            quality = stream.get("quality", "")
            match = re.search(r"(\d+)", str(quality))
            return int(match.group(1)) if match else 0

        sorted_streams = sorted(streams, key=get_height)

        if self.quality == "lowest":
            return sorted_streams[0]
        if self.quality == "medium":
            return sorted_streams[len(sorted_streams) // 2]
        # default to highest
        return sorted_streams[-1]

    def _extract_simple_download_url(self, html: str) -> Optional[str]:
        """
        Fallback heuristic: search for a field that looks like `"downloadUrl":"<url>"`.
        """
        match = re.search(r'"downloadUrl"\s*:\s*"(?P<url>https?://[^"]+)"', html)
        if match:
            return match.group("url")
        return None