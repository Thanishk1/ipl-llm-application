import json

with open("ipl_2025_reports.json", "r", encoding="utf-8") as f:
    reports_2025 = json.load(f)

with open("ipl_2026_reports.json", "r", encoding="utf-8") as f:
    reports_2026 = json.load(f)

all_reports = reports_2025 + reports_2026
print("Total reports combined:", len(all_reports))

with open("ipl_all_reports.json", "w", encoding="utf-8") as f:
    json.dump(all_reports, f, indent=2, ensure_ascii=False)