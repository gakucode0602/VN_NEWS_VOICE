from bs4 import BeautifulSoup
from app.models.article import ArticleBlock
from app.services.crawlers.base_crawler import BaseCrawler, CrawlResult
from typing import List, Optional, Tuple
import feedparser
from datetime import datetime
import re
import html
import logging
from app.services.text_utils import normalize_text

logger = logging.getLogger(__name__)


class ThanhNienCrawler(BaseCrawler):
    def __init__(self):
        super().__init__(
            source_name="thanhnien", base_url="https://thanhnien.vn/", rate_limit=3
        )
        self.rss_url = "https://thanhnien.vn/rss/home.rss"

    @staticmethod
    def _clean_cdata(text: str) -> str:
        # Bóc CDATA nếu có (hỗ trợ <! [CDATA[ ... ]]> với khoảng trắng)
        if not text:
            return ""
        unwrapped = re.sub(r"<!\s*\[CDATA\[(.*?)\]\]>", r"\1", text, flags=re.DOTALL)
        unwrapped = re.sub(r"<[^>]+>", "", unwrapped)
        unwrapped = html.unescape(unwrapped)
        return re.sub(r"\s+", " ", unwrapped).strip()

    async def get_rss_feed_urls(
        self,
        max_articles: int = 5,
        custom_rss_url: Optional[str] = None,
        last_crawl_time: Optional["datetime"] = None,
    ) -> List[Tuple[str, str]]:
        try:
            url_to_fetch = custom_rss_url if custom_rss_url else self.rss_url
            feed = feedparser.parse(url_to_fetch)
            data = []
            count = 0

            from app.services.text_utils import parse_datetime_flexible, parse_rss_date

            parsed_last_time = (
                parse_datetime_flexible(last_crawl_time) if last_crawl_time else None
            )

            for entry in feed.entries:
                if count >= max_articles:
                    break
                if not hasattr(entry, "link"):
                    continue

                if parsed_last_time:
                    published_date = parse_rss_date(entry)
                    if published_date and published_date <= parsed_last_time:
                        continue

                raw_title = getattr(entry, "title", "")
                clean_title = self._clean_cdata(raw_title)
                data.append((entry.link, clean_title))
                count += 1

            return data
        except Exception:
            logger.exception("Error fetching RSS feed")
            return []

    async def crawl_article(
        self, url: str, title_hint: Optional[str] = None
    ) -> CrawlResult:
        try:
            if not self.session:
                raise RuntimeError("Session not initialized. Use 'async with' context.")
            async with self.session.get(url) as response:
                response.raise_for_status()
                html = await response.text()
            soup = BeautifulSoup(html, "html.parser")

            # Extract title
            title = title_hint or (
                soup.find("h1", class_="title-detail").get_text(strip=True)
                if soup.find("h1", class_="title-detail")
                else "No Title Found"
            )

            # Extract sapo (human-written lead paragraph — gold label for training)
            sapo: Optional[str] = None
            sapo_tag = soup.select_one(
                "div.sapo, p.sapo, .article-sapo, h2.detail-sapo"
            )
            if sapo_tag:
                sapo_text = normalize_text(sapo_tag.get_text(" ", strip=True))
                if len(sapo_text) >= 30:
                    sapo = sapo_text

            # Extract Container
            container = None
            potential_containers = [
                "div.detail-cmain",  # Old selector
                "div.sidebar-1",  # New possible selector
                "div.container",  # Generic
                "article",  # Semantic HTML
                ".fck_detail",  # Alternative
                ".content-detail",  # Alternative
                "div[class*='detail']",  # Any div with 'detail' in class
                "div[class*='content']",  # Any div with 'content' in class
            ]
            container = self.select_best_content_container(soup, potential_containers)
            if not container:
                raise ValueError("Could not find main content container")

            ## Get rid of unwanted sections
            unwanted_selectors = [
                "script",
                "style",
                "iframe",
                "nav",
                "header",
                "footer",
                ".breadcrumb",
                ".navigation",
                ".menu",
                ".date",
                ".time-stamp",
                ".meta-info",
                ".social",
                ".share",
                ".comment",
                ".related",
                ".sidebar",
                ".ads",
                ".advertisement",
                '[class*="nav"]',
                '[class*="menu"]',
                '[class*="breadcrumb"]',
                '[class*="header"]',
                '[class*="footer"]',
                '[class*="social"]',
            ]

            for selector in unwanted_selectors:
                for element in container.select(selector):
                    element.decompose()

            ## Get rid of related news sections
            for related_div in container.find_all(["script", "style", "iframe", "ads"]):
                related_div.decompose()

            blocks = self._parse_blocks_from_container(container)

            top_image = ""
            for block in blocks:
                if block.type == "image" and block.src:
                    top_image = block.src
                    break

            if top_image == "":
                top_image = "https://res.cloudinary.com/dg66aou8q/image/upload/v1759936604/original_ib9nin.png"

            return CrawlResult(
                title=title,
                top_image=top_image,
                url=url,
                published_at=None,
                blocks=blocks,
                success=True,
                error_message=None,
                sapo=sapo,
            )

            # Also fix the error case:
        except Exception as e:
            return CrawlResult(
                title="",
                top_image="",
                url=url,
                published_at=None,
                blocks=[],
                success=False,
                error_message=str(e),
            )

    def _parse_blocks_from_container(self, container) -> List[ArticleBlock]:
        blocks = []
        order = 1
        seen_paragraphs = set()
        seen_figcaptions = set()
        seen_image_srcs = set()

        for figure in container.find_all(["figure", "picture"], recursive=True):
            figcaption_tag = figure.find("figcaption")
            if figcaption_tag:
                caption_text = normalize_text(figcaption_tag.get_text(" ", strip=True))
                if caption_text:
                    seen_figcaptions.add(caption_text)

        # Cast a wider net - look for more element types
        elements = container.find_all(
            [
                "p",
                "h1",
                "h2",
                "h3",
                "h4",
                "h5",
                "h6",
                "figure",
                "picture",
                "img",
                "div",
            ],
            recursive=True,
        )

        for elem in elements:
            if elem.name in ["figure", "picture"] and elem.find_parent(
                ["figure", "picture"]
            ):
                continue
            if elem.name == "img" and elem.find_parent(["figure", "picture"]):
                continue
            block_data = {"order": order}

            if elem.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                text = normalize_text(elem.get_text(" ", strip=True))
                if (
                    text and len(text) > 0 and len(text) < 200
                ):  # Reasonable heading length
                    block_data.update(
                        {
                            "type": "heading",
                            "content": text,
                            "text": text,
                            "tag": elem.name,
                        }
                    )
                    blocks.append(ArticleBlock(**block_data))
                    order += 1
                    logger.debug("Added heading: %s", text[:50])

            elif elem.name == "p":
                text = normalize_text(elem.get_text(" ", strip=True))

                # Skip short, empty, or duplicate content
                if (
                    not text
                    or len(text) < 20
                    or text in seen_paragraphs
                    or text in seen_figcaptions
                ):
                    continue
                if elem.find_parent(["figure", "figcaption", "picture"]):
                    continue

                # Skip navigation, ads, etc.
                if elem.has_attr("class"):
                    classes = " ".join(elem["class"]).lower()
                    if any(
                        skip in classes
                        for skip in [
                            "nav",
                            "menu",
                            "ads",
                            "comment",
                            "social",
                            "share",
                            "related",
                        ]
                    ):
                        continue

                seen_paragraphs.add(text)
                block_data.update({"type": "paragraph", "content": text, "text": text})
                blocks.append(ArticleBlock(**block_data))
                order += 1

            elif elem.name in ["figure", "picture", "img"]:
                # Handle direct img tags and img within figure/picture
                img_tag = elem if elem.name == "img" else elem.find("img")
                if not img_tag:
                    continue

                # Extract image source with multiple fallbacks
                src = None
                for attr in ["data-src", "data-original", "data-lazy-src", "src"]:
                    if img_tag.has_attr(attr) and img_tag[attr]:
                        src_value = img_tag[attr]
                        # Skip placeholder images
                        if not src_value.startswith("data:image/"):
                            src = src_value
                            break

                if not src:
                    continue

                # Handle relative URLs
                if src.startswith("//"):
                    src = "https:" + src
                elif src.startswith("/"):
                    src = "https://thanhnien.vn" + src

                if src in seen_image_srcs:
                    continue
                seen_image_srcs.add(src)

                # Extract caption
                caption = ""
                if elem.name == "figure":
                    figcaption_tag = elem.find("figcaption")
                    if figcaption_tag:
                        caption = normalize_text(
                            figcaption_tag.get_text(" ", strip=True)
                        )
                        if caption:
                            seen_figcaptions.add(caption)

                alt_text = img_tag.get("alt", "")

                block_data.update(
                    {
                        "type": "image",
                        "caption": caption,
                        "src": src,
                        "alt": alt_text,
                    }
                )
                blocks.append(ArticleBlock(**block_data))
                order += 1

            # Handle divs with substantial text (fallback for article content)
            elif elem.name == "div":
                text = normalize_text(elem.get_text(" ", strip=True))
                if 30 < len(text) < 1000:  # Reasonable content length
                    # Check if it's likely article content
                    if not elem.find(["script", "style", "nav", "header", "footer"]):
                        if text not in seen_paragraphs and text not in seen_figcaptions:
                            # Check if this div contains mostly text (not other structural elements)
                            child_divs = elem.find_all("div")
                            if len(child_divs) < 3:  # Not too nested
                                seen_paragraphs.add(text)
                                block_data.update(
                                    {"type": "paragraph", "content": text, "text": text}
                                )
                                blocks.append(ArticleBlock(**block_data))
                                order += 1

        logger.info("Total blocks created: %s", len(blocks))
        return blocks
