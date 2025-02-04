"""
cache_warmer - Site cache warmer

MIT License

Copyright (c) 2025 Infra Bits

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import logging
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import List

import click
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

logger: logging.Logger = logging.getLogger(__name__)


def get_urls_from_sitemap(sitemap_url: str) -> List[str]:
    r = requests.get(sitemap_url, timeout=5)
    if r.status_code != 200:
        print(f"Sitemap not found: {sitemap_url}")
        sys.exit(1)
    if r.headers.get("Content-Type") != "application/xml":
        print(f"Sitemap wrong content-type: {sitemap_url}")
        sys.exit(1)
    soup = BeautifulSoup(r.content, "xml")
    return list({loc.text for loc in soup.find_all("loc")})


def _prime_url(url: str, headless: bool) -> None:
    logger.info(f"Priming {url}")
    options = Options()
    options.set_preference(
        "general.useragent.override",
        "Mozilla/5.0 (X11; Linux i686; rv:134.0) Gecko/20100101 Firefox/134.0 CacheWarmer",
    )
    if headless:
        options.add_argument("--headless")
    with webdriver.Firefox(options) as browser:
        browser.get(url)


@click.command()
@click.option("--workers", type=int, default=10)
@click.option("--headless", is_flag=True)
@click.argument("sitemap_url")
def cli(sitemap_url: str, workers: int, headless: bool) -> None:
    """cache_warmer - Site cache warmer."""
    logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(asctime)-15s %(message)s")

    executor = ThreadPoolExecutor(max_workers=workers)
    try:
        for url in get_urls_from_sitemap(sitemap_url):
            executor.submit(_prime_url, url, headless)
    finally:
        executor.shutdown()


if __name__ == "__main__":
    cli()
