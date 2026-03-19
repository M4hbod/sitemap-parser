# Sitemap Parser

<p align="center">
  <img src="https://github.com/thelovinator1/sitemap-parser/blob/master/.github/logo.png?raw=true" title="Robot searching for sitemaps" alt="Robot searching for sitemaps" width="300" height="300" />
</p>

This is a Python library designed to parse XML sitemaps and sitemap index files from a given URL. It supports both standard XML sitemaps (which contain URLs) and sitemap index files (which contain links to other sitemaps). This tool is useful for extracting data such as URLs and modification dates from website sitemaps.

## Acknowledgments

This is a fork of [Dave O'Connor](https://github.com/daveoconnor)'s [site-map-parser](https://github.com/daveoconnor/site-map-parser). I couldn't have done this without his original work.


## Installation

```sh
uv add git+https://github.com/TheLovinator1/sitemap-parser.git
```

## Usage

The library provides a SiteMapParser class that can be used to parse sitemaps and sitemap indexes. You can pass a URL or raw XML data to the parser to extract the URLs or links to other sitemaps.

### Parsing a Sitemap from a URL

```python
import logging
from typing import TYPE_CHECKING

from sitemap_parser import SiteMapParser

if TYPE_CHECKING:
    from sitemap_parser import SitemapIndex
    from sitemap_parser import UrlSet

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger: logging.Logger = logging.getLogger(__name__)


# url = "https://ttvdrops.lovinator.space/sitemap.xml"  # Sitemap index
url = "https://ttvdrops.lovinator.space/sitemap-static.xml"  # Sitemap with URLs
parser = SiteMapParser(source=url)

if parser.has_sitemaps():
    sitemaps: SitemapIndex = parser.get_sitemaps()
    for sitemap in sitemaps:
        logger.info(sitemap)

elif parser.has_urls():
    urls: UrlSet = parser.get_urls()
    for url in urls:
        logger.info(url)
```

### Parsing a Raw XML String

```python
from sitemap_parser import SiteMapParser, UrlSet

xml_data = """
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://example.com/</loc>
        <lastmod>2023-09-27</lastmod>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>https://example.com/about</loc>
        <lastmod>2023-09-27</lastmod>
        <changefreq>daily</changefreq>
        <priority>0.8</priority>
    </url>
</urlset>
"""
parser = SiteMapParser(source=xml_data, is_data_string=True)
urls: UrlSet = parser.get_urls()
for url in urls:
    print(url)

# Output:
# - https://example.com/
# - https://example.com/about
```

### Exporting Sitemap Data to JSON

You can export the parsed sitemap data to a JSON file using the JSONExporter class.

```python
import json
import logging

from sitemap_parser import JSONExporter
from sitemap_parser import SiteMapParser

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger: logging.Logger = logging.getLogger(__name__)

# Sitemap with URLs to other sitemaps
parser = SiteMapParser(source="https://ttvdrops.lovinator.space/sitemap.xml")

if parser.has_sitemaps():
    json_data: str = JSONExporter(data=parser).export_sitemaps()
    json_data = json.loads(json_data)
    logger.info("Exported sitemaps: %s", json_data)

logger.info("----" * 10)

# Sitemap with "real" URLs
parser2 = SiteMapParser(
    source="https://ttvdrops.lovinator.space/sitemap-static.xml",
)

if parser2.has_urls():
    json_data: str = JSONExporter(data=parser2).export_urls()
    json_data = json.loads(json_data)
    logger.info("Exported URLs: %s", json_data)
```

### Converting Sitemap XML to a Python dict

If you'd like to work with the parsed sitemap as a plain Python dictionary, you can use `SiteMapParser.to_dict()`.

```python
from sitemap_parser import SiteMapParser

xml = """
<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">
    <url>
        <loc>https://example.com/</loc>
    </url>
</urlset>
"""

parser = SiteMapParser(source=xml, is_data_string=True)
parsed = parser.to_dict()

# xmltodict represents repeated elements as lists
print(parsed["urlset"]["url"][0]["loc"])
```

You can also enable namespace processing for expanded namespace keys:

```python
parsed = parser.to_dict(process_namespaces=True)
```

## Disabling Logging

If you want to disable logging, you can adjust the logging level to logging.CRITICAL or higher. This will suppress all log messages below the CRITICAL level.

Here's an example of how to do this:

```python
import logging

# Set the logging level to CRITICAL to disable logging
logging.getLogger("sitemap_parser").setLevel(logging.CRITICAL)
```
