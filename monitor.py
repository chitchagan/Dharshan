import json
import os
import smtplib
import sys
import urllib.error
import urllib.request
from email.message import EmailMessage
from datetime import datetime, timezone

URL = "https://online.sai.org.in/eDarshan/darshanAvailability/2026-12-25/100002"
TO = "dpjegankumar@gmail.com"

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
        pretty = json.dumps(json.loads(body), indent=2, ensure_ascii=False)
    except (ValueError, TypeError):
        pretty = body

    now = datetime.now(timezone.utc).isoformat()
    report = f"Checked (UTC): {now}\nEndpoint: {URL}\nHTTP status: {status}\n\nResponse:\n{pretty}\n"
    print(report)

    sender = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASSWORD")
    if not sender or not password:
        print("SMTP_USER and SMTP_PASSWORD secrets are missing; email was NOT sent.", file=sys.stderr)
        sys.exit(2)

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = TO
    msg["Subject"] = f"Sai Darshan API check - {status} - 25 Dec 2026"
    msg.set_content(report)
    host = (os.environ.get("SMTP_HOST") or "smtp.gmail.com")
    port = int((os.environ.get("SMTP_PORT") or "465"))
    with smtplib.SMTP_SSL(host, port, timeout=30) as smtp:
        smtp.login(sender, password)
        smtp.send_message(msg)
    print("Email sent successfully.")

if __name__ == "__main__":
    main()
