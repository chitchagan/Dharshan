# API Availability Monitor — Complete GitHub Actions + Gmail Blueprint

A practical, no-paid-server automation that checks an **authorized, read-only availability API** on a schedule and emails a clean HTML report.

> **What this repository actually does:** `monitor.py` sends a POST request with JSON body `{}`, parses the `darshanSlots` array, and emails a three-column table (**Aarti | Timing | Available Slots**) using Gmail SMTP. `.github/workflows/hourly-darshan.yml` runs it hourly. This repository is an example of the technique, **not a security finding or permission to scrape a third-party service**. The script currently contains example-specific hardcoded values: update them before reuse.

## 1. Architecture

```text
GitHub Actions (hourly / manual run)
           |
           v
     Python monitor.py
           |
           v
POST to authorized availability API
  Content-Type: application/json
  Body: {}
           |
           v
JSON response: darshanSlots[]
           |
           v
HTML email: Aarti | Timing | Available Slots
           |
           v
Gmail SMTP (smtp.gmail.com:465)
           |
           v
Your email inbox
```

**Requirements:** a GitHub account; a Gmail account that supports App Passwords; Python 3 (provided by the GitHub-hosted Ubuntu runner); and an API you are permitted to query. The script uses only Python's standard library, so no `pip install` or `requirements.txt` is required.

## 2. Copy the project

1. Open this repository and choose **Fork** (or create a new repository and copy `monitor.py` and `.github/workflows/hourly-darshan.yml`).
2. Open `monitor.py` and review these variables near the top:
   - `URL`: replace the example endpoint with **your own permitted API URL**.
   - `TO`: replace the example recipient with your email.
3. In `main()`, replace `sender = "stanskillacademy@gmail.com"` with **your own Gmail sender address**.
4. In `make_html()`, `make_text()`, and the email subject, replace the example date/title with your own description. These labels are hardcoded in this particular example.
5. Commit your changes. **Do not commit a Gmail password or App Password.**

The included script assumes the API accepts **POST** with an empty JSON object, and responds with a JSON object containing `darshanSlots`. For a different API, adjust the request body, headers, response keys, and table columns accordingly. Do not assume any endpoint works without authorization just because it returns public data.

## 3. Understand the POST request

The key part of `monitor.py` is:

```python
req = urllib.request.Request(
    URL,
    data=b"{}",
    headers={
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0",
    },
    method="POST",
)
with urllib.request.urlopen(req, timeout=40) as response:
    payload = json.loads(response.read().decode("utf-8"))
```

For the example response, the script reads:

| JSON field | Meaning |
| --- | --- |
| `darshanSlots` | List of returned availability slots |
| `slotName` | Aarti name |
| `slotBeginTime` | Start time |
| `slotEndTime` | End time |
| `noOfTicketsAvailable` | Available ticket count |

These names are **specific to the example**. A different API will have different fields.

## 4. Generate a Google App Password

Gmail SMTP authentication here uses a **Google App Password**, not your regular Google password.

1. Sign in to the Gmail account you want to send email from.
2. Open **Google Account → Security**: https://myaccount.google.com/security
3. Enable **2-Step Verification** if it is not already enabled.
4. Open **App Passwords**: https://myaccount.google.com/apppasswords
5. Create an App Password (for example, name it `GitHub Availability Monitor`).
6. Copy the generated password **privately**. You may need to remove spaces when pasting it as a secret.

**If App Passwords is unavailable:** your account may be managed by an organization, use certain advanced protections, or otherwise be ineligible. Use a supported mail provider or a properly configured OAuth/mail service instead. Never disable security controls to make this work.

**Important:** Do not paste the App Password into Python code, README files, screenshots, commits, comments, or DMs. Revoke it from your Google Account if you suspect exposure.

## 5. Add the password as a GitHub Actions secret

Inside **your fork/repository**:

1. Open **Settings**.
2. Go to **Secrets and variables → Actions**.
3. Select **New repository secret**.
4. Name it **exactly** `GOOGLE_APP_PASSWORD`.
5. Paste the Google App Password into the **Secret** value.
6. Save.

The workflow passes this secret to Python at runtime:

```yaml
env:
  GOOGLE_APP_PASSWORD: ${{ secrets.GOOGLE_APP_PASSWORD }}
```

Python reads it with:

```python
app_password = os.environ.get("GOOGLE_APP_PASSWORD")
```

A secret is available to the workflow but is **not stored in the repository's source files**.

## 6. How Gmail sending works

The script creates both a plain-text message and an HTML table, then sends them over encrypted SMTP:

```python
import smtplib
from email.message import EmailMessage

msg = EmailMessage()
msg["From"] = sender
msg["To"] = TO
msg["Subject"] = "Availability update"
msg.set_content("See the availability report.")
msg.add_alternative("<h2>Availability</h2><p>See the latest slots.</p>", subtype="html")

with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
    smtp.login(sender, app_password)
    smtp.send_message(msg)
```

The actual `monitor.py` builds the HTML table dynamically from the API response.

## 7. Schedule with GitHub Actions

Workflow file: **`.github/workflows/hourly-darshan.yml`**

```yaml
name: Hourly Sai Darshan API check

on:
  schedule:
    - cron: "0 * * * *"
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: hourly-sai-darshan
  cancel-in-progress: false

jobs:
  check:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4
      - name: Call POST endpoint and send formatted email via Gmail
        env:
          GOOGLE_APP_PASSWORD: ${{ secrets.GOOGLE_APP_PASSWORD }}
        run: python monitor.py
```

**Schedule:** `0 * * * *` means once per hour at minute 00 **UTC** (approximately minute 30 in India Standard Time). GitHub scheduled jobs can be delayed or occasionally skipped; they are not a precision timer. The `workflow_dispatch` entry enables a manual test button.

For a less frequent schedule, change the cron expression, for example `0 */3 * * *` for every three hours. Respect the API provider's policies and traffic limits.

## 8. Run a test

1. Push your edits to the repository's default branch.
2. Open the **Actions** tab and enable workflows if GitHub prompts you.
3. Choose **Hourly Sai Darshan API check** from the workflow list.
4. Click **Run workflow**.
5. Open the new run, then the **check** job.
6. Look for **Gmail SMTP accepted the formatted email.**
7. Check the recipient's Inbox and Spam/Junk folders.

The email should show the three-column report when the example API returns valid slots. A successful SMTP handoff does not guarantee inbox placement.

**Privacy note:** The current script prints the full API response and URL to the GitHub Actions log. If you adapt it to a private or sensitive API, **remove that logging** before running it. Avoid logging personal data, tokens, or credentials.

## 9. Common problems and fixes

| Symptom | Likely cause / action |
| --- | --- |
| `GOOGLE_APP_PASSWORD GitHub secret is missing` | Secret name must be exactly `GOOGLE_APP_PASSWORD`; add it in the same repository where Actions runs |
| Gmail `SMTPAuthenticationError` / login rejected | Verify sender account, 2-Step Verification, and App Password; do not use the normal account password |
| Email not received | Check spam, sender/recipient addresses, workflow logs, and Gmail sending limits |
| HTTP 401 / 403 | The API requires authorization or blocks access; use an API you are authorized to access |
| HTTP 429 | Too many requests; reduce frequency and respect the service's limits; do not bypass protections |
| HTTP 404 | Check the URL and resource identifiers |
| HTTP 500 / timeout | Service unavailable or network issue; retry conservatively, not in a tight loop |
| `No slots returned` | API response shape differs, or no data is available; inspect a safe redacted response |
| No scheduled run | Check Actions settings, default-branch workflow, and GitHub scheduling delays |
| HTML table looks wrong | Check the `darshanSlots` structure and map the correct field names |

## 10. Security and responsible use

- Public availability information **does not automatically require login**. An unauthenticated read-only endpoint is not, by itself, proof of a vulnerability.
- Appropriate protections may include **rate limiting, caching, monitoring**, and **strong authentication/authorization for booking, payment, and personal-data operations**. This project does **not** establish whether any particular third-party website has those protections.
- Only automate endpoints you are authorized to access, and keep request volume low. Do not stress-test a live service without permission.
- Keep `GOOGLE_APP_PASSWORD` in GitHub Secrets, not in source control.
- Use a dedicated sender account if possible and rotate/revoke credentials if exposed.
- Do not commit private responses, personal data, payment information, or authentication tokens.
- Treat emailed availability as informational; it is **not a reservation or booking confirmation**.

## 11. Project files

| File | Purpose |
| --- | --- |
| [`monitor.py`](monitor.py) | POST request, JSON parsing, HTML table, Gmail SMTP delivery |
| [`.github/workflows/hourly-darshan.yml`](.github/workflows/hourly-darshan.yml) | Hourly schedule, manual trigger, secret injection |

## 12. Quick-start checklist

- [ ] Fork repository
- [ ] Set your authorized API URL and request/response mapping
- [ ] Change sender and recipient addresses
- [ ] Update example-specific report labels
- [ ] Enable Google 2-Step Verification
- [ ] Generate Google App Password
- [ ] Save `GOOGLE_APP_PASSWORD` in GitHub Actions secrets
- [ ] Run workflow manually
- [ ] Verify email
- [ ] Keep scheduled checks within the API provider's permitted limits

**Result:** a lightweight, no-paid-server scheduled API-to-email workflow that readers can adapt to their own permitted data sources.
