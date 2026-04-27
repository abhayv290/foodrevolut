from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from apps.users.emails import send_html_email, wrap_email_html
from django.utils import timezone



@shared_task(bind=True, max_retries=3)
def notify_new_login(self, user_id, ip_address=None, user_agent=None):
    """
    Fires after every successful login.
    Security alert — lets user know if someone else logged into their account.
 
    ── Why include IP and device info? ──────────────────────────────────────
    If the user didn't log in — they can immediately know something is wrong.
    Same pattern used by Google, GitHub, every serious platform.
    """
    try:
        User = get_user_model()
        user = User.objects.get(pk=user_id)
        user_name = getattr(user, "name", user.email)
 
        login_time = timezone.now().strftime("%d %b %Y at %I:%M %p")
        ip         = ip_address or "Unknown"
        device     = user_agent or "Unknown device"
 
        # truncate long user agent strings — browser strings can be 200+ chars
        if len(device) > 80:
            device = device[:80] + "..."
 
        frontend_url  = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
        support_email = settings.DEFAULT_FROM_EMAIL
 
        content = f"""
            <p style="margin:0 0 16px;font-size:16px;color:#1a1a1a;font-weight:500;">
                Hi {user_name},
            </p>
            <p style="margin:0 0 24px;font-size:15px;color:#4a4a4a;">
                We noticed a new login to your FoodDelivery account.
            </p>
 
            <table width="100%" cellpadding="0" cellspacing="0"
                   style="background:#f9f9f9;border-radius:6px;padding:16px;margin:0 0 24px;">
                <tr>
                    <td style="font-size:14px;color:#6b6b6b;padding:6px 0;">Time</td>
                    <td style="font-size:14px;color:#1a1a1a;text-align:right;">{login_time} (IST)</td>
                </tr>
                <tr>
                    <td style="font-size:14px;color:#6b6b6b;padding:6px 0;">IP address</td>
                    <td style="font-size:14px;color:#1a1a1a;text-align:right;">{ip}</td>
                </tr>
                <tr>
                    <td style="font-size:14px;color:#6b6b6b;padding:6px 0;">Device</td>
                    <td style="font-size:14px;color:#1a1a1a;text-align:right;">{device}</td>
                </tr>
            </table>
 
            <p style="margin:0 0 16px;font-size:15px;color:#4a4a4a;">
                If this was you, no action is needed.
            </p>
            <p style="margin:0 0 24px;font-size:15px;color:#4a4a4a;">
                If you did not log in, your account may be compromised.
                Please change your password immediately.
            </p>
 
            <table cellpadding="0" cellspacing="0">
                <tr>
                    <td style="background-color:#e85d30;border-radius:6px;">
                        <a href="{frontend_url}/settings/change-password"
                           style="display:inline-block;padding:12px 28px;color:#ffffff;font-size:14px;font-weight:500;text-decoration:none;">
                            Change Password
                        </a>
                    </td>
                </tr>
            </table>
 
            <p style="margin:24px 0 0;font-size:13px;color:#9b9b9b;">
                If you need help, contact us at {support_email}
            </p>
        """
 
        html = wrap_email_html(content, "New Login Detected")
        text = (
            f"New login to your FoodDelivery account\n"
            f"Time: {login_time}\n"
            f"IP: {ip}\n"
            f"Device: {device}\n\n"
            f"If this wasn't you, change your password immediately: {frontend_url}/settings/change-password"
        )
 
        send_html_email(
            to_email  = user.email,
            subject   = "New Login to Your FoodRevolut Account",
            html_body = html,
            text_body = text,
        )
 
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
    

