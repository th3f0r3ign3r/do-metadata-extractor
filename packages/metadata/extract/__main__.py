from bs4 import BeautifulSoup
from http.client import HTTPException
from urllib.parse import urljoin, urlparse
import requests
import json
import re


class MetadataExtractor:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64 ;x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
            }
        )

    def fetch_page(self, url: str) -> tuple[requests.Response, BeautifulSoup]:
        """Fetch and parse HTML page"""
        try:
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            response.raise_for_status()

            # Get the final URL after redirects
            final_url = response.url

            soup = BeautifulSoup(response.content, "html.parser")
            return response, soup, final_url

        except requests.exceptions.RequestException as e:
            raise HTTPException(
                status_code=400, detail=f"Failed to fetch URL: {str(e)}"
            )

    def extract_basic_metadata(self, soup: BeautifulSoup) -> dict:
        """Extract basic HTML metadata"""
        metadata = {}

        # Title
        title_tag = soup.find("title")
        if title_tag:
            metadata["title"] = title_tag.get_text().strip()

        # Meta description
        desc_tag = soup.find("meta", attrs={"name": "description"})
        if desc_tag:
            metadata["description"] = desc_tag.get("content", "").strip()

        # Language
        html_tag = soup.find("html")
        if html_tag and html_tag.get("lang"):
            metadata["lang"] = html_tag.get("lang")

        # Author
        author_tag = soup.find("meta", attrs={"name": "author"})
        if author_tag:
            metadata["author"] = author_tag.get("content", "").strip()

        # Canonical URL
        canonical_tag = soup.find("link", attrs={"rel": "canonical"})
        if canonical_tag:
            metadata["canonical_url"] = canonical_tag.get("href")

        # Image (og:image or first image)
        image_tag = soup.find("meta", attrs={"property": "og:image"})
        if image_tag:
            metadata["image"] = image_tag.get("content", "").strip()
        elif soup.find("img"):
            first_img = soup.find("img")
            if first_img and first_img.get("src"):
                metadata["image"] = first_img.get("src")

        return metadata

    def extract_open_graph(self, soup: BeautifulSoup) -> dict:
        """Extract Open Graph metadata"""
        og_data = {}
        og_tags = soup.find_all("meta", attrs={"property": re.compile(r"^og:")})

        for tag in og_tags:
            prop = tag.get("property", "")
            content = tag.get("content", "")
            if prop and content:
                # Remove 'og:' prefix and store
                key = prop.replace("og:", "")
                og_data[key] = content

        return og_data

    def extract_twitter_card(self, soup: BeautifulSoup) -> dict:
        """Extract Twitter Card metadata"""
        twitter_data = {}
        twitter_tags = soup.find_all("meta", attrs={"name": re.compile(r"^twitter:")})

        for tag in twitter_tags:
            name = tag.get("name", "")
            content = tag.get("content", "")
            if name and content:
                # Remove 'twitter:' prefix and store
                key = name.replace("twitter:", "")
                twitter_data[key] = content

        return twitter_data

    def extract_schema_org(self, soup: BeautifulSoup) -> dict:
        """Extract Schema.org JSON-LD data"""
        schema_data = {}

        # Find JSON-LD scripts
        scripts = soup.find_all("script", type="application/ld+json")

        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    schema_data.update(data)
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            schema_data.update(item)
            except (json.JSONDecodeError, AttributeError):
                continue

        return schema_data

    def extract_favicon(self, soup: BeautifulSoup, base_url: str) -> str:
        """Extract favicon URL"""
        # Try various favicon link relations
        favicon_selectors = [
            'link[rel="icon"]',
            'link[rel="shortcut icon"]',
            'link[rel="apple-touch-icon"]',
            'link[rel="apple-touch-icon-precomposed"]',
        ]

        for selector in favicon_selectors:
            favicon_tag = soup.select_one(selector)
            if favicon_tag and favicon_tag.get("href"):
                return urljoin(base_url, favicon_tag.get("href"))

        # Default favicon.ico
        return urljoin(base_url, "/favicon.ico")

    def consolidate_metadata(
        self, basic: dict, og: dict, twitter: dict, schema: dict, domain: str
    ) -> dict:
        """Consolidate metadata from different sources with priority"""
        consolidated = {}

        # Title priority: OG > Twitter > Basic > Schema
        consolidated["title"] = (
            og.get("title")
            or twitter.get("title")
            or basic.get("title")
            or schema.get("name")
            or schema.get("headline")
        )

        # Description priority: OG > Twitter > Basic > Schema
        consolidated["description"] = (
            og.get("description")
            or twitter.get("description")
            or basic.get("description")
            or schema.get("description")
        )

        # Image priority: OG > Twitter > Schema > Basic
        consolidated["image"] = (
            og.get("image")
            or twitter.get("image")
            or schema.get("image")
            or basic.get("image")
            if basic.get("image")
            and basic.get("image").startswith(("http://", "https://"))
            else f"https://{domain}" + basic.get("image", "").strip()
        )

        # Site name
        consolidated["site_name"] = (
            og.get("site_name")
            or twitter.get("site")
            or schema.get("publisher", {}).get("name")
            if isinstance(schema.get("publisher"), dict)
            else (
                None or domain.split(".")[-2].capitalize()
                if len(domain.split(".")) > 1
                else None
            )
        )

        # Author
        consolidated["author"] = (
            basic.get("author")
            or (
                schema.get("author", {}).get("name")
                if isinstance(schema.get("author"), dict)
                else (
                    schema.get("author")[0].get("mainEntity").get("name")
                    if isinstance(schema.get("author"), list)
                    and len(schema.get("author")) > 0
                    and isinstance(schema.get("author")[0], dict)
                    else schema.get("author")
                )
            )
        ) or None

        # Other basic metadata
        consolidated["lang"] = basic.get("lang")
        consolidated["canonical_url"] = basic.get("canonical_url")

        return consolidated

    def extract_metadata(self, url: str) -> dict:
        """Main extraction method"""
        response, soup, final_url = self.fetch_page(url)
        domain = urlparse(final_url).netloc.replace("www.", "")
        base_url = f"{urlparse(final_url).scheme}://{domain}"

        # Extract from different sources
        basic_metadata = self.extract_basic_metadata(soup)
        og_metadata = self.extract_open_graph(soup)
        twitter_metadata = self.extract_twitter_card(soup)
        schema_metadata = self.extract_schema_org(soup)

        # Consolidate metadata
        consolidated = self.consolidate_metadata(
            basic_metadata, og_metadata, twitter_metadata, schema_metadata, domain
        )

        # Extract additional metadata
        favicon = self.extract_favicon(soup, base_url)

        # Build response
        return {
            "url": final_url,
            "domain": domain,
            "title": consolidated.get("title"),
            "description": consolidated.get("description"),
            "image": consolidated.get("image"),
            "site_name": consolidated.get("site_name"),
            "type": consolidated.get("type"),
            "author": consolidated.get("author"),
            "lang": consolidated.get("lang"),
            "canonical_url": consolidated.get("canonical_url"),
            "favicon": favicon,
            "open_graph": og_metadata if og_metadata else None,
            "twitter_card": twitter_metadata if twitter_metadata else None,
            "schema_org": schema_metadata if schema_metadata else None,
        }


extractor = MetadataExtractor()


def main(args):
    url = args.get("url")
    if not url:
        return {"statusCode": 400, "body": {"error": "Missing 'url' parameter"}}
    try:
        metadata = extractor.extract_metadata(url)
        return {
            "statusCode": 200,
            "body": metadata.model_dump(),
        }
    except Exception as e:
        return {"statusCode": 500, "body": {"error": str(e)}}
