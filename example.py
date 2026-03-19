import logging
from typing import TYPE_CHECKING

from src.sitemap_parser import SiteMapParser

if TYPE_CHECKING:
    from sitemap_parser import UrlSet

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    """Example usage of the SiteMapParser."""
    sitemap_url = "https://ttvdrops.lovinator.space/sitemap.xml"
    parser = SiteMapParser(sitemap_url)
    urls: UrlSet = parser.get_urls()

    logger.info("Fetched %d URLs from sitemap.", len(list(urls)))
    for url in urls:
        logger.info("URL: %s", url)


if __name__ == "__main__":
    main()
