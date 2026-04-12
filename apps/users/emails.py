from django.core.mail import send_mail
from django.conf import settings 


def text_email(name,link):
    return f"""
    Hi {name},
    Thanks for signing up with foodRevolut
    
    Please verify your email  address  by clicking  the link below:
    {link}
    
    this link will expires in within 10 minutes 
    
    If you didn't sent this request , ignore this 
    """.strip()
def text_email_reset_password(name,link):
    return f"""
    Hi {name},
    
    Click the link below to reset your password:
    {link}
    
    this link will expires in within 10 minutes 
    
    If you didn't sent this request , ignore this 
    """.strip()

def send_verification_email(user,token):
    link  = f"http://localhost:8000/api/v1/auth/email/verify/?token={token}"
    text_body = text_email(user.name,link)
    send_mail(
        subject='Verify Your FoodRevolut Account',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        message=text_body
    )


def send_password_reset_email(user,token):
    link = f"http://localhost:8000/api/v1/auth/password/reset/?token={token}"
    text_body = text_email_reset_password(user.name,link)
    send_mail(
        subject='Reset Your Old password ',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        message=text_body
    )