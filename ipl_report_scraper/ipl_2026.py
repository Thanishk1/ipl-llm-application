import requests
import json
import time
from bs4 import BeautifulSoup

def get_next_data(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    script = soup.find("script", {"id": "__NEXT_DATA__"})
    return json.loads(script.string)

def extract_report_text(items):
    paragraphs = []
    for item in items:
        if item.get('type') == 'HTML':
            clean_text = BeautifulSoup(item['html'], 'html.parser').get_text()
            paragraphs.append(clean_text)
    return "\n\n".join(paragraphs)

def scrape_match_report(base_url):
    report_url = base_url + "/match-report"
    data = get_next_data(report_url)
    story = data['props']['appPageProps']['data']['content']['storyDetails']['story']
    items = data['props']['appPageProps']['data']['content']['storyDetails']['content']['items']
    return {
        "match_id": story['matchMeta']['objectId'],
        "title": story['title'],
        "byline": story['byline'],
        "date": story['publishedAt'],
        "report_text": extract_report_text(items)
    }

def get_all_match_base_urls(schedule_url, series_slug):
    data = get_next_data(schedule_url)
    matches = data['props']['appPageProps']['data']['content']['matches']
    base_urls = []
    for m in matches:
        if m.get('status') != 'RESULT':
            continue  # skip abandoned/no-result matches
        slug = m['slug']
        object_id = m['objectId']
        base_url = f"https://www.espncricinfo.com/series/{series_slug}/{slug}-{object_id}"
        base_urls.append(base_url)
    return base_urls

# ---- MAIN ----
schedule_url_2026 = "https://www.espncricinfo.com/series/ipl-2026-1510719/match-schedule-fixtures-and-results"
base_urls_2026 = get_all_match_base_urls(schedule_url_2026, "ipl-2026-1510719")

print(f"Found {len(base_urls_2026)} completed matches for IPL 2026")

all_reports = []
for i, url in enumerate(base_urls_2026):
    try:
        report = scrape_match_report(url)
        all_reports.append(report)
        print(f"[{i+1}/{len(base_urls_2026)}] Scraped: {report['title']}")
    except Exception as e:
        print(f"[{i+1}/{len(base_urls_2026)}] FAILED: {url} — {e}")
    time.sleep(1.5)  # be polite, avoid hammering the server

# Save incrementally
with open("ipl_2026_reports.json", "w", encoding="utf-8") as f:
    json.dump(all_reports, f, indent=2, ensure_ascii=False)

print(f"\nDone. Saved {len(all_reports)} reports.")