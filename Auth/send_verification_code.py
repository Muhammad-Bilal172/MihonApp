import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import *
from Auth.create_jwt_token import create_jwt_token

def send_verification_code_func(email, text):
    sender_email = "bilalashiq190@gmail.com"
    receiver_email = email
    password = smtplibPassword

    message = MIMEMultipart("alternative")
    message["Subject"] = "Email Verification From Bilal"
    message["From"] = sender_email
    message["To"] = receiver_email

    part = MIMEText(text, "plain")

    message.attach(part)

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, password)

        server.sendmail(sender_email, receiver_email, message.as_string())

    except Exception as e:
        return e

    finally:
        server.quit()
