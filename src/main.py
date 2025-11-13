import argparse
import json
import os
import sys
from typing import Any, Dict, List

from downloader.video_downloader import VideoDownloader
from utils.logger import get_logger

DEFAULT_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__),
    "config",
    "settings.example.json",
)

def load_json(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def validate_input(data: Dict[str, Any]) -> None:
    if "startUrls" not in data or not isinstance(data["startUrls"], list):
        raise ValueError("Input JSON must contain 'startUrls' as a non-empty list.")

    if not data["startUrls"]:
        raise ValueError("'startUrls' list cannot be empty.")

    for entry in data["startUrls"]:
        if not isinstance(entry, dict) or "url" not in entry:
            raise ValueError("Each item in 'startUrls' must be an object with a 'url' field.")

def merge_config(input_data: Dict[str, Any], config_data: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(config_data or {})
    merged.update(input_data or {})
    return merged

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Vimeo Video Downloader Scraper - download or resolve direct video URLs from Vimeo links."
    )
    parser.add_argument(
        "--input",
        "-i",
        default=os.path.join(os.path.dirname(__file__), "..", "data", "sample_input.json"),
        help="Path to the input JSON file containing startUrls and options.",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Optional path to save the result JSON. If omitted, prints to stdout.",
    )
    parser.add_argument(
        "--config",
        "-c",
        default=DEFAULT_CONFIG_PATH,
        help="Path to configuration JSON (defaults to settings.example.json).",
    )
    return parser.parse_args()

def main() -> None:
    logger = get_logger("vimeo_downloader.main")
    args = parse_args()

    try:
        logger.info("Loading configuration from %s", args.config)
        config_data = load_json(args.config)

        logger.info("Loading input from %s", args.input)
        input_data = load_json(args.input)
        validate_input(input_data)

        merged = merge_config(input_data, config_data)

        urls: List[str] = [entry["url"] for entry in merged["startUrls"]]
        quality: str = merged.get("quality", "highest")
        use_proxy: bool = bool(merged.get("useProxyForDownload", merged.get("use_proxy_for_download", False)))
        proxy_url: str = merged.get("proxyUrl", merged.get("proxy_url", ""))
        output_dir: str = merged.get("outputDir", merged.get("output_dir", "downloads"))
        timeout: int = int(merged.get("timeout", 30))

        logger.info("Starting Vimeo video download process")
        logger.debug(
            "Configuration - quality=%s, use_proxy=%s, proxy_url=%s, output_dir=%s, timeout=%s",
            quality,
            use_proxy,
            proxy_url or "None",
            output_dir,
            timeout,
        )

        downloader = VideoDownloader(
            quality=quality,
            use_proxy=use_proxy,
            proxy_url=proxy_url,
            output_dir=output_dir,
            timeout=timeout,
            logger=logger,
        )

        results = downloader.download_videos(urls)

        output_payload = [
            {
                "sourceUrl": result.source_url,
                "downloadUrl": result.download_url,
            }
            for result in results
        ]

        output_json = json.dumps(output_payload, indent=2)

        if args.output:
            os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output_json)
            logger.info("Results saved to %s", args.output)
        else:
            print(output_json)

        logger.info("Completed Vimeo download run successfully")

    except Exception as exc:
        logger.exception("Fatal error during execution: %s", exc)
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()