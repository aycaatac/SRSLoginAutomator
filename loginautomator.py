from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
import time
import imaplib
import email
from email.header import decode_header
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re

from bs4 import BeautifulSoup
import re
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_argument("--disable-features=CookiesWithoutSameSiteMustBeSecure")
chrome_options.add_argument("--disable-site-isolation-trials")
chrome_options.add_argument("--disable-popup-blocking")
chrome_options.add_experimental_option(
    "detach", True
)  # makes sure the site doesnt close afterwards
chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])


email_user = "your-mail-address"
email_pass = "your-mail-password"
imap_server = "mail.bilkent.edu.tr" #the imap server of bilkent's webmail
imap_port = 993


def fetch_email_code(email_user, email_pass, imap_server, imap_port=993):
    try:
        mail = imaplib.IMAP4_SSL(imap_server, imap_port)
        mail.login(email_user, email_pass)

        mail.select("inbox")

        status, messages = mail.search(None, "ALL")
        if status != "OK":
            print("Failed to search emails!")
            return None

        email_ids = messages[0].split()
        if not email_ids:
            print("No emails found!")
            return None

        latest_email_id = email_ids[-1]

        status, msg_data = mail.fetch(latest_email_id, "(RFC822)")
        if status != "OK":
            print("Failed to fetch the email!")
            return None

        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                email_body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        if content_type == "text/plain":
                            email_body = part.get_payload(decode=True).decode()
                        elif content_type == "text/html":
                            email_body = part.get_payload(decode=True).decode()

                            soup = BeautifulSoup(email_body, "html.parser")

                            text_content = soup.get_text()
                            match = re.search(
                                r"Verification Code:\s*(\d{5})", text_content
                            )
                            if match:
                                return match.group(1)
                else:
                    email_body = msg.get_payload(decode=True).decode()
                    match = re.search(r"Verification Code:\s*(\d{5})", email_body)
                    if match:
                        return match.group(1)
        print("No 2FA code found in the email!")

    except Exception as e:
        print(f"Error fetching email: {e}")
    finally:
        try:
            mail.logout()
        except Exception as e:
            print(f"Error during logout: {e}")

    return None

def extract_code(email_body):
    import re

    match = re.search(r"Verification Code:\s*(\d{5})", email_body)
    if match:
        return match.group(1)
    return None


driver_path = (
    r"your-driver-path"
)

service = Service(driver_path)

driver = webdriver.Chrome(service=service, options=chrome_options)

service_url = "https://stars.bilkent.edu.tr/srs"

driver.get(service_url)

id_input = WebDriverWait(driver, 10).until(
    EC.visibility_of_element_located((By.ID, "LoginForm_username"))
)
id_input.send_keys("your-bilkent-id")

password_input = WebDriverWait(driver, 10).until(
    EC.visibility_of_element_located((By.ID, "LoginForm_password"))
)
password_input.send_keys("your-srs-password")
password_input.send_keys(Keys.RETURN)

time.sleep(5)

WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.ID, "EmailVerifyForm_verifyCode"))
)

code = fetch_email_code(email_user, email_pass, imap_server)

if code:
    print(f"Fetched 2FA code: {code}")

    code_input = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "EmailVerifyForm_verifyCode"))
    )
    code_input.send_keys(code)
    code_input.send_keys(Keys.RETURN)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "center"))
        )
        print("Login successful!")
    except Exception as e:
        print("Login failed or timed out!")
        print(f"Error: {e}")
else:
    print("Failed to fetch 2FA code.")
