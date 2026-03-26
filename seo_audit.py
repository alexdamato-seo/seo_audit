import requests
from bs4 import BeautifulSoup
import csv
import time

urls_with_gsc = [
    {"url": "https://evidentscientific.com/en/life-science-microscopes/software", "clicks": 176, "impressions": 16621, "ctr": 1.06, "position": 18.34},
    {"url": "https://evidentscientific.com/en/clinical-microscopes/slide-scanners", "clicks": 151, "impressions": 19469, "ctr": 0.78, "position": 18.92},
    {"url": "https://evidentscientific.com/en/clinical-microscopes/inverted", "clicks": 10, "impressions": 4383, "ctr": 0.23, "position": 26.77},
    {"url": "https://evidentscientific.com/en/digital-cameras", "clicks": 284, "impressions": 27671, "ctr": 1.03, "position": 18.88},
    {"url": "https://evidentscientific.com/en/digital-cameras/color", "clicks": 87, "impressions": 12909, "ctr": 0.67, "position": 19.76},
    {"url": "https://evidentscientific.com/en/life-science-microscopes/super-resolution", "clicks": 49, "impressions": 15532, "ctr": 0.32, "position": 11.8},
    {"url": "https://evidentscientific.com/en/life-science-microscopes/stereo", "clicks": 497, "impressions": 84008, "ctr": 0.59, "position": 11.55},
    {"url": "https://evidentscientific.com/en/life-science-microscopes/spinning-disk-confocal", "clicks": 127, "impressions": 12192, "ctr": 1.04, "position": 9.59},
    {"url": "https://evidentscientific.com/en/life-science-microscopes/inverted", "clicks": 369, "impressions": 62827, "ctr": 0.59, "position": 9.13},
    {"url": "https://evidentscientific.com/en/material-science-microscopes/digital-cameras", "clicks": 75, "impressions": 13979, "ctr": 0.54, "position": 19.7},
    {"url": "https://evidentscientific.com/en/material-science-microscopes/cleanliness-and-particle-analysis", "clicks": 52, "impressions": 6632, "ctr": 0.78, "position": 17.83},
    {"url": "https://evidentscientific.com/en/material-science-microscopes/digital", "clicks": 250, "impressions": 56033, "ctr": 0.45, "position": 13.46},
    {"url": "https://evidentscientific.com/en/material-science-microscopes/3d-optical-profilometers", "clicks": 56, "impressions": 88838, "ctr": 0.06, "position": 12.09},
    {"url": "https://evidentscientific.com/en/material-science-microscopes/semiconductor-inspection", "clicks": 62, "impressions": 14529, "ctr": 0.43, "position": 17.7},
    {"url": "https://evidentscientific.com/en/life-science-microscopes/confocal", "clicks": 147, "impressions": 50782, "ctr": 0.29, "position": 13.92},
    {"url": "https://evidentscientific.com/en/material-science-microscopes/coordinate-measuring", "clicks": 63, "impressions": 12678, "ctr": 0.50, "position": 11.05},
    {"url": "https://evidentscientific.com/en/material-science-microscopes/industrial-stereo", "clicks": 39, "impressions": 11476, "ctr": 0.34, "position": 21.54},
    {"url": "https://evidentscientific.com/en/material-science-microscopes/light", "clicks": 53, "impressions": 32455, "ctr": 0.16, "position": 11.12},
    {"url": "https://evidentscientific.com/en/material-science-microscopes/metallurgical", "clicks": 65, "impressions": 13556, "ctr": 0.48, "position": 8.86},
    {"url": "https://evidentscientific.com/en/material-science-microscopes/image-analysis-software", "clicks": 86, "impressions": 14468, "ctr": 0.59, "position": 24.64},
    {"url": "https://evidentscientific.com/en/life-science-microscopes/slide-scanners", "clicks": 171, "impressions": 72574, "ctr": 0.24, "position": 7.92},
    {"url": "https://evidentscientific.com/en/life-science-microscopes/upright", "clicks": 0, "impressions": 1, "ctr": 0.0, "position": 2.0},
    {"url": "https://evidentscientific.com/en/digital-cameras/mono", "clicks": 27, "impressions": 3622, "ctr": 0.75, "position": 15.62},
    {"url": "https://evidentscientific.com/en/life-science-microscopes/objectives", "clicks": 295, "impressions": 21955, "ctr": 1.34, "position": 7.17},
    {"url": "https://evidentscientific.com/en/material-science-microscopes/objectives/white-light-interferometry", "clicks": 84, "impressions": 6543, "ctr": 1.28, "position": 29.67},
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}

# Tags and attributes whose text should be excluded from word count
INVISIBLE_TAGS = {"script", "style", "noscript", "head", "meta", "link", "title"}


def get_visible_text(soup):
    for tag in soup(INVISIBLE_TAGS):
        tag.decompose()
    return soup.get_text(separator=" ", strip=True)


def audit_url(entry):
    url = entry["url"]
    print(f"  Auditing: {url}")

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        return {**entry, "error": str(e)}

    soup = BeautifulSoup(resp.text, "html.parser")

    # --- Title ---
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""
    title_len = len(title)

    # --- Meta description ---
    meta_tag = soup.find("meta", attrs={"name": lambda n: n and n.lower() == "description"})
    meta_desc = meta_tag.get("content", "").strip() if meta_tag else ""
    meta_len = len(meta_desc)

    # --- H1 ---
    h1_tag = soup.find("h1")
    h1 = h1_tag.get_text(strip=True) if h1_tag else ""

    # --- H2s ---
    h2_tags = soup.find_all("h2")
    h2s = ", ".join(t.get_text(strip=True) for t in h2_tags)

    # --- Word count (visible body text) ---
    body = soup.find("body")
    visible_text = get_visible_text(body) if body else ""
    word_count = len(visible_text.split())

    # --- Images missing alt ---
    images = soup.find_all("img")
    missing_alt = sum(
        1 for img in images
        if not img.get("alt", "").strip()
    )

    # --- Canonical ---
    canonical_tag = soup.find("link", attrs={"rel": lambda r: r and "canonical" in r})
    canonical = canonical_tag.get("href", "").strip() if canonical_tag else ""

    # --- Flags ---
    flags = []
    if not title or title_len > 60:
        flags.append("Title Issue")
    if not meta_desc or meta_len > 155:
        flags.append("Meta Issue")
    if not h1:
        flags.append("Missing H1")
    if word_count < 300:
        flags.append("Thin Content")
    if entry["impressions"] > 5000 and entry["ctr"] < 1.0:
        flags.append("Low CTR")

    return {
        "url": url,
        "clicks": entry["clicks"],
        "impressions": entry["impressions"],
        "ctr": entry["ctr"],
        "position": entry["position"],
        "title": title,
        "title_len": title_len,
        "meta_description": meta_desc,
        "meta_len": meta_len,
        "h1": h1,
        "h2s": h2s,
        "word_count": word_count,
        "images_missing_alt": missing_alt,
        "canonical": canonical,
        "flags": " | ".join(flags) if flags else "OK",
        "error": "",
    }


def main():
    results = []
    for i, entry in enumerate(urls_with_gsc):
        result = audit_url(entry)
        results.append(result)
        if i < len(urls_with_gsc) - 1:
            time.sleep(1)  # polite crawl delay

    output_file = "seo_audit_results.csv"
    fieldnames = [
        "url", "clicks", "impressions", "ctr", "position",
        "title", "title_len", "meta_description", "meta_len",
        "h1", "h2s", "word_count", "images_missing_alt",
        "canonical", "flags", "error",
    ]

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\nDone. Results saved to {output_file}")

    # Summary
    flag_counts = {}
    for r in results:
        for flag in r.get("flags", "").split(" | "):
            if flag and flag != "OK":
                flag_counts[flag] = flag_counts.get(flag, 0) + 1

    if flag_counts:
        print("\nFlag summary:")
        for flag, count in sorted(flag_counts.items(), key=lambda x: -x[1]):
            print(f"  {flag}: {count} URL(s)")


if __name__ == "__main__":
    main()
