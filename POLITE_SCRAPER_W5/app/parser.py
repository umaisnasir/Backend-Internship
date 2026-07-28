import re
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.exceptions import ParseError
from app.models import BookRecord


RATING_MAP = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5,
}


def clean_text(value: str) -> str:
    return " ".join(value.split())


def parse_money(value: str) -> Decimal:
    cleaned = value.replace("£", "").strip()

    try:
        return Decimal(cleaned)
    except InvalidOperation as exc:
        raise ParseError(f"Invalid money value: {value!r}") from exc


def parse_integer(value: str, field_name: str) -> int:
    match = re.search(r"\d+", value.replace(",", ""))

    if not match:
        raise ParseError(
            f"Could not parse integer for {field_name}: {value!r}"
        )

    return int(match.group())


def parse_listing_page(
    html: str,
    page_url: str,
) -> tuple[list[str], str | None]:
    soup = BeautifulSoup(html, "html.parser")

    book_links = [
        urljoin(page_url, anchor["href"])
        for anchor in soup.select(
            "article.product_pod h3 a[href]"
        )
    ]

    if not book_links:
        raise ParseError(
            f"No book links found on listing page: {page_url}"
        )

    next_anchor = soup.select_one("li.next a[href]")

    next_url = (
        urljoin(page_url, next_anchor["href"])
        if next_anchor
        else None
    )

    return book_links, next_url


def parse_book_page(html: str, page_url: str) -> BookRecord:
    soup = BeautifulSoup(html, "html.parser")

    title_node = soup.select_one("div.product_main h1")
    price_node = soup.select_one(
        "div.product_main p.price_color"
    )
    availability_node = soup.select_one(
        "div.product_main p.instock.availability"
    )
    rating_node = soup.select_one(
        "div.product_main p.star-rating"
    )
    image_node = soup.select_one(
        "div.item.active img[src]"
    )

    required_nodes = {
        "title": title_node,
        "price": price_node,
        "availability": availability_node,
        "rating": rating_node,
        "image": image_node,
    }

    missing = [
        name
        for name, node in required_nodes.items()
        if node is None
    ]

    if missing:
        raise ParseError(
            f"Missing required fields {missing} on {page_url}"
        )

    table: dict[str, str] = {}

    for row in soup.select("table.table.table-striped tr"):
        heading = row.find("th")
        value = row.find("td")

        if heading and value:
            table[clean_text(heading.get_text())] = clean_text(
                value.get_text()
            )

    required_table_keys = {
        "UPC",
        "Product Type",
        "Price (excl. tax)",
        "Price (incl. tax)",
        "Tax",
        "Availability",
        "Number of reviews",
    }

    missing_table = sorted(
        required_table_keys - table.keys()
    )

    if missing_table:
        raise ParseError(
            f"Missing product table fields "
            f"{missing_table} on {page_url}"
        )

    breadcrumbs = [
        clean_text(node.get_text())
        for node in soup.select("ul.breadcrumb li")
    ]

    if len(breadcrumbs) < 3:
        raise ParseError(
            f"Could not determine category on {page_url}"
        )

    category = breadcrumbs[-2]

    rating_classes = set(
        rating_node.get("class", [])
    )

    rating_name = next(
        (
            name
            for name in RATING_MAP
            if name in rating_classes
        ),
        None,
    )

    if rating_name is None:
        raise ParseError(
            f"Unknown rating class "
            f"{sorted(rating_classes)} on {page_url}"
        )

    availability_text = clean_text(
        availability_node.get_text()
    )

    stock_count = parse_integer(
        table["Availability"],
        "stock_count",
    )

    description_heading = soup.select_one(
        "#product_description"
    )

    description_node = (
        description_heading.find_next_sibling("p")
        if description_heading
        else None
    )

    description = (
        clean_text(description_node.get_text())
        if description_node
        else None
    )

    image_url = urljoin(
        page_url,
        image_node["src"],
    )

    return BookRecord(
        upc=table["UPC"],
        title=clean_text(title_node.get_text()),
        category=category,
        product_type=table["Product Type"],
        price_gbp=parse_money(price_node.get_text()),
        price_excl_tax_gbp=parse_money(
            table["Price (excl. tax)"]
        ),
        price_incl_tax_gbp=parse_money(
            table["Price (incl. tax)"]
        ),
        tax_gbp=parse_money(table["Tax"]),
        availability_text=availability_text,
        stock_count=stock_count,
        in_stock=stock_count > 0,
        rating=RATING_MAP[rating_name],
        review_count=parse_integer(
            table["Number of reviews"],
            "review_count",
        ),
        description=description,
        image_url=image_url,
        source_url=page_url,
        scraped_at=datetime.now(UTC),
    )