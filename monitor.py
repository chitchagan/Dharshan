import json
import os
import smtplib
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html import escape
from email.message import EmailMessage

URL = "https://online.sai.org.in/eDarshan/darshanAvailability/2026-12-25/100002"
TO = "dpjegankumar@gmail.com"

def display(value):
    if value is None:
        return "Not provided"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)

def make_html(status, payload, raw, timestamp):
    slots = payload.get("darshanSlots", []) if isinstance(payload, dict) else []
    if not isinstance(slots, list):
        slots = []

    rows = []
    for slot in slots:
        if not isinstance(slot, dict):
            continue
        name = str(slot.get("slotName") or "Aarti")
        # Remove repeated times from the slot name; times have their own column.
        import re
        name = re.sub(r"\\s*\\d{1,2}:\\d{2}\\s*[–—-]\\s*\\d{1,2}:\\d{2}\\s*$", "", name).strip()
        begin = str(slot.get("slotBeginTime") or "")
        finish = str(slot.get("slotEndTime") or "")
        timing = f"{begin} – {finish}" if begin and finish else "Not provided"
        available = display(slot.get("noOfTicketsAvailable"))
        rows.append(
            "<tr>"
            f'<td style="padding:12px;border-bottom:1px solid #e5e7eb">{escape(name)}</td>'
            f'<td style="padding:12px;border-bottom:1px solid #e5e7eb;white-space:nowrap">{escape(timing)}</td>'
            f'<td style="padding:12px;border-bottom:1px solid #e5e7eb;text-align:center;font-weight:bold">{escape(available)}</td>'
            "</tr>"
        )
    if not rows:
        rows.append('<tr><td colspan="3" style="padding:12px">No slots returned.</td></tr>')

    return f"""<html><body style="font-family:Arial,sans-serif;color:#1f2937">
      <h2 style="margin-bottom:4px">Sai Darshan Availability</h2>
      <p style="color:#6b7280;margin-top:0">25 December 2026 · Checked {escape(timestamp)} UTC</p>
      <table style="border-collapse:collapse;width:100%;max-width:650px;font-size:14px">
        <thead><tr style="background:#f3f4f6">
          <th style="padding:12px;text-align:left">Aarti</th>
          <th style="padding:12px;text-align:left">Timing</th>
          <th style="padding:12px;text-align:center">Available Slots</th>
        </tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </body></html>"""

def make_text(payload, timestamp):
    slots = payload.get("darshanSlots", []) if isinstance(payload, dict) else []
    lines = [f"Sai Darshan Availability - 25 December 2026", f"Checked (UTC): {timestamp}", ""]
    for slot in slots if isinstance(slots, list) else []:
        if isinstance(slot, dict):
            lines.append(f"{slot.get('slotName', 'Aarti')} | {slot.get('slotBeginTime', '')}-{slot.get('slotEndTime', '')} | Available: {display(slot.get('noOfTicketsAvailable'))}")
    if len(lines) == 3:
        lines.append("No slots returned.")
    return "\\n".join(lines)

def main():
    req = urllib.request.Request(
        URL,
        data=b"{}",
        headers={"Content-Type": "application/json", "Accept": "application/json", "User-Agent": "Mozilla/5.0"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=40) as resp:
            status = resp.status
            body = resp.read(250000).decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        status = exc.code
        body = exc.read(250000).decode("utf-8", errors="replace")
    except Exception as exc:
        status = "NETWORK ERROR"
        body = str(exc)

    try:
        payload = json.loads(body)
        pretty = json.dumps(payload, indent=2, ensure_ascii=False)
    except (ValueError, TypeError):
        payload = None
        pretty = body

    timestamp = datetime.now(timezone.utc).isoformat()
    report = f"Checked (UTC): {timestamp}\nEndpoint: {URL}\nHTTP status: {status}\n\nResponse:\n{pretty}\n"
    print(report)

    app_password = os.environ.get("GOOGLE_APP_PASSWORD")
    sender = "stanskillacademy@gmail.com"
    if not app_password:
        print("GOOGLE_APP_PASSWORD GitHub secret is missing.", file=sys.stderr)
        sys.exit(2)

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = TO
    msg["Subject"] = f"Sai Darshan Availability - 25 Dec 2026 - {status}"
    msg.set_content(make_text(payload, timestamp))
    msg.add_alternative(make_html(status, payload, body, timestamp), subtype="html")
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
            smtp.login(sender, app_password)
            smtp.send_message(msg)
        print("Gmail SMTP accepted the formatted email.")
    except Exception as exc:
        print(f"Gmail delivery failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
