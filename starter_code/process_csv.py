import pandas as pd
from typing import Any, Optional, Tuple


def _parse_price(raw: Any, currency: Any) -> Tuple[Optional[float], str]:
    """Normalize price to float where possible; return (None, currency) for missing/contact."""
    if pd.isna(raw):
        return None, (str(currency).strip().upper() if pd.notna(currency) else "VND")

    s = str(raw).strip()
    cur = str(currency).strip().upper() if pd.notna(currency) else "VND"

    if s.upper() in ("N/A", "NULL", "") or s in ("Liên hệ", "liên hệ"):
        return None, cur

    low = s.lower()
    if "five dollars" in low:
        return 5.0, "USD"

    cleaned = s.replace("$", "").replace(",", "").strip()
    try:
        return float(cleaned), cur
    except ValueError:
        return None, cur


def process_sales_csv(file_path):
    df = pd.read_csv(file_path)
    df = df.drop_duplicates(subset=["id"], keep="last")

    dt = pd.to_datetime(df["date_of_sale"], errors="coerce", dayfirst=True)
    df = df.assign(date_normalized=dt.dt.strftime("%Y-%m-%d"))

    out = []
    for _, row in df.iterrows():
        price_val, cur = _parse_price(row.get("price"), row.get("currency"))
        meta = {
            "product_name": row.get("product_name"),
            "category": row.get("category"),
            "price": price_val,
            "currency": cur,
            "seller_id": row.get("seller_id"),
            "stock_quantity": int(row["stock_quantity"])
            if pd.notna(row.get("stock_quantity")) and str(row.get("stock_quantity")).strip() != ""
            else None,
        }
        content_parts = [
            f"Sale record id {int(row['id'])}: {row.get('product_name')} ({row.get('category')}).",
            f"Price: {price_val} {cur}." if price_val is not None else "Price: not listed.",
            f"Date of sale: {row['date_normalized']}. Seller {row.get('seller_id')}.",
        ]
        content = " ".join(content_parts)

        out.append(
            {
                "document_id": f"csv-{int(row['id'])}",
                "content": content,
                "source_type": "CSV",
                "author": str(row.get("seller_id") or "Unknown"),
                "timestamp": None,
                "source_metadata": meta,
            }
        )
    return out
