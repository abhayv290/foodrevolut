from celery import shared_task 
from django.utils import timezone
from datetime import timedelta
from .emails import _notify_accepted,_notify_cancelled,_notify_delivered,_notify_picked_up,_notify_placed,_notify_preparing,_notify_ready,_order_summary_html,notify_payment_confirmed
@shared_task
def cancel_unpaid_orders():
    '''
    Run Every 5 minutes via celery beat
    Cancel Online payments orders  unpaid  after  15 minutes  '''

    from .models import Order ,OrderStatusHistory


    cutoff = timezone.now() - timedelta(minutes=15)
    unpaid = Order.objects.filter(status = Order.Status.PLACED,
                                 is_paid = False,
                                 payment_method__in = ['UPI','CARD','NETBANKING','WALLET']
                                , placed_at__lt =cutoff)
    for order in unpaid : 
        order.status = Order.Status.CANCELLED
        order.cancelled_by = Order.CancelledBy.SYSTEM
        order.cancellation_reason= 'Payment not completed within 15 minute of ordering'
        order.save(update_fields=['status','cancelled_by','cancellation_reason'])

        
        from apps.payments.models import Payment
        Payment.objects.filter(
            order= order ,
            status = Payment.Status.PENDING
        ).update(status = Payment.Status.FAILED,failure_reason = 'Payment timeout - order auto-cancelled.')

        OrderStatusHistory.objects.create(
            order= order ,
            status  = Order.Status.CANCELLED,
            note = 'Auto Cancelled - payment timeout'
        )

@shared_task
def assign_delivery_agent_task(order_id):
    '''
    Trigger when restaurant marks order ready 
    find nearest available agent and assign
    Retries  up to 5 times  if on agent found 
    '''

    from .models import Order
    from .utils import assign_delivery_agent

    try:
        order = Order.objects.get(pk=order_id)
        assigned = assign_delivery_agent(order)
        
        if not assigned:
            #retry after 2 minutes
            raise assign_delivery_agent_task.retry(countdown=120, max_retries=5) #type:ignore
    except Order.DoesNotExist:
        pass 


# ─────────────────────────────────────────────────────────────────────────────
# ORDER NOTIFICATION TASKS
#
# ── Why Celery for emails? ────────────────────────────────────────────────────
# Email sending adds 200-500ms latency (Mailgun API call).
# Order status updates should respond instantly to the client.
# Celery fires the email in the background — view returns immediately.
#
# ── Pattern ───────────────────────────────────────────────────────────────────
# Views call: notify_order_status_changed.delay(order_id, new_status)
# Celery picks up the task, fetches order from DB, sends appropriate emails.
# ─────────────────────────────────────────────────────────────────────────────

@shared_task(bind=True, max_retries=3)
def notify_order_status_changed(self, order_id, new_status):
    """
    Master notification task — fires after every order status transition.
    Routes to the right recipients based on the new status.

    bind=True      → gives access to self for retry logic
    max_retries=3  → retries up to 3 times if Mailgun fails
    """
    try:
        from apps.orders.models import Order
        from apps.users.emails import send_html_email, wrap_email_html

        order = Order.objects.select_related(
            "customer",
            "restaurant__owner",
            "delivery_agent",
        ).get(pk=order_id)

        # route to correct handler based on status
        handlers = {
            Order.Status.PLACED:    _notify_placed,
            Order.Status.ACCEPTED:  _notify_accepted,
            Order.Status.PREPARING: _notify_preparing,
            Order.Status.READY:     _notify_ready,
            Order.Status.PICKED_UP: _notify_picked_up,
            Order.Status.DELIVERED: _notify_delivered,
            Order.Status.CANCELLED: _notify_cancelled,
        }

        handler = handlers.get(new_status)
        if handler:
            handler(order, send_html_email, wrap_email_html)

    except Exception as exc:
        # ── Retry on failure ──────────────────────────────────────────────
        # countdown=60 → wait 60 seconds before retry
        # exponential backoff: 60s, 120s, 240s
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))



