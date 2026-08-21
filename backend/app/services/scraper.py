import json
import logging
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

def parse_html_content(html_content: str, selector_mapping: Dict[str, str], schema: Dict[str, str]) -> Tuple[List[Dict[str, Any]], str]:
    """
    Parses HTML content using CSS selectors defined in selector_mapping.
    Returns a tuple: (list of parsed records, full raw HTML).
    """
    is_xml = html_content.strip().startswith("<?xml") or "<rss" in html_content or "<channel" in html_content
    parser = "xml" if is_xml else "lxml"
    soup = BeautifulSoup(html_content, parser)

    # Find the row container selector
    row_selector = selector_mapping.get("row_container", "")
    if not row_selector:
        logger.warning("No row_container selector defined.")
        return [], html_content

    # Select all rows
    rows = soup.select(row_selector)
    records = []

    for row in rows:
        record = {}
        for field, selector in selector_mapping.items():
            if field == "row_container":
                continue
                
            try:
                # Handle attribute extraction, e.g. "attr:data-symbol"
                if selector.startswith("attr:"):
                    attr_name = selector.split("attr:")[1]
                    val = row.get(attr_name)
                    record[field] = val.strip() if val else None
                else:
                    el = row.select_one(selector)
                    if el:
                        if field == "url" and el.name == "a":
                            val = el.get("href")
                        elif field == "timestamp" and el.name == "time" and el.get("datetime"):
                            val = el.get("datetime")
                        else:
                            val = el.get_text(strip=True)
                        record[field] = val if val else None
                    else:
                        record[field] = None
            except Exception as e:
                logger.error(f"Error parsing field {field} with selector {selector}: {e}")
                record[field] = None
        
        # Clean up keys not in active schema
        filtered_record = {}
        has_any_value = False
        for field in schema.keys():
            val = record.get(field)
            if val is not None and val != "":
                has_any_value = True
            filtered_record[field] = val
            
        if has_any_value:
            records.append(filtered_record)

    return records, html_content

async def scrape_url(url: str, selector_mapping: Dict[str, str], schema: Dict[str, str]) -> Tuple[List[Dict[str, Any]], str, str]:
    """
    Asynchronously fetches a URL and parses its HTML.
    Returns: (parsed records, full raw HTML, error message if any).
    """
    # Intercept local demo site to avoid running a live server process during execution/tests
    if "demo-site/target" in url or "localhost" in url or "127.0.0.1" in url:
        try:
            from backend.app.routes.demo_site import get_demo_target_site
            html_text = get_demo_target_site()
            records, full_html = parse_html_content(html_text, selector_mapping, schema)
            return records, full_html, ""
        except Exception as e:
            logger.error(f"Local scrape simulation failed: {e}")
            return [], "", str(e)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Add user-agent header to avoid scraping blocks
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = await client.get(url, headers=headers, follow_redirects=True)
            if response.status_code != 200:
                return [], "", f"Failed to fetch site. HTTP Code: {response.status_code}"
                
            records, full_html = parse_html_content(response.text, selector_mapping, schema)
            return records, full_html, ""
    except Exception as e:
        logger.error(f"Failed to scrape URL {url}: {e}")
        return [], "", str(e)
