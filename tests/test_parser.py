import json
from typing import TYPE_CHECKING
from typing import Any

import niquests
import pytest

import py_sitemap_parser
from py_sitemap_parser import BaseData
from py_sitemap_parser import JSONExporter
from py_sitemap_parser import Sitemap
from py_sitemap_parser import SitemapIndex
from py_sitemap_parser import SiteMapParser
from py_sitemap_parser import Url
from py_sitemap_parser import UrlSet
from py_sitemap_parser import download_uri_data

if TYPE_CHECKING:
    import datetime


def test_ttvdrops_sitemap_parsing() -> None:
    """Test parsing the sitemap from ttvdrops.lovinator.space using the library."""
    url = "https://ttvdrops.lovinator.space/sitemap.xml"
    parser = py_sitemap_parser.SiteMapParser(source=url)

    if parser.has_urls():
        msg = "Expected ttvdrops sitemap to be a URL set, but found <sitemapindex>!"
        pytest.fail(msg)

    if parser.has_sitemaps():
        sitemaps: SitemapIndex = parser.get_sitemaps()
        sitemap_list: list[Sitemap] = list(sitemaps)
        assert len(sitemap_list) > 0, "No sitemaps found in ttvdrops sitemap index!"
        for sm in sitemap_list:
            assert sm.loc, f"Sitemap loc missing: {sm}"
            assert sm.loc.startswith("http"), f"Invalid sitemap loc: {sm.loc}"
    else:
        pytest.fail("Neither <urlset> nor <sitemapindex> found in ttvdrops sitemap!")

    sitemaps_that_are_urls = "https://ttvdrops.lovinator.space/sitemap-static.xml"
    parser2 = py_sitemap_parser.SiteMapParser(source=sitemaps_that_are_urls)
    if parser2.has_urls():
        urlset: UrlSet = parser2.get_urls()
        urls: list[Url] = list(urlset)
        assert len(urls) > 0, "No URLs found in ttvdrops sitemap!"
        for url in urls:
            assert url.loc, f"URL loc missing: {url}"
            assert url.loc.startswith("http"), f"Invalid URL: {url.loc}"
    if parser2.has_sitemaps():
        pytest.fail("Expected no sitemaps, but found some in ttvdrops sitemap index!")


def test_to_dict_from_urlset() -> None:
    """Test that to_dict correctly parses a simple URL set XML string."""
    xml = """
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url>
            <loc>https://example.com/</loc>
            <lastmod>2023-08-01</lastmod>
        </url>
    </urlset>
    """

    parser = SiteMapParser(source=xml, is_data_string=True)
    parsed: dict[str, dict[str, Any]] = parser.to_dict()

    urls: list[dict[str, str]] = parsed["urlset"]["url"]
    assert len(urls) == 1
    assert isinstance(urls, list)
    assert urls[0]["loc"] == "https://example.com/"
    assert urls[0]["lastmod"] == "2023-08-01"


def test_to_dict_process_namespaces() -> None:
    """Test that to_dict correctly processes XML namespaces when process_namespaces=True."""
    xml = """
    <root xmlns="http://defaultns.com/" xmlns:a="http://a.com/" xmlns:b="http://b.com/">
      <x>1</x>
      <a:y>2</a:y>
      <b:z>3</b:z>
    </root>
    """

    parser = SiteMapParser(source=xml, is_data_string=True)
    parsed: dict[str, dict[str, str]] = parser.to_dict(process_namespaces=True)

    assert parsed == {
        "http://defaultns.com/:root": {
            "@xmlns": {
                "": "http://defaultns.com/",
                "a": "http://a.com/",
                "b": "http://b.com/",
            },
            "http://defaultns.com/:x": "1",
            "http://a.com/:y": "2",
            "http://b.com/:z": "3",
        },
    }


def test_base_data_loc_and_lastmod_validation() -> None:
    """Validate BaseData loc/url validation and lastmod parsing."""
    base = BaseData()

    base.lastmod = "2023-08-01T12:34:56Z"
    lastmod: datetime.datetime | None = base.lastmod
    assert lastmod is not None
    assert lastmod.year == 2023
    assert lastmod.month == 8

    base.lastmod = None
    assert base.lastmod is None

    base.loc = "https://example.com/"
    assert base.loc == "https://example.com/"

    with pytest.raises(TypeError, match="URL must be a string"):
        base.loc = 123  # type: ignore[assignment]

    with pytest.raises(ValueError, match="is not a valid URL"):
        base.loc = "not a url"


def test_sitemap_str_and_repr_and_missing_loc() -> None:
    """Verify Sitemap string formatting and missing loc behavior."""
    sitemap = Sitemap(loc="https://example.com/sitemap.xml", lastmod="2023-08-01")
    assert str(sitemap) == "https://example.com/sitemap.xml"
    assert repr(sitemap) == "<Sitemap https://example.com/sitemap.xml>"

    # Bypass the setter validation so we can test the __str__ failure path.
    sitemap._loc = None  # type: ignore[attr-defined]
    with pytest.raises(ValueError, match="loc cannot be None"):
        str(sitemap)


def test_url_changefreq_and_priority_validation() -> None:
    """Validate Url property validation and formatting."""
    url = Url(
        loc="https://example.com/",
        lastmod="2023-08-01",
        changefreq="daily",
        priority="0.5",
    )

    assert url.loc == "https://example.com/"
    assert url.changefreq == "daily"
    priority: float | None = url.priority
    assert priority is not None
    assert abs(priority - 0.5) < 1e-9
    assert str(url) == "https://example.com/"
    assert "Url(loc=" in repr(url)

    with pytest.raises(ValueError, match="not an allowed value"):
        Url(loc="https://example.com/", changefreq="invalid")

    with pytest.raises(ValueError, match="not between"):
        Url(loc="https://example.com/", priority=1.1)

    with pytest.raises(ValueError, match="not between"):
        Url(loc="https://example.com/", priority=-0.1)


def test_urlset_iteration_and_missing_items() -> None:
    """Validate UrlSet iteration and missing url handling."""
    urlset_data: dict[str, dict[str, str]] | dict[str, list[dict[str, str]]] = {
        "url": {
            "loc": "https://example.com/",
            "lastmod": "2023-08-01",
            "changefreq": "daily",
            "priority": "0.1",
        },
    }

    urlset = UrlSet(urlset_data)
    urls: list[Url] = list(urlset)
    assert len(urls) == 1
    assert urls[0].loc == "https://example.com/"
    priority: float | None = urls[0].priority
    assert priority is not None
    assert abs(priority - 0.1) < 1e-9

    urlset_data = {
        "url": [
            {"loc": "https://example.com/1"},
            {"loc": "https://example.com/2"},
        ],
    }

    urlset = UrlSet(urlset_data)
    urls: list[Url] = list(urlset)
    assert {u.loc for u in urls} == {"https://example.com/1", "https://example.com/2"}

    urlset = UrlSet({})
    assert list(urlset) == []


def test_sitemapindex_iteration() -> None:
    """Validate SitemapIndex iteration and sitemap extraction."""
    index_data: dict[str, dict[str, str]] | dict[str, list[dict[str, str]]] = {
        "sitemap": {"loc": "https://example.com/sitemap1.xml", "lastmod": "2023-08-01"},
    }
    index = SitemapIndex(index_data)
    sitemaps: list[Sitemap] = list(index)
    assert len(sitemaps) == 1
    assert sitemaps[0].loc == "https://example.com/sitemap1.xml"

    index_data = {
        "sitemap": [
            {"loc": "https://example.com/sitemap1.xml"},
            {"loc": "https://example.com/sitemap2.xml"},
        ],
    }
    index = SitemapIndex(index_data)
    assert {s.loc for s in index} == {
        "https://example.com/sitemap1.xml",
        "https://example.com/sitemap2.xml",
    }


def test_sitemapparser_get_urls_and_get_sitemaps() -> None:
    """Validate SiteMapParser behavior for URL sets and sitemap indexes."""
    urlset_xml = """
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url>
            <loc>https://example.com/</loc>
        </url>
    </urlset>
    """

    parser = SiteMapParser(source=urlset_xml, is_data_string=True)
    assert parser.has_urls()
    assert not parser.has_sitemaps()
    urls: list[Url] = list(parser.get_urls())
    assert urls[0].loc == "https://example.com/"

    with pytest.raises(
        KeyError,
        match="Method called when root is not a <sitemapindex>",
    ):
        parser.get_sitemaps()

    sitemapindex_xml = """
    <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <sitemap>
        <loc>https://example.com/sitemap1.xml</loc>
      </sitemap>
    </sitemapindex>
    """

    parser = SiteMapParser(source=sitemapindex_xml, is_data_string=True)
    assert parser.has_sitemaps()
    assert not parser.has_urls()
    sitemaps = list(parser.get_sitemaps())
    assert sitemaps[0].loc == "https://example.com/sitemap1.xml"

    with pytest.raises(
        KeyError,
        match=r"Method called when root is a <sitemapindex>\. Use 'get_sitemaps\(\)' instead",
    ):
        parser.get_urls()


def test_sitemapparser_to_dict_cache_and_runtime_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Validate caching behavior and runtime error when XML data is missing."""
    xml = """
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url>
        <loc>https://example.com/</loc>
      </url>
    </urlset>
    """

    parser = SiteMapParser(source=xml, is_data_string=True)
    cached = parser.to_dict()
    assert cached["urlset"]["url"][0]["loc"] == "https://example.com/"

    def failing_parse(*args: object, **kwargs: object) -> dict[str, object]:
        pytest.fail("xmltodict.parse should not be called")

    monkeypatch.setattr(py_sitemap_parser.xmltodict, "parse", failing_parse)
    assert parser.to_dict()["urlset"]["url"][0]["loc"] == "https://example.com/"

    called: dict[str, bool] = {"seen": False}

    def tracing_parse(*args: object, **kwargs: object) -> dict[str, object]:
        called["seen"] = True
        return {"root": {}}

    monkeypatch.setattr(py_sitemap_parser.xmltodict, "parse", tracing_parse)
    parser.to_dict(process_namespaces=True)
    assert called["seen"]

    parser._xml_bytes = None  # type: ignore[attr-defined]
    with pytest.raises(RuntimeError, match="No XML data available to parse"):
        parser.to_dict()


def test_jsonexporter_exports_urls_and_sitemaps() -> None:
    """Validate JSONExporter output for urls and sitemaps."""
    urlset_xml = """
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url>
            <loc>https://example.com/</loc>
            <lastmod>2023-08-01</lastmod>
            <changefreq>daily</changefreq>
            <priority>0.2</priority>
        </url>
    </urlset>
    """

    parser = SiteMapParser(source=urlset_xml, is_data_string=True)
    exporter = JSONExporter(data=parser)
    out = exporter.export_urls()
    assert json.loads(out) == [
        {
            "loc": "https://example.com/",
            "lastmod": "2023-08-01T00:00:00",
            "changefreq": "daily",
            "priority": 0.2,
        },
    ]

    sitemapindex_xml = """
    <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <sitemap>
        <loc>https://example.com/sitemap1.xml</loc>
        <lastmod>2023-08-01</lastmod>
      </sitemap>
    </sitemapindex>
    """

    parser = SiteMapParser(source=sitemapindex_xml, is_data_string=True)
    exporter = JSONExporter(data=parser)
    out: str = exporter.export_sitemaps()
    assert json.loads(out) == [
        {"loc": "https://example.com/sitemap1.xml", "lastmod": "2023-08-01T00:00:00"},
    ]


def test_download_uri_data_success_and_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    """Validate download_uri_data handles empty content and HTTP errors."""

    class DummyResponse:
        def __init__(self, content: bytes, should_raise: bool = False) -> None:
            self.content = content
            self._should_raise = should_raise

        def raise_for_status(self) -> None:
            if self._should_raise:
                msg = "boom"
                raise niquests.HTTPError(msg)

    def fake_get_success(uri: str) -> DummyResponse:
        return DummyResponse(b"<xml></xml>")

    monkeypatch.setattr("py_sitemap_parser.niquests.get", fake_get_success)
    assert download_uri_data("https://example.com") == b"<xml></xml>"

    def fake_get_empty(uri: str) -> DummyResponse:
        return DummyResponse(b"")

    monkeypatch.setattr("py_sitemap_parser.niquests.get", fake_get_empty)
    with pytest.raises(ValueError, match="No content found at"):
        download_uri_data("https://example.com")

    def fake_get_http_error(uri: str) -> DummyResponse:
        return DummyResponse(b"<xml></xml>", should_raise=True)

    monkeypatch.setattr("py_sitemap_parser.niquests.get", fake_get_http_error)
    with pytest.raises(niquests.HTTPError):
        download_uri_data("https://example.com")


def test_sitemap_str_returns_loc() -> None:
    """Validate that Sitemap __str__ returns the loc value."""
    sitemap = Sitemap(loc="https://example.com/sitemap.xml", lastmod="2023-08-01")
    assert str(sitemap) == "https://example.com/sitemap.xml"


def test_sitemap_str_raises_value_error_when_loc_none() -> None:
    """Validate that Sitemap __str__ raises ValueError when loc is None."""
    sitemap = Sitemap(loc="https://example.com/sitemap.xml")
    sitemap._loc = None  # pyright: ignore[reportPrivateUsage] # bypass setter for test
    with pytest.raises(ValueError, match="loc cannot be None"):
        str(sitemap)


def test_sitemapindex_str() -> None:
    """Validate that SitemapIndex __str__ returns a summary of the index."""
    index_data: dict[str, dict[str, str]] = {
        "sitemap": {"loc": "https://example.com/sitemap1.xml"},
    }
    index = SitemapIndex(index_data)
    assert str(index) == f"<SitemapIndex: {index_data}>"


def test_url_str_returns_loc() -> None:
    """Validate that Url __str__ returns the loc value."""
    url = Url(loc="https://example.com/", lastmod="2023-08-01")
    assert str(url) == "https://example.com/"


def test_url_str_returns_empty_when_loc_none() -> None:
    """Validate that Url __str__ returns empty string when loc is None."""
    url = Url(loc="https://example.com/", lastmod="2023-08-01")
    url._loc = None  # pyright: ignore[reportPrivateUsage] # bypass setter for test
    assert not str(url)


def test_urlset_str_via_site_map_parser() -> None:
    """Validate that SiteMapParser __str__ returns the string representation of the URLs when root is a URL set."""
    xml = """
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url>
            <loc>https://example.com/</loc>
        </url>
    </urlset>
    """
    parser = SiteMapParser(source=xml, is_data_string=True)
    assert str(parser) == str(parser.get_urls())


def test_sitemapindex_str_via_site_map_parser() -> None:
    """Validate that SiteMapParser __str__ returns the string representation of the sitemaps when root is a sitemap index."""
    xml = """
    <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <sitemap>
        <loc>https://example.com/sitemap1.xml</loc>
      </sitemap>
    </sitemapindex>
    """
    parser = SiteMapParser(source=xml, is_data_string=True)
    assert str(parser) == str(parser.get_sitemaps())
