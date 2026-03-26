import os
import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel
import anthropic
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


class SEOSuggestion(BaseModel):
    suggested_title: str
    suggested_meta: str


def generate_suggestions(client, result):
    """Call Claude to generate an improved title and meta for a flagged page."""
    slug = result["url"].replace("https://evidentscientific.com/en/", "")

    prompt = (
        f"You are an SEO specialist writing copy for Evident Scientific, a manufacturer of "
        f"high-end microscopes and imaging equipment.\n\n"
        f"Page: {slug}\n"
        f"Current title: {result.get('title') or 'Missing'}\n"
        f"Current meta: {result.get('meta_description') or 'Missing'}\n"
        f"H1: {result.get('h1') or 'Missing'}\n"
        f"H2s: {result.get('h2s') or 'None'}\n"
        f"GSC impressions (3 mo): {result['impressions']} | CTR: {result['ctr']}% | Avg position: {result['position']}\n"
        f"Issues: {result['flags']}\n\n"
        f"Write an improved title tag (strict max 60 characters) and meta description "
        f"(strict max 155 characters). The title should lead with the primary keyword. "
        f"The meta should include a clear benefit and a soft CTA. "
        f"Do not pad to fill the limit — be concise."
    )

    response = client.messages.parse(
        model="claude-opus-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
        output_format=SEOSuggestion,
    )
    s = response.parsed_output
    return s.suggested_title, s.suggested_meta


FLAG_COLORS = {
    "Low CTR":     "#f59e0b",
    "Meta Issue":  "#ef4444",
    "Title Issue": "#ef4444",
    "Missing H1":  "#ef4444",
    "Thin Content":"#8b5cf6",
}


def flag_badges(flags_str):
    if flags_str == "OK":
        return '<span class="badge ok">OK</span>'
    parts = flags_str.split(" | ")
    badges = []
    for f in parts:
        color = FLAG_COLORS.get(f, "#6b7280")
        badges.append(f'<span class="badge" style="background:{color}">{f}</span>')
    return " ".join(badges)


def ctr_bar(ctr):
    pct = min(ctr * 10, 100)  # scale: 10% CTR = full bar
    color = "#22c55e" if ctr >= 1.0 else "#f59e0b" if ctr >= 0.5 else "#ef4444"
    return (
        f'<div class="bar-wrap"><div class="bar" style="width:{pct:.1f}%;background:{color}"></div>'
        f'<span>{ctr:.2f}%</span></div>'
    )


def position_chip(pos):
    color = "#22c55e" if pos <= 10 else "#f59e0b" if pos <= 20 else "#ef4444"
    return f'<span class="chip" style="color:{color};border-color:{color}">{pos:.1f}</span>'


def char_cell(text, length, warn, limit):
    if not text:
        return '<span style="color:#ef4444">Missing</span>'
    color = "#ef4444" if length > limit else "#22c55e"
    short = (text[:60] + "…") if len(text) > 63 else text
    return f'<span title="{text}" style="color:{color}">{short}</span> <small>({length})</small>'


def generate_html(results, flag_counts):
    total = len(results)
    ok_count = sum(1 for r in results if r.get("flags") == "OK")

    summary_cards = ""
    card_meta = [
        ("Total URLs", total, "#3b82f6"),
        ("Clean", ok_count, "#22c55e"),
        ("Low CTR", flag_counts.get("Low CTR", 0), "#f59e0b"),
        ("Meta Issues", flag_counts.get("Meta Issue", 0), "#ef4444"),
        ("Title Issues", flag_counts.get("Title Issue", 0), "#ef4444"),
        ("Thin Content", flag_counts.get("Thin Content", 0), "#8b5cf6"),
    ]
    for label, val, color in card_meta:
        summary_cards += f'''
        <div class="card">
          <div class="card-val" style="color:{color}">{val}</div>
          <div class="card-label">{label}</div>
        </div>'''

    rows = ""
    for r in results:
        slug = r["url"].replace("https://evidentscientific.com/en/", "")
        sug_title = r.get("suggested_title", "")
        sug_meta  = r.get("suggested_meta", "")

        def suggestion_cell(text):
            if not text:
                return '<span style="color:#475569">—</span>'
            color = "#ef4444" if len(text) > (60 if "title" in suggestion_cell.__name__ else 155) else "#a78bfa"
            return f'<span style="color:#a78bfa">{text}</span> <small>({len(text)})</small>'

        sug_title_html = (
            f'<span style="color:#a78bfa">{sug_title}</span> <small>({len(sug_title)})</small>'
            if sug_title else '<span style="color:#475569">—</span>'
        )
        sug_meta_html = (
            f'<span style="color:#a78bfa">{sug_meta}</span> <small>({len(sug_meta)})</small>'
            if sug_meta else '<span style="color:#475569">—</span>'
        )

        rows += f'''
        <tr>
          <td><a href="{r["url"]}" target="_blank">{slug}</a></td>
          <td class="num">{r["clicks"]:,}</td>
          <td class="num">{r["impressions"]:,}</td>
          <td>{ctr_bar(r["ctr"])}</td>
          <td>{position_chip(r["position"])}</td>
          <td>{char_cell(r.get("title",""), r.get("title_len",0), True, 60)}</td>
          <td>{sug_title_html}</td>
          <td>{char_cell(r.get("meta_description",""), r.get("meta_len",0), True, 155)}</td>
          <td>{sug_meta_html}</td>
          <td class="num">{r.get("word_count","—")}</td>
          <td class="num">{r.get("images_missing_alt","—")}</td>
          <td>{flag_badges(r.get("flags","OK"))}</td>
        </tr>'''

    from datetime import date
    run_date = date.today().strftime("%B %d, %Y")

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SEO Audit — Evident Scientific</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
         background: #0f172a; color: #e2e8f0; min-height: 100vh; padding: 2rem; }}
  h1   {{ font-size: 1.6rem; font-weight: 700; color: #f8fafc; }}
  .sub {{ color: #94a3b8; font-size: 0.85rem; margin-top: 0.25rem; }}
  header {{ margin-bottom: 2rem; }}

  /* Summary cards */
  .cards {{ display: flex; flex-wrap: wrap; gap: 1rem; margin-bottom: 2rem; }}
  .card  {{ background: #1e293b; border: 1px solid #334155; border-radius: 10px;
            padding: 1.1rem 1.4rem; min-width: 120px; }}
  .card-val   {{ font-size: 2rem; font-weight: 700; line-height: 1; }}
  .card-label {{ font-size: 0.75rem; color: #94a3b8; margin-top: 0.3rem; text-transform: uppercase; letter-spacing: .05em; }}

  /* Table */
  .table-wrap {{ overflow-x: auto; border-radius: 10px; border: 1px solid #334155; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.82rem; }}
  thead tr {{ background: #1e293b; }}
  thead th {{ padding: 0.7rem 0.9rem; text-align: left; font-weight: 600;
              color: #94a3b8; text-transform: uppercase; letter-spacing: .05em;
              white-space: nowrap; border-bottom: 1px solid #334155; }}
  tbody tr {{ border-bottom: 1px solid #1e293b; transition: background .15s; }}
  tbody tr:hover {{ background: #1e293b; }}
  tbody td {{ padding: 0.65rem 0.9rem; vertical-align: middle; }}
  td a {{ color: #60a5fa; text-decoration: none; }}
  td a:hover {{ text-decoration: underline; }}
  .num {{ text-align: right; font-variant-numeric: tabular-nums; }}

  /* CTR bar */
  .bar-wrap {{ display: flex; align-items: center; gap: 0.5rem; min-width: 110px; }}
  .bar      {{ height: 6px; border-radius: 3px; min-width: 2px; flex-shrink: 0; }}
  .bar-wrap span {{ font-size: 0.8rem; color: #cbd5e1; white-space: nowrap; }}

  /* Position chip */
  .chip {{ font-size: 0.78rem; font-weight: 600; border: 1.5px solid; border-radius: 20px;
           padding: 1px 8px; white-space: nowrap; }}

  /* Badges */
  .badge {{ display: inline-block; font-size: 0.7rem; font-weight: 600; padding: 2px 7px;
            border-radius: 20px; color: #fff; white-space: nowrap; }}
  .badge.ok {{ background: #166534; color: #bbf7d0; }}

  footer {{ margin-top: 2rem; font-size: 0.75rem; color: #475569; text-align: center; }}
</style>
</head>
<body>
<header>
  <h1>SEO Audit — Evident Scientific</h1>
  <p class="sub">GSC data: last 3 months &nbsp;·&nbsp; Audited {run_date} &nbsp;·&nbsp; {total} URLs</p>
</header>

<div class="cards">{summary_cards}
</div>

<div class="table-wrap">
<table>
  <thead>
    <tr>
      <th>URL</th>
      <th>Clicks</th>
      <th>Impressions</th>
      <th>CTR</th>
      <th>Position</th>
      <th>Current Title</th>
      <th>Suggested Title</th>
      <th>Current Meta</th>
      <th>Suggested Meta</th>
      <th>Words</th>
      <th>Imgs No Alt</th>
      <th>Flags</th>
    </tr>
  </thead>
  <tbody>{rows}
  </tbody>
</table>
</div>

<footer>Generated by seo_audit.py</footer>
</body>
</html>'''


def main():
    results = []
    for i, entry in enumerate(urls_with_gsc):
        result = audit_url(entry)
        results.append(result)
        if i < len(urls_with_gsc) - 1:
            time.sleep(1)  # polite crawl delay

    # Generate AI suggestions for flagged URLs
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("\nNote: ANTHROPIC_API_KEY not set — skipping AI suggestions.")
    else:
        ai_client = anthropic.Anthropic(api_key=api_key)
        flagged = [r for r in results if r.get("flags", "OK") != "OK" and not r.get("error")]
        print(f"\nGenerating AI suggestions for {len(flagged)} flagged URL(s)...")
        for r in flagged:
            try:
                sug_title, sug_meta = generate_suggestions(ai_client, r)
                r["suggested_title"] = sug_title
                r["suggested_meta"]  = sug_meta
                print(f"  Done: {r['url'].split('/en/')[-1]}")
            except Exception as e:
                print(f"  Error on {r['url']}: {e}")
                r["suggested_title"] = ""
                r["suggested_meta"]  = ""

    # CSV
    fieldnames = [
        "url", "clicks", "impressions", "ctr", "position",
        "title", "title_len", "suggested_title",
        "meta_description", "meta_len", "suggested_meta",
        "h1", "h2s", "word_count", "images_missing_alt",
        "canonical", "flags", "error",
    ]
    with open("seo_audit_results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    # Flag summary
    flag_counts = {}
    for r in results:
        for flag in r.get("flags", "").split(" | "):
            if flag and flag != "OK":
                flag_counts[flag] = flag_counts.get(flag, 0) + 1

    # HTML report
    html = generate_html(results, flag_counts)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("\nDone.")
    print("  seo_audit_results.csv")
    print("  index.html")

    if flag_counts:
        print("\nFlag summary:")
        for flag, count in sorted(flag_counts.items(), key=lambda x: -x[1]):
            print(f"  {flag}: {count} URL(s)")


if __name__ == "__main__":
    main()
