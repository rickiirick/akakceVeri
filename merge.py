import glob
import json


def main():
    merged = {}
    for path in sorted(glob.glob("parts/**/part_*.json", recursive=True)):
        with open(path, "r", encoding="utf-8") as f:
            items = json.load(f)
            for item in items:
                merged[item["id"]] = item

    result = list(merged.values())
    with open("akakce_raw.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False)
    print(f"Birleştirme tamamlandı: {len(result)} benzersiz ürün.")


if __name__ == "__main__":
    main()
