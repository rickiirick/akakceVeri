import argparse
import json
import re
import time
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.akakce.com/son-alti-ayin-en-ucuz-fiyatli-urunleri/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
}


def parse_price(text):
    if not text:
        return 0.0
    cleaned = re.sub(r"[^\d,]", "", text).replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def parse_discount(text):
    if not text:
        return 0
    match = re.search(r"%\s*(\d+)", text)
    return int(match.group(1)) if match else 0


def scrape_range(start_page, end_page):
    session = requests.Session()
    session.headers.update(HEADERS)
    deals = []
    seen_ids = set()

    for page in range(start_page, end_page + 1):
        url = f"{BASE_URL}?p={page}"
        try:
            resp = session.get(url, timeout=15)
            if resp.status_code == 429:
                print(f"[Sayfa {page}] 429 Rate Limit, bu makine durduruluyor.")
                break
            if resp.status_code != 200:
                print(f"[Sayfa {page}] HTTP {resp.status_code}, atlanıyor.")
                break
        except Exception as e:
            print(f"[Sayfa {page}] İstek hatası: {e}")
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.select("ul#APL > li") or soup.select("li.w")
        if not items:
            print(f"[Sayfa {page}] Ürün bulunamadı, tarama bitti.")
            break

        page_count = 0
        for item in items:
            link_tag = item.select_one("a.pw_v8") or item.select_one("a[href]")
            title_tag = item.select_one("h3.pn_v8") or item.select_one("h3")
            if not link_tag or not title_tag:
                continue

            href = link_tag.get("href", "")
            full_url = f"https://www.akakce.com{href}" if href.startswith("/") else href
            title = title_tag.get_text(strip=True)

            id_match = re.search(r",(\d+)\.html", full_url)
            prod_id = f"akakce_{id_match.group(1)}" if id_match else f"akakce_{abs(hash(full_url))}"
            if prod_id in seen_ids:
                continue
            seen_ids.add(prod_id)

            price_tag = item.select_one("span.pt_v9") or item.select_one("span.pt_v8")
            price = parse_price(price_tag.get_text(strip=True)) if price_tag else 0.0

            discount = parse_discount(item.get_text(" ", strip=True))

            deals.append({
                "id": prod_id,
                "source": "Akakçe (Son 6 Ay Dip)",
                "title": title,
                "url": full_url,
                "price": price,
                "discount": discount,
                "is_6_months_low": True,
                "stock": ""
            })
            page_count += 1

        print(f"[Sayfa {page}] {page_count} ürün çekildi.")
        if page_count == 0:
            break
        time.sleep(0.5)

    return deals


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, required=True)
    parser.add_argument("--end", type=int, required=True)
    parser.add_argument("--output", type=str, required=True)
    args = parser.parse_args()

    deals = scrape_range(args.start, args.end)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(deals, f, ensure_ascii=False)
    print(f"Toplam {len(deals)} ürün {args.output} dosyasına yazıldı.")


if __name__ == "__main__":
    main()
