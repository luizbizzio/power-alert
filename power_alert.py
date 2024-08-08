import os
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import locale

# Set Locale
locale.setlocale(locale.LC_TIME, 'C')
# locale.setlocale(locale.LC_TIME, 'en_GB.UTF-8') # Example of another locale 

# Email Configuration
sender_email = "SENDER_EMAIL"
sender_password = "SENDER_EMAIL_PASSWORD"
receiver_emails = ["RECEIVER_EMAIL_1", "RECEIVER_EMAIL_2"]
smtp_server = "SMTP_SERVER" # SMTP server examples: Outlook - smtp.office365.com, Gmail - smtp.gmail.com, Yahoo - smtp.mail.yahoo.com
smtp_port = 587

# Device IPs to monitor
device_ips = ['192.168.0.9','192.168.0.23']

# Modem and Router IPs
modem_ip = '192.168.1.254'
router_ip = '192.168.0.1'

# Number of times a device must be offline to trigger a notification
max_offline_checks = 3

offline_counts = {ip: 0 for ip in device_ips}

def send_email(subject, message):
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)

            msg = MIMEMultipart()
            msg['From'] = f"Power Alert <{sender_email}>"
            msg['Subject'] = subject
            msg.attach(MIMEText(message, 'plain'))

            for email in receiver_emails:
                msg['To'] = email
                server.sendmail(sender_email, email, msg.as_string())

        print("Email successfully sent!")
    except Exception as e:
        print(f"Error sending email: {e}")

def is_device_online(ip):
    try:
        response = os.system(f"ping -c 1 {ip} > /dev/null 2>&1")
        online = response == 0
        status = "online" if online else "offline"
        return online, status
    except Exception as e:
        print(f"Error checking device status {ip}: {e}")
        return False, "error"

def check_network_devices():
    modem_online, modem_status = is_device_online(modem_ip)
    router_online, router_status = is_device_online(router_ip)

    print(f"\n{datetime.now().strftime('%H:%M:%S')} - Modem ({modem_ip}) is {modem_status}.")
    print(f"{datetime.now().strftime('%H:%M:%S')} - Router ({router_ip}) is {router_status}.")

    if not (modem_online and router_online):
        print("Waiting for modem and router connection...")
        return False

    print("Modem and router are online.\nProceeding with device verification.")
    return True

def monitor_devices(ips):
    email_sent = False
    first_run = True

    while True:
        if first_run:
            print("Waiting 1 minute before starting monitoring...")
            time.sleep(60)  # Time before starting script
            first_run = False

        if check_network_devices():
            current_time = datetime.now().strftime("%I:%M:%S %p on %B %d, %Y")
            all_offline = True

            for ip in ips:
                online, status = is_device_online(ip)
                print(f"{datetime.now().strftime('%H:%M:%S')} - Device ({ip}) is {status}.")

                if online:
                    offline_counts[ip] = 0
                    all_offline = False
                else:
                    offline_counts[ip] += 1

            if all([offline_counts[ip] >= max_offline_checks for ip in ips]) and not email_sent:
                subject = "Power Outage ⚡🏚"
                message = f"A power outage was detected at your residence at {current_time}."
                send_email(subject, message)
                email_sent = True
            elif any([offline_counts[ip] < max_offline_checks for ip in ips]) and email_sent:
                subject = "Power Restored ✅🏡"
                message = f"Power was restored to your home at {current_time}."
                send_email(subject, message)
                email_sent = False

        time.sleep(10)  # Time before checking devices again

if __name__ == "__main__":
    monitor_devices(device_ips)

