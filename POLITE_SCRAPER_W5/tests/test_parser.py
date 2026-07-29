from decimal import Decimal

from app.parser import (
    parse_book_page,
    parse_listing_page,
)


LISTING_HTML = """
<html>
<body>

<article class="product_pod">
    <h3>
        <a href="book-one_1/index.html">
            Book One
        </a>
    </h3>
</article>

<article class="product_pod">
    <h3>
        <a href="book-two_2/index.html">
            Book Two
        </a>
    </h3>
</article>

<li class="next">
    <a href="page-2.html">next</a>
</li>

</body>
</html>
"""


DETAIL_HTML = """
<html>
<body>

<ul class="breadcrumb">
    <li>Home</li>
    <li>Books</li>
    <li>Travel</li>
    <li>Example Book</li>
</ul>

<div class="item active">
    <img src="../../media/example.jpg">
</div>

<div class="product_main">
    <h1> Example   Book </h1>

    <p class="price_color">
        £12.34
    </p>

    <p class="instock availability">
        In stock (7 available)
    </p>

    <p class="star-rating Four"></p>
</div>

<div id="product_description"></div>
<p>A useful description.</p>

<table class="table table-striped">

<tr>
    <th>UPC</th>
    <td>abc123</td>
</tr>

<tr>
    <th>Product Type</th>
    <td>Books</td>
</tr>

<tr>
    <th>Price (excl. tax)</th>
    <td>£12.34</td>
</tr>

<tr>
    <th>Price (incl. tax)</th>
    <td>£12.34</td>
</tr>

<tr>
    <th>Tax</th>
    <td>£0.00</td>
</tr>

<tr>
    <th>Availability</th>
    <td>In stock (7 available)</td>
</tr>

<tr>
    <th>Number of reviews</th>
    <td>2</td>
</tr>

</table>

</body>
</html>
"""


def test_parse_listing_page_resolves_links() -> None:
    links, next_url = parse_listing_page(
        LISTING_HTML,
        (
            "https://books.toscrape.com/"
            "catalogue/page-1.html"
        ),
    )

    assert links == [
        (
            "https://books.toscrape.com/"
            "catalogue/book-one_1/index.html"
        ),
        (
            "https://books.toscrape.com/"
            "catalogue/book-two_2/index.html"
        ),
    ]

    assert next_url == (
        "https://books.toscrape.com/"
        "catalogue/page-2.html"
    )


def test_parse_book_page_extracts_and_cleans_fields() -> None:
    book = parse_book_page(
        DETAIL_HTML,
        (
            "https://books.toscrape.com/"
            "catalogue/example-book_1/index.html"
        ),
    )

    assert book.upc == "abc123"
    assert book.title == "Example Book"
    assert book.category == "Travel"

    assert book.price_gbp == Decimal(
        "12.34"
    )

    assert book.stock_count == 7
    assert book.in_stock is True
    assert book.rating == 4
    assert book.review_count == 2

    assert book.description == (
        "A useful description."
    )

    assert str(book.image_url) == (
        "https://books.toscrape.com/"
        "media/example.jpg"
    )