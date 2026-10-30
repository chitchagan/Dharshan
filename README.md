# Sai Darshan availability monitor

Runs hourly through GitHub Actions, sends POST to `https://online.sai.org.in/eDarshan/darshanAvailability/2026-12-25/100002`, and emails an HTML table with **all** returned slots and extra API fields to `dpjegankumar@gmail.com`. The full JSON response is included below the table.

## One-time Resend setup

1. Sign up at https://resend.com and create a sending API key.
2. Verify a sending domain in Resend, or use Resend's test sender only when the recipient is your Resend account email (testing restrictions apply).
3. Add these repository secrets at **Settings → Secrets and variables → Actions**:
   - `RESEND_API_KEY` — your private Resend API key
   - `RESEND_FROM_EMAIL` — sender address authorized by Resend (for example `Alerts <alerts@your-verified-domain.com>`)
4. Open **Actions → Hourly Sai Darshan API check → Run workflow** to test.

**Never put an API key in code, an issue, or a chat message.**

Notes: Emails on **every** run, not only when values change. GitHub cron can run late or skip runs. An API slot listing is not necessarily proof of available tickets. The POST body is `{}`, and may need changing if the site expects something else. The first live execution and email delivery remain unverified.
