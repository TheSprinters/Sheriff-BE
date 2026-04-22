"""Gmail SMTP email service — RSVP confirmations with calendar attachment."""
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from urllib.parse import quote
import os


# ── iCalendar (.ics) builder ─────────────────────────────────────────────────

def _ics(event) -> str:
    """Generate iCalendar (.ics) text for the event (2-hour duration assumed)."""
    date_str = event._date.strftime('%Y%m%d')
    h, m = map(int, (event._time + ':00').split(':')[:2])
    end_h = (h + 2) % 24

    start  = f"{date_str}T{h:02d}{m:02d}00"
    end    = f"{date_str}T{end_h:02d}{m:02d}00"
    stamp  = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    title  = (event._title or '').replace(',', '\\,').replace('\n', '\\n')
    desc   = (event._description or '').replace(',', '\\,').replace('\n', '\\n')
    loc    = (event._location or '').replace(',', '\\,')

    return (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//DSA San Diego//Events//EN\r\n"
        "CALSCALE:GREGORIAN\r\n"
        "METHOD:PUBLISH\r\n"
        "BEGIN:VEVENT\r\n"
        f"UID:dsa-event-{event.id}@dsasd.org\r\n"
        f"DTSTAMP:{stamp}\r\n"
        f"DTSTART:{start}\r\n"
        f"DTEND:{end}\r\n"
        f"SUMMARY:{title}\r\n"
        f"DESCRIPTION:{desc}\r\n"
        f"LOCATION:{loc}\r\n"
        "STATUS:CONFIRMED\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )


# ── Google Calendar URL builder ───────────────────────────────────────────────

def _gcal_url(event) -> str:
    """Return a 'Add to Google Calendar' URL for the event."""
    date_str = event._date.strftime('%Y%m%d')
    h, m = map(int, (event._time + ':00').split(':')[:2])
    end_h = (h + 2) % 24

    start = f"{date_str}T{h:02d}{m:02d}00"
    end   = f"{date_str}T{end_h:02d}{m:02d}00"

    return (
        "https://calendar.google.com/calendar/render?action=TEMPLATE"
        f"&text={quote(event._title or '')}"
        f"&dates={start}/{end}"
        f"&details={quote(event._description or '')}"
        f"&location={quote(event._location or '')}"
    )


# ── HTML email body ───────────────────────────────────────────────────────────

def _html_body(first_name: str, event, gcal: str) -> str:
    date_fmt = event._date.strftime('%A, %B %d, %Y')
    desc_row = (
        f'<tr><td colspan="2" style="padding:12px 0 0;">'
        f'<span style="color:#94a3b8;font-size:0.85rem;">{event._description}</span></td></tr>'
        if event._description else ''
    )
    return f"""
<!DOCTYPE html>
<html>
<body style="margin:0;padding:20px;background:#0b1a2e;font-family:Arial,sans-serif;">
<div style="max-width:600px;margin:0 auto;background:#0f1c2e;border-radius:14px;overflow:hidden;border:1px solid #1e3352;">

  <!-- Header -->
  <div style="background:#1e3a5f;padding:28px 28px 20px;text-align:center;border-bottom:3px solid #fbbf24;">
    <h1 style="color:#fbbf24;margin:0;font-size:1.5rem;font-weight:800;">&#9733; You&rsquo;re Going!</h1>
    <p style="color:#94a3b8;margin:6px 0 0;font-size:0.82rem;">Deputy Sheriffs&rsquo; Association of San Diego County</p>
  </div>

  <!-- Body -->
  <div style="padding:28px;">
    <p style="color:#94a3b8;margin:0 0 20px;">Hi {first_name},</p>
    <p style="color:#cbd5e1;margin:0 0 24px;line-height:1.6;">
      Your RSVP has been confirmed. We look forward to seeing you there!
    </p>

    <!-- Event details card -->
    <div style="background:#162a46;border:1px solid #1e3352;border-radius:10px;padding:20px;margin-bottom:24px;">
      <h2 style="color:#fbbf24;margin:0 0 16px;font-size:1.15rem;">{event._title}</h2>
      <table style="width:100%;border-collapse:collapse;">
        <tr>
          <td style="color:#64748b;padding:5px 0;width:90px;vertical-align:top;">&#128197;&nbsp;Date</td>
          <td style="color:#e2e8f0;padding:5px 0;">{date_fmt}</td>
        </tr>
        <tr>
          <td style="color:#64748b;padding:5px 0;vertical-align:top;">&#128336;&nbsp;Time</td>
          <td style="color:#e2e8f0;padding:5px 0;">{event._time}</td>
        </tr>
        <tr>
          <td style="color:#64748b;padding:5px 0;vertical-align:top;">&#128205;&nbsp;Location</td>
          <td style="color:#e2e8f0;padding:5px 0;">{event._location}</td>
        </tr>
        {desc_row}
      </table>
    </div>

    <!-- Calendar buttons -->
    <p style="color:#64748b;font-size:0.82rem;margin:0 0 14px;">Add this event to your calendar:</p>
    <table>
      <tr>
        <td style="padding-right:12px;">
          <a href="{gcal}" target="_blank"
             style="display:inline-block;padding:10px 20px;background:#4285f4;color:#fff;
                    border-radius:8px;text-decoration:none;font-weight:700;font-size:0.82rem;">
            &#43;&nbsp;Google Calendar
          </a>
        </td>
        <td>
          <span style="display:inline-block;padding:10px 16px;background:rgba(255,255,255,0.04);
                       color:#94a3b8;border-radius:8px;font-size:0.78rem;
                       border:1px solid rgba(255,255,255,0.08);">
            &#128193;&nbsp;Apple / Outlook: open the attached <em>event.ics</em> file
          </span>
        </td>
      </tr>
    </table>
  </div>

  <!-- Footer -->
  <div style="padding:14px 28px;background:#0b1a2e;border-top:1px solid #1e3352;text-align:center;">
    <p style="color:#334155;font-size:0.72rem;margin:0;">
      Deputy Sheriffs&rsquo; Association &bull; San Diego County &bull; dsasd.org
    </p>
  </div>

</div>
</body>
</html>
"""


# ── Public send function ─────────────────────────────────────────────────────

def send_rsvp_confirmation(to_email: str, to_name: str, event) -> bool:
    """
    Send an RSVP confirmation email.

    Returns True on success, False if email is not configured or sending fails.
    Requires env vars: MAIL_USERNAME, MAIL_PASSWORD, and optionally
    MAIL_SERVER (default smtp.gmail.com) and MAIL_PORT (default 587).
    """
    mail_user   = os.environ.get('MAIL_USERNAME', '').strip()
    mail_pass   = os.environ.get('MAIL_PASSWORD', '').strip()
    mail_server = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    mail_port   = int(os.environ.get('MAIL_PORT', 587))

    if not mail_user or not mail_pass:
        print('[email_service] Email not configured — skipping confirmation.')
        return False

    first_name = (to_name or 'Officer').split()[0]
    gcal       = _gcal_url(event)
    date_fmt   = event._date.strftime('%A, %B %d, %Y')

    msg = MIMEMultipart('mixed')
    msg['Subject'] = f"RSVP Confirmed: {event._title} — {date_fmt}"
    msg['From']    = f"DSA San Diego <{mail_user}>"
    msg['To']      = to_email

    msg.attach(MIMEText(_html_body(first_name, event, gcal), 'html'))

    # Attach .ics calendar file
    ics_bytes = _ics(event).encode('utf-8')
    ics_part  = MIMEBase('text', 'calendar', method='PUBLISH', name='event.ics')
    ics_part.set_payload(ics_bytes)
    encoders.encode_base64(ics_part)
    ics_part.add_header('Content-Disposition', 'attachment', filename='event.ics')
    msg.attach(ics_part)

    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP(mail_server, mail_port) as srv:
            srv.ehlo()
            srv.starttls(context=ctx)
            srv.login(mail_user, mail_pass)
            srv.sendmail(mail_user, to_email, msg.as_string())
        print(f'[email_service] Sent confirmation to {to_email}')
        return True
    except Exception as exc:
        print(f'[email_service] Failed to send to {to_email}: {exc}')
        return False
