# Selenium Attendance Filler (Darabala)

Automates bulk attendance filling for after‑school / training centers on **darabala.kz**. The bot logs in once, opens each child record, and sets the required days with a single command. Built for reliability (stable clicks, waits, retries) and safe configuration via **.env**.

> **Who is this for?** Owners/managers of education centers who waste hours clicking the same dropdowns. This script turns a monthly chore into a 1–2 minute run.

---

## Demo

* **Loom (30s):** [*Loom video*](https://www.loom.com/share/e039c9e109bc46d59000171f44aa460b)
* ![GIF preview](docs/demo_selenium.gif)

---

## Quick start (3 steps)

1. **Clone & install**

   ```bash
   git clone https://github.com/sagintai/selenium-attendance-filler.git
   cd selenium-attendance-filler
   python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. **Configure credentials**
   Create `.env` in the project root:

   ```dotenv
   DARABALA_LOGIN=000000000000
   DARABALA_PASSWORD=changeme
   ```
3. **Run**

   ```bash
   # single page
   python run.py --url https://darabala.kz/Attendances/AttendancesView/18001 --dates 3,7,10,14,17,21,24,28

   # multiple pages (repeat --url)
   python run.py \
     --url https://darabala.kz/Attendances/AttendancesView/18018 \
     --url https://darabala.kz/Attendances/AttendancesView/18019 \
     --dates 2,4,7,9,11,14,16,18,21,23,25,28
   ```

> **Note**: The browser stays open between runs; you can call the filler multiple times in one session.

---

## What it does under the hood

* Logs in once with the supplier role.
* Opens the attendance page and finds each child row.
* For each target day (e.g., `3, 7, 10, …`), sets value **"З"** in the dropdown.
* Uses **robust clicking**: scrolls into view and JS‑clicks if elements are covered (solves *ElementClickIntercepted* / *NotInteractable*).
* Dismisses alerts and ensures the off‑canvas editor is fully closed before continuing.

---

## Two ways to use

### 1) CLI (recommended for operations)

```bash
python run.py --url <attendance_url> --dates 1,3,5-10,28
```

* `--url` can be passed multiple times.
* `--dates` accepts ranges like `5-10`.

### 2) Python API (for scripts or notebooks)

```python
from darabala_auto import filler

link = "https://darabala.kz/Attendances/AttendancesView/18024"
dates = [3, 7, 10, 14, 17, 21, 24, 28]
filler(link, dates)

links = [
    "https://darabala.kz/Attendances/AttendancesView/18018",
    "https://darabala.kz/Attendances/AttendancesView/18019",
]
for url in links:
    filler(url, dates)
```

---

## Requirements

* macOS/Windows/Linux with Google Chrome installed.
* Python 3.10+.
* Packages: `selenium`, `webdriver-manager`, `python-dotenv` (see `requirements.txt`).

---

## Configuration & security

* Credentials are loaded from **.env** (never hard‑code passwords).
* Keep `.env` out of version control (`.gitignore` provided).
* Use only with accounts you own or have explicit permission to automate.

---

## Troubleshooting

* **Chrome/Driver mismatch** → `webdriver-manager` downloads a matching driver automatically. Restart if Chrome updated during a session.
* **Site changed layout/IDs** → open an issue with a screenshot; selectors are isolated and easy to adjust.
* **ElementClickIntercepted / NotInteractable** → the script already performs scroll + JS‑click; if you still see it, try slowing down the machine or closing overlapping windows.
* **Alerts keep appearing** → built‑in alert handler accepts them; if your org has custom alerts, tell me the text and I’ll extend the matcher.

---

## Why this implementation is reliable

* Explicit waits for presence/visibility.
* Centralized safe‑click helper (normal click → fallback JS‑click with pre‑scroll).
* Off‑canvas close detection with refresh fallback.
* Keeps state across calls (single driver per session).

---

## Engage me to adapt this to your portal

Most internal admin panels are similar. I ship fast, with clear acceptance criteria and Loom updates.

**Packages**

* **Basic — \$149**: adapt to one attendance form + README + 1 Loom.
* **Standard — \$299**: multiple pages in one run + CLI with date ranges + .env + short user guide.
* **Premium — \$499**: two forms/flows + success log/CSV + dry‑run mode + Dockerized runner.

**Acceptance Criteria (sample)**

1. Processes N child records without manual clicks.
2. Target days are set to "З"; non‑target days left unchanged.
3. Errors are visible in console logs; run returns without crashes.
4. Config via `.env` and CLI is documented on one screen.

---

## Legal

This tool is for **authorized automation only**. You are responsible for complying with your platform’s Terms of Service and your local laws.

---

## License

MIT — use freely, attribute appreciated.
