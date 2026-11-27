import argparse
import json
import re
import time
from curl_cffi import requests
from bs4 import BeautifulSoup


def parse_price(text):
    if not text:
        return None
    cleaned = re.sub(r"[^\d,]", "", text).replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def scrape_range(start_page, end_page):
    deals = []
    seen_ids = set()
    session = requests.Session(impersonate="chrome")

    for page in range(start_page, end_page + 1):
        url = f"https://www.akakce.com/son-alti-ayin-en-ucuz-fiyatli-urunleri/?c=1&s=7&p1=250&p2=5000&p={page}"
        try:
            resp = session.get(url, timeout=20)
            if resp.status_code == 429:
                print(f"[Sayfa {page}] 429 Rate Limit, bu makine durduruluyor.")
                break
            if resp.status_code != 200:
                print(f"[Sayfa {page}] HTTP Hatası: {resp.status_code}")
                break

            soup = BeautifulSoup(resp.text, "html.parser")
            items = soup.select("ul#CPL li, ul.pl_v9 li")
            if not items:
                print(f"[Sayfa {page}] Ürün bulunamadı, tarama bitti.")
                break

            yeni_urun_sayisi = 0

            for item in items:
                a_tag = item.find("a", href=True)
                if not a_tag:
                    continue

                title = a_tag.get("title") or a_tag.get_text(strip=True)
                link = a_tag["href"]
                if not link.startswith("http"):
                    link = "https://www.akakce.com" + link

                item_id = f"akakce_{link.split('/')[-1]}"
                if item_id in seen_ids:
                    continue
                seen_ids.add(item_id)

                price_el = item.select_one(".pt_v9, .pt_v8")
                price = parse_price(price_el.get_text(strip=True)) if price_el else None
                if not price:
                    continue

                text_all = item.get_text(" ", strip=True).lower()

                discount = 0
                disc_match = re.search(r"%\s*(\d+)", text_all)
                if disc_match:
                    discount = int(disc_match.group(1))

                stock_match = re.search(r"(son\s+\d+\s+adet|\d+\s+adet\s+kaldı)", text_all)
                stock_info = stock_match.group(1).title() if stock_match else None

                deals.append({
                    "id": item_id,
                    "source": "Akakçe (Son 6 Ay Dip)",
                    "title": title,
                    "price": price,
                    "discount": discount,
                    "is_6_months_low": False,
                    "stock": stock_info,
                    "url": link
                })
                yeni_urun_sayisi += 1

            print(f"[Sayfa {page}] {yeni_urun_sayisi} ürün çekildi.")
            if yeni_urun_sayisi == 0:
                break

            time.sleep(0.5)

        except Exception as e:
            print(f"[Sayfa {page}] Hata: {e}")
            break

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
