# Sai Darshan availability API monitor

GitHub Actions calls the configured API with an HTTP POST request once per hour (UTC schedule) and sends the full response to dpjegankumar@gmail.com.

## Setup required

In **Settings → Secrets and variables → Actions**, add repository secrets:
- `SMTP_USER`: your sending Gmail address
- `SMTP_PASSWORD`: a Gmail app password (not your normal Gmail password)

Optional repository variables: `SMTP_HOST` (defaults to smtp.gmail.com) and `SMTP_PORT` (defaults to 465). Leave both unset to use the defaults.

In **Actions → Hourly Sai Darshan API check → Run workflow**, test it. No email can be sent until SMTP credentials are configured.

## Notes

- Sends an email on **every hourly check**, including API errors. It does not yet compare responses across runs.
- GitHub scheduled jobs may be delayed or occasionally skipped; not a guaranteed exact-time service.
- API body is currently `{}` with Content-Type application/json; adjust if the endpoint requires another body or browser session.
- This is a monitoring aid, not a booking confirmation.
- Do not commit credentials to the repository.
