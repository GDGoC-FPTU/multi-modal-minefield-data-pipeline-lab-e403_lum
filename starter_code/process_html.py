from bs4 import BeautifulSoup


def _normalize_price_cell(text: str) -> str:
    t = (text or "").strip()
    if not t:
        return ""
    if t.upper() == "N/A" or t.lower() == "liên hệ":
        return t
    # e.g. "28,500,000 VND" -> keep digits and label
    return t


def parse_html_catalog(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    table = soup.find("table", id="main-catalog")
    if not table:
        return []

    tbody = table.find("tbody")
    if not tbody:
        return []

    rows = []
    for tr in tbody.find_all("tr"):
        cells = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(cells) < 6:
            continue
        sku, name, category, price_cell, stock, rating = cells[:6]
        price_display = _normalize_price_cell(price_cell)
        rows.append(
            {
                "document_id": f"html-{sku}",
                "content": (
                    f"Catalog product {sku}: {name}. Category: {category}. "
                    f"Listed price: {price_display}. Stock: {stock}. Rating: {rating}."
                ),
                "source_type": "HTML",
                "author": "VinShop",
                "timestamp": None,
                "source_metadata": {
                    "sku": sku,
                    "product_name": name,
                    "category": category,
                    "price_display": price_display,
                    "stock": stock,
                    "rating": rating,
                },
            }
        )
    return rows
