import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

logger = logging.getLogger("price_tracker")

def send_price_drop_alert(to_email: str, product_name: str, current_price: float, currency: str, product_url: str):
    # Configure your SMTP credentials (e.g., Gmail App Password or local SMTP relay)
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = "shreyanshsonkar59@gmail.com"
    sender_password = "12345678"

    if sender_email == "shreyanshsonkar59@gmail.com":
        logger.warning("SMTP credentials not configured. Skipping actual email send.")
        return

    try:
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = to_email
        msg["Subject"] = f"🔥 Price Drop Alert: {product_name} is now {current_price} {currency}!"

        body = f"""
        Hi there,
        
        Good news! The product you are tracking on PricePulse has hit your target price.
        
        Product: {product_name}
        New Price: {current_price} {currency}
        
        Click here to grab the deal: {product_url}
        
        Best regards,
        PricePulse Intelligence Engine
        """
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, msg.as_string())
            
        logger.info(f"Price drop alert email successfully sent to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send email alert: {e}")