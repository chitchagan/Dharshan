import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html import escape

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
    columns = [
        ("slotName", "Darshan / Aarti"),
        ("darshanDate", "Date"),
        ("slotBeginTime", "Start"),
        ("slotEndTime", "End"),
        ("darshanPrice", "Price (₹)"),
    ]
    # Include all extra API fields (including any availability indicators) without assuming their meaning.
    extras = sorted({k for s in slots if isinstance(s, dict) for k in s if k not in {c[0] for c in columns}})
    columns.extend((key, key) for key in extras)
    head = "".join(f'<th style="padding:10px;border:1px solid #ddd;background:#edf2f7;text-align:left">{escape(label)}</th>' for _, label in columns)
    rows = []
    for slot in slots:
        if not isinstance(slot, dict):
            continue
        cells = "".join(f'<td style="padding:10px;border:1px solid #ddd">{escape(display(slot.get(key)))}</td>' for key, _ in columns)
        rows.append(f"<tr>{cells}</tr>")
    if not rows:
        rows.append(f'<tr><td colspan="{len(columns)}" style="padding:12px">No darshan slot rows returned.</td></tr>')
    table = f'<table style="border-collapse:collapse;width:100%;font-family:Arial,sans-serif;font-size:13px"><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table>'
    response = escape(json.dumps(payload, indent=2, ensure_ascii=False) if payload is not None else raw)
    return f"""<html><body style="font-family:Arial,sans-serif;color:#202a36">
    <h2>Sai Baba Darshan Availability Report</h2>
    <p><b>Darshan date:</b> 25 December 2026<br><b>Checked (UTC):</b> {escape(timestamp)}<br><b>HTTP status:</b> {escape(str(status))}<br><b>Slots returned:</b> {len(slots)}</p>
    {table}
    <p style="font-size:12px;color:#555">Slot listing does not by itself confirm bookable tickets. Availability fields are shown exactly as returned by the API.</p>
    <h3>Complete API response</h3><pre style="white-space:pre-wrap;overflow-wrap:anywhere;background:#f5f5f5;padding:12px">{response}</pre>
    </body></html>"""

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

    api_key = os.environ.get("RESEND_API_KEY")
    sender = os.environ.get("RESEND_FROM_EMAIL")
    if not api_key or not sender:
        print("RESEND_API_KEY and RESEND_FROM_EMAIL must be configured as GitHub secrets.", file=sys.stderr)
        sys.exit(2)

    email_data = {
        "from": sender,
        "to": [TO],
        "subject": f"Sai Darshan Availability - 25 Dec 2026 - {status}",
        "html": make_html(status, payload, body, timestamp),
        "text": report,
    }
    request = urllib.request.Request(
        "https://api.resend.com/emails",
        data=json.dumps(email_data).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            print(f"Resend accepted email: HTTP {response.status}")
    except urllib.error.HTTPError as exc:
        error_body = exc.read(2000).decode("utf-8", errors="replace")
        print(f"Resend rejected email: HTTP {exc.code} - {error_body}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
