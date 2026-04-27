from django.conf import settings 
from celery import shared_task

# ─────────────────────────────────────────────────────────────────────────────
# STATUS HANDLERS — one function per status transition
# Each handles WHO gets notified and WHAT they see
# ─────────────────────────────────────────────────────────────────────────────



def _notify_placed(order, send_html_email, wrap_email_html):
    """New order → notify restaurant owner."""
    items_html = "".join([
        f"<tr>"
        f"<td style='padding:8px 0;font-size:14px;color:#1a1a1a;border-bottom:1px solid #f0f0f0;'>"
        f"{item.item_name}"
        f"{'  (' + item.variant_name + ')' if item.variant_name else ''}"
        f"</td>"
        f"<td style='padding:8px 0;font-size:14px;color:#1a1a1a;text-align:right;border-bottom:1px solid #f0f0f0;'>"
        f"x{item.quantity} — ₹{item.subtotal}"
        f"</td>"
        f"</tr>"
        for item in order.items.all()
    ])

    content = f"""
        <p style="margin:0 0 16px;font-size:16px;color:#1a1a1a;font-weight:500;">
            Hi {order.restaurant.owner.name},
        </p>
        <p style="margin:0 0 24px;font-size:15px;color:#4a4a4a;">
            You have a new order from <strong>{order.customer.name}</strong>.
        </p>

        <table width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 24px;">
            {items_html}
            <tr>
                <td style="padding:12px 0 4px;font-size:14px;color:#6b6b6b;">Subtotal</td>
                <td style="padding:12px 0 4px;font-size:14px;color:#6b6b6b;text-align:right;">₹{order.subtotal}</td>
            </tr>
            <tr>
                <td style="padding:4px 0;font-size:14px;color:#6b6b6b;">Delivery fee</td>
                <td style="padding:4px 0;font-size:14px;color:#6b6b6b;text-align:right;">₹{order.delivery_fee}</td>
            </tr>
            <tr>
                <td style="padding:8px 0 0;font-size:15px;color:#1a1a1a;font-weight:500;">Total</td>
                <td style="padding:8px 0 0;font-size:15px;color:#e85d30;font-weight:500;text-align:right;">₹{order.total_amount}</td>
            </tr>
        </table>

        <p style="margin:0 0 8px;font-size:14px;color:#6b6b6b;">
            Payment: <strong>{order.get_payment_method_display()}</strong>
            {"— Paid" if order.is_paid else "— Pending"}
        </p>
        <p style="margin:0;font-size:14px;color:#6b6b6b;">
            Delivery to: {order.delivery_address}
        </p>
        {"<p style='margin:8px 0 0;font-size:14px;color:#6b6b6b;'>Note: " + order.customer_notes + "</p>" if order.customer_notes else ""}
    """

    html = wrap_email_html(content, "New Order Received")
    text = (
        f"New order from {order.customer.name}\n"
        f"Total: ₹{order.total_amount}\n"
        f"Payment: {order.get_payment_method_display()}\n"
        f"Deliver to: {order.delivery_address}"
    )

    send_html_email(
        to_email = order.restaurant.owner.email,
        subject  = f"New Order — ₹{order.total_amount}",
        html_body = html,
        text_body = text,
    )


def _notify_accepted(order, send_html_email, wrap_email_html):
    """Restaurant accepted → notify customer."""
    content = f"""
        <p style="margin:0 0 16px;font-size:16px;color:#1a1a1a;font-weight:500;">
            Hi {order.customer.name},
        </p>
        <p style="margin:0 0 8px;font-size:15px;color:#4a4a4a;">
            Great news! <strong>{order.restaurant.name}</strong> has accepted your order.
        </p>
        <p style="margin:0 0 24px;font-size:15px;color:#4a4a4a;">
            Your food is being prepared. We'll notify you when it's on the way.
        </p>
        {_order_summary_html(order)}
    """

    html = wrap_email_html(content, "Order Accepted")
    text = f"Your order from {order.restaurant.name} has been accepted. Food is being prepared."

    send_html_email(
        to_email  = order.customer.email,
        subject   = f"Order Accepted — {order.restaurant.name}",
        html_body = html,
        text_body = text,
    )


def _notify_preparing(order, send_html_email, wrap_email_html):
    """Preparing → notify customer."""
    content = f"""
        <p style="margin:0 0 16px;font-size:16px;color:#1a1a1a;font-weight:500;">
            Hi {order.customer.name},
        </p>
        <p style="margin:0 0 24px;font-size:15px;color:#4a4a4a;">
            Your order from <strong>{order.restaurant.name}</strong> is being prepared.
            We'll let you know when it's ready for pickup.
        </p>
        {_order_summary_html(order)}
    """

    html = wrap_email_html(content, "Your Food is Being Prepared")
    text = f"Your order from {order.restaurant.name} is being prepared."

    send_html_email(
        to_email  = order.customer.email,
        subject   = f"Preparing Your Order — {order.restaurant.name}",
        html_body = html,
        text_body = text,
    )


def _notify_ready(order, send_html_email, wrap_email_html):
    """Ready for pickup → notify delivery agent."""
    if not order.delivery_agent:
        return

    content = f"""
        <p style="margin:0 0 16px;font-size:16px;color:#1a1a1a;font-weight:500;">
            Hi {order.delivery_agent.name},
        </p>
        <p style="margin:0 0 24px;font-size:15px;color:#4a4a4a;">
            An order is ready for pickup at <strong>{order.restaurant.name}</strong>.
        </p>

        <table width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 24px;background:#f9f9f9;border-radius:6px;padding:16px;">
            <tr>
                <td style="font-size:14px;color:#6b6b6b;padding:4px 0;">Restaurant</td>
                <td style="font-size:14px;color:#1a1a1a;text-align:right;">{order.restaurant.name}</td>
            </tr>
            <tr>
                <td style="font-size:14px;color:#6b6b6b;padding:4px 0;">Address</td>
                <td style="font-size:14px;color:#1a1a1a;text-align:right;">{order.restaurant.address}, {order.restaurant.city}</td>
            </tr>
            <tr>
                <td style="font-size:14px;color:#6b6b6b;padding:4px 0;">Deliver to</td>
                <td style="font-size:14px;color:#1a1a1a;text-align:right;">{order.delivery_address}</td>
            </tr>
            <tr>
                <td style="font-size:14px;color:#6b6b6b;padding:4px 0;">Order value</td>
                <td style="font-size:14px;color:#e85d30;font-weight:500;text-align:right;">₹{order.total_amount}</td>
            </tr>
            <tr>
                <td style="font-size:14px;color:#6b6b6b;padding:4px 0;">Payment</td>
                <td style="font-size:14px;color:#1a1a1a;text-align:right;">
                    {order.get_payment_method_display()} — {"Paid" if order.is_paid else "Collect on delivery"}
                </td>
            </tr>
        </table>
    """

    html = wrap_email_html(content, "Order Ready for Pickup")
    text = (
        f"Order ready at {order.restaurant.name}\n"
        f"Deliver to: {order.delivery_address}\n"
        f"Value: ₹{order.total_amount}"
    )

    send_html_email(
        to_email  = order.delivery_agent.email,
        subject   = f"Pickup Ready — {order.restaurant.name}",
        html_body = html,
        text_body = text,
    )


def _notify_picked_up(order, send_html_email, wrap_email_html):
    """Agent picked up → notify customer."""
    agent_name = order.delivery_agent.name if order.delivery_agent else "Your delivery agent"

    content = f"""
        <p style="margin:0 0 16px;font-size:16px;color:#1a1a1a;font-weight:500;">
            Hi {order.customer.name},
        </p>
        <p style="margin:0 0 24px;font-size:15px;color:#4a4a4a;">
            <strong>{agent_name}</strong> has picked up your order from
            <strong>{order.restaurant.name}</strong> and is on the way to you.
        </p>
        {_order_summary_html(order)}
    """

    html = wrap_email_html(content, "Your Order is On the Way")
    text = f"{agent_name} has picked up your order and is heading your way."

    send_html_email(
        to_email  = order.customer.email,
        subject   = f"On the Way — {order.restaurant.name}",
        html_body = html,
        text_body = text,
    )


def _notify_delivered(order, send_html_email, wrap_email_html):
    """Delivered → notify customer + restaurant."""
    # ── Customer email ────────────────────────────────────────────────────
    frontend_url  = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
    review_link   = f"{frontend_url}/orders/{order.id}/review"

    content = f"""
        <p style="margin:0 0 16px;font-size:16px;color:#1a1a1a;font-weight:500;">
            Hi {order.customer.name},
        </p>
        <p style="margin:0 0 24px;font-size:15px;color:#4a4a4a;">
            Your order from <strong>{order.restaurant.name}</strong> has been delivered.
            Enjoy your meal!
        </p>
        {_order_summary_html(order)}
        <table cellpadding="0" cellspacing="0" style="margin:24px 0 0;">
            <tr>
                <td style="background-color:#e85d30;border-radius:6px;">
                    <a href="{review_link}"
                       style="display:inline-block;padding:12px 28px;color:#ffffff;font-size:14px;font-weight:500;text-decoration:none;">
                        Rate Your Experience
                    </a>
                </td>
            </tr>
        </table>
    """

    html = wrap_email_html(content, "Order Delivered")
    text = f"Your order from {order.restaurant.name} has been delivered. Rate your experience: {review_link}"

    send_html_email(
        to_email  = order.customer.email,
        subject   = f"Order Delivered — {order.restaurant.name}",
        html_body = html,
        text_body = text,
    )

    # ── Restaurant email ──────────────────────────────────────────────────
    content_rest = f"""
        <p style="margin:0 0 16px;font-size:16px;color:#1a1a1a;font-weight:500;">
            Hi {order.restaurant.owner.name},
        </p>
        <p style="margin:0 0 24px;font-size:15px;color:#4a4a4a;">
            Order <strong>#{str(order.id)[:8].upper()}</strong> has been successfully delivered
            to <strong>{order.customer.name}</strong>.
        </p>
        {_order_summary_html(order)}
    """

    html_rest = wrap_email_html(content_rest, "Order Completed")
    text_rest  = f"Order #{str(order.id)[:8].upper()} delivered to {order.customer.name}. Total: ₹{order.total_amount}"

    send_html_email(
        to_email  = order.restaurant.owner.email,
        subject   = f"Order Completed — ₹{order.total_amount}",
        html_body = html_rest,
        text_body = text_rest,
    )


def _notify_cancelled(order, send_html_email, wrap_email_html):
    """Cancelled → notify customer + restaurant + agent (if assigned)."""
    reason = order.cancellation_reason or "No reason provided."
    cancelled_by = order.get_cancelled_by_display() if order.cancelled_by else "System"

    # ── Customer email ────────────────────────────────────────────────────
    content = f"""
        <p style="margin:0 0 16px;font-size:16px;color:#1a1a1a;font-weight:500;">
            Hi {order.customer.name},
        </p>
        <p style="margin:0 0 8px;font-size:15px;color:#4a4a4a;">
            Your order from <strong>{order.restaurant.name}</strong> has been cancelled.
        </p>
        <p style="margin:0 0 24px;font-size:14px;color:#6b6b6b;">
            Reason: {reason}
        </p>
        {_order_summary_html(order)}
        <p style="margin:24px 0 0;font-size:14px;color:#6b6b6b;">
            If you paid online, your refund will be processed within 5-7 business days.
        </p>
    """

    html = wrap_email_html(content, "Order Cancelled")
    text = f"Your order from {order.restaurant.name} has been cancelled.\nReason: {reason}"

    send_html_email(
        to_email  = order.customer.email,
        subject   = f"Order Cancelled — {order.restaurant.name}",
        html_body = html,
        text_body = text,
    )

    # ── Restaurant email ──────────────────────────────────────────────────
    content_rest = f"""
        <p style="margin:0 0 16px;font-size:16px;color:#1a1a1a;font-weight:500;">
            Hi {order.restaurant.owner.name},
        </p>
        <p style="margin:0 0 24px;font-size:15px;color:#4a4a4a;">
            Order <strong>#{str(order.id)[:8].upper()}</strong> from
            <strong>{order.customer.name}</strong> has been cancelled by {cancelled_by}.
        </p>
        <p style="margin:0;font-size:14px;color:#6b6b6b;">Reason: {reason}</p>
    """

    html_rest = wrap_email_html(content_rest, "Order Cancelled")
    text_rest  = f"Order #{str(order.id)[:8].upper()} cancelled by {cancelled_by}.\nReason: {reason}"

    send_html_email(
        to_email  = order.restaurant.owner.email,
        subject   = f"Order Cancelled — #{str(order.id)[:8].upper()}",
        html_body = html_rest,
        text_body = text_rest,
    )

    # ── Agent email — only if assigned ───────────────────────────────────
    if order.delivery_agent:
        content_agent = f"""
            <p style="margin:0 0 16px;font-size:16px;color:#1a1a1a;font-weight:500;">
                Hi {order.delivery_agent.name},
            </p>
            <p style="margin:0 0 24px;font-size:15px;color:#4a4a4a;">
                The order assigned to you from <strong>{order.restaurant.name}</strong>
                has been cancelled. No action needed.
            </p>
            <p style="margin:0;font-size:14px;color:#6b6b6b;">Reason: {reason}</p>
        """

        html_agent = wrap_email_html(content_agent, "Delivery Cancelled")
        text_agent = f"Your assigned order from {order.restaurant.name} has been cancelled."

        send_html_email(
            to_email  = order.delivery_agent.email,
            subject   = "Assigned Order Cancelled",
            html_body = html_agent,
            text_body = text_agent,
        )


# ─────────────────────────────────────────────────────────────────────────────
# PAYMENT NOTIFICATION
# ─────────────────────────────────────────────────────────────────────────────

@shared_task(bind=True, max_retries=3)
def notify_payment_confirmed(self, order_id):
    """Fires after successful payment verification."""
    try:
        from apps.orders.models import Order
        from apps.users.emails import send_html_email, wrap_email_html

        order = Order.objects.select_related("customer", "restaurant").get(pk=order_id)

        content = f"""
            <p style="margin:0 0 16px;font-size:16px;color:#1a1a1a;font-weight:500;">
                Hi {order.customer.name},
            </p>
            <p style="margin:0 0 24px;font-size:15px;color:#4a4a4a;">
                Your payment of <strong>₹{order.total_amount}</strong> for your order
                from <strong>{order.restaurant.name}</strong> has been confirmed.
            </p>
            {_order_summary_html(order)}
        """

        html = wrap_email_html(content, "Payment Confirmed")
        text = f"Payment of ₹{order.total_amount} confirmed for your order from {order.restaurant.name}."

        send_html_email(
            to_email  = order.customer.email,
            subject   = f"Payment Confirmed — ₹{order.total_amount}",
            html_body = html,
            text_body = text,
        )

    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


# ─────────────────────────────────────────────────────────────────────────────
# SHARED TEMPLATE HELPER
# ─────────────────────────────────────────────────────────────────────────────

def _order_summary_html(order):
    """Reusable order summary block — used in multiple email templates."""
    return f"""
        <table width="100%" cellpadding="0" cellspacing="0"
               style="background:#f9f9f9;border-radius:6px;padding:16px;margin:0;">
            <tr>
                <td style="font-size:14px;color:#6b6b6b;padding:4px 0;">Order ID</td>
                <td style="font-size:14px;color:#1a1a1a;text-align:right;">#{str(order.id)[:8].upper()}</td>
            </tr>
            <tr>
                <td style="font-size:14px;color:#6b6b6b;padding:4px 0;">Restaurant</td>
                <td style="font-size:14px;color:#1a1a1a;text-align:right;">{order.restaurant.name}</td>
            </tr>
            <tr>
                <td style="font-size:14px;color:#6b6b6b;padding:4px 0;">Total</td>
                <td style="font-size:15px;color:#e85d30;font-weight:500;text-align:right;">₹{order.total_amount}</td>
            </tr>
            <tr>
                <td style="font-size:14px;color:#6b6b6b;padding:4px 0;">Payment</td>
                <td style="font-size:14px;color:#1a1a1a;text-align:right;">
                    {order.get_payment_method_display()} — {"Paid" if order.is_paid else "Pending"}
                </td>
            </tr>
        </table>
    """

