"""Public market context for the desktop dashboard."""

import math
import re
import time
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from broker import NETWORKS
from engine import get, markets, shared_fetch
from storage import data_root

FEEDS = {
    "Fed": "https://www.federalreserve.gov/feeds/press_monetary.xml",
    "SEC": "https://www.sec.gov/news/pressreleases.rss",
}
CRYPTO = re.compile(r"\b(?:crypto\w*|bitcoin|ethereum|stablecoins?|digital assets?|tokeniz\w*|blockchain)\b", re.I)


def market_context(network, symbol):
    folder = data_root() / "dashboard"
    market_id = markets(network).get(symbol)
    base_url = NETWORKS[network] + "/api/v1/"

    def load_quotes():
        fields = ("last_trade_price", "daily_price_change", "daily_quote_token_volume")
        rows = get(base_url + "orderBookDetails")["order_book_details"]
        return {row["symbol"]: [row[key] for key in fields] for row in rows
                if row["market_type"] == "perp" and row["status"] == "active"
                and all(isinstance(row.get(key), (float, int)) and math.isfinite(row[key]) for key in fields)}

    def load_book():
        book = get(base_url + "orderBookOrders", {"market_id": market_id, "limit": 50})
        bids, asks = ([tuple(float(row[key]) for key in ("price", "remaining_base_amount")) for row in book[side]]
                      for side in ("bids", "asks"))
        if not bids or not asks or not all(math.isfinite(p) and math.isfinite(q) and p > 0 and q >= 0
                                           for p, q in bids + asks):
            return None
        bid, ask = max(p for p, _ in bids), min(p for p, _ in asks)
        if bid > ask:
            return None
        mid = (bid + ask) / 2
        spread_bps = (ask - bid) / mid * 10000
        bid_depth = sum(p * q for p, q in bids if p >= mid * .9975)
        ask_depth = sum(p * q for p, q in asks if p <= mid * 1.0025)
        return spread_bps, bid_depth, ask_depth, time.time()

    try:
        quotes = shared_fetch(folder / f"quotes-{network}.json", load_quotes, 240)
    except (OSError, ValueError, KeyError):
        quotes = {}
    try:
        book = shared_fetch(folder / f"book-{network}-{symbol}.json", load_book, 45) if market_id is not None else None
    except (OSError, ValueError, KeyError):
        book = None
    return quotes, book


def headlines():
    def load_feed(source, url):
        request = Request(url, headers={"User-Agent": "EMA-Trader/1.0 (public RSS reader)"})
        with urlopen(request, timeout=6) as response:
            body = response.read(262145)
        if len(body) > 262144 or b"<!DOCTYPE" in body.upper():
            return []
        items = []
        for item in ElementTree.fromstring(body).findall("./channel/item"):
            title = " ".join(item.findtext("title", "").split())
            link = urljoin(url, item.findtext("link", "").strip())
            destination = urlsplit(link)
            if not title or destination.scheme != "https" or destination.hostname != urlsplit(url).hostname:
                continue
            if source == "SEC" and not CRYPTO.search(title):
                continue
            try:
                published = parsedate_to_datetime(item.findtext("pubDate", "")).timestamp()
            except (ValueError, TypeError, OverflowError):
                continue
            if published >= time.time() - 30 * 86400:
                items.append((published, title[:220], source, link))
        return sorted(items, reverse=True)[:2]

    items = []
    for source, url in FEEDS.items():
        try:
            items.extend(shared_fetch(data_root() / "dashboard" / f"news-{source}.json",
                                      lambda: load_feed(source, url), 900))
        except (OSError, ElementTree.ParseError, ValueError):
            continue
    latest = sorted(items, reverse=True)
    if len({item[2] for item in latest}) > 1:
        return [latest[0], next(item for item in latest if item[2] != latest[0][2])]
    return latest[:2]
