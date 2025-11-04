import smtplib
import imaplib
import email
from email.header import decode_header
from email.utils import parseaddr
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from App.models import EmployeeEmailAccount
import base64
import os
import time

# --- (Constants and helper functions: decode_email_header, get_email_body_and_attachments - No changes) ---
HOSTINGER_IMAP_HOST = 'imap.hostinger.com'
HOSTINGER_IMAP_PORT = 993
HOSTINGER_SMTP_HOST = 'smtp.hostinger.com'
HOSTINGER_SMTP_PORT = 465

def decode_email_header(header_value):
    if not header_value:
        return ""
    decoded_headers = decode_header(header_value)
    decoded_string = []
    for s, encoding in decoded_headers:
        if isinstance(s, bytes):
            try:
                decoded_string.append(s.decode(encoding if encoding else "utf-8"))
            except (UnicodeDecodeError, LookupError):
                decoded_string.append(s.decode("latin-1", errors='ignore'))
        else:
            decoded_string.append(s)
    return "".join(decoded_string)

def get_email_body_and_attachments(msg):
    html_body = None
    text_body = None
    attachments = []
    for part in msg.walk():
        if part.is_multipart():
            continue
        content_type = part.get_content_type()
        content_disposition = part.get("Content-Disposition", "")
        filename = part.get_filename()
        if "attachment" in content_disposition or filename:
            try:
                decoded_filename = decode_email_header(filename) if filename else f"attachment_{len(attachments) + 1}"
                payload = part.get_payload(decode=True)
                
                attachments.append({
                    "filename": decoded_filename,
                    "content_type": content_type,
                    "size": len(payload),
                    "payload": base64.b64encode(payload).decode('utf-8')
                })
            except Exception as e:
                print(f"Error processing attachment: {e}")
        elif content_type == "text/html":
            try:
                charset = part.get_content_charset()
                payload = part.get_payload(decode=True)
                html_body = payload.decode(charset if charset else 'utf-8', errors='ignore')
            except Exception as e:
                html_body = part.get_payload()
        elif content_type == "text/plain" and not text_body:
            try:
                charset = part.get_content_charset()
                payload = part.get_payload(decode=True)
                text_body = payload.decode(charset if charset else 'utf-8', errors='ignore')
            except Exception as e:
                text_body = part.get_payload()
    
    return html_body, text_body, attachments

# --- UPDATED: Added search_query parameter ---
def fetch_hostinger_inbox(account: EmployeeEmailAccount, readonly=False, limit=50, mailbox='inbox', search_query=None):
    email_address = account.email_address
    password = account.email_password
    mail_list = []

    try:
        mail = imaplib.IMAP4_SSL(HOSTINGER_IMAP_HOST, HOSTINGER_IMAP_PORT)
        mail.login(email_address, password)
        mail.select(mailbox, readonly=readonly)
        
        # --- NEW: Use search query if provided ---
        if search_query:
            # (TEXT "query") searches headers and body.
            search_criteria = f'(TEXT "{search_query}")'
            status, messages = mail.search(None, search_criteria)
        else:
            status, messages = mail.search(None, 'ALL')
        # --- End search logic ---
            
        if status != 'OK':
            mail.logout()
            return []

        email_ids = messages[0].split()
        
        for e_id in reversed(email_ids[-limit:]):
            status, msg_data = mail.fetch(e_id, '(FLAGS RFC822)')
            
            if status == 'OK':
                flags_raw = imaplib.ParseFlags(msg_data[0][0])
                msg = email.message_from_bytes(msg_data[0][1])

                is_seen = '\\Seen' in flags_raw
                is_flagged = '\\Flagged' in flags_raw
                
                from_email = decode_email_header(msg.get("From"))
                subject = decode_email_header(msg.get("Subject"))
                date_str = msg.get("Date")

                has_attachments = False
                if msg.is_multipart():
                    for part in msg.walk():
                        content_disposition = part.get("Content-Disposition", "")
                        if "attachment" in content_disposition:
                            has_attachments = True
                            break

                mail_list.append({
                    "id": e_id.decode(),
                    "from": from_email,
                    "subject": subject or "(no subject)",
                    "date": date_str,
                    "is_seen": is_seen,
                    "is_flagged": is_flagged,
                    "has_attachments": has_attachments,
                })
        mail.logout()
        return mail_list

    except Exception as e:
        print(f"Error fetching email for {email_address}: {e}")
        return []

# --- (get_email_details - No changes) ---
def get_email_details(account: EmployeeEmailAccount, email_id: str, mailbox='inbox'):
    email_address = account.email_address
    password = account.email_password

    try:
        mail = imaplib.IMAP4_SSL(HOSTINGER_IMAP_HOST, HOSTINGER_IMAP_PORT)
        mail.login(email_address, password)
        mail.select(mailbox)
        status, msg_data = mail.fetch(email_id, '(RFC822)')
        
        if status != 'OK':
            mail.logout()
            return None

        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                
                subject = decode_email_header(msg.get("Subject"))
                from_email_full = decode_email_header(msg.get("From"))
                to_email = decode_email_header(msg.get("To"))
                date = msg.get("Date")
                
                from_name, from_address_only = parseaddr(from_email_full)
                reply_subject = "Re: " + subject
                if subject.lower().startswith("re:"):
                    reply_subject = subject

                html_body, text_body, attachments = get_email_body_and_attachments(msg)
                
                mail.store(email_id, '+FLAGS', '\\Seen')
                mail.logout()
                
                return {
                    "id": email_id,
                    "from": from_email_full,
                    "from_address_only": from_address_only,
                    "to": to_email,
                    "subject": subject,
                    "reply_subject": reply_subject,
                    "date": date,
                    "html_body": html_body,
                    "text_body": text_body,
                    "attachments": attachments
                }
        mail.logout()
        return None
    except Exception as e:
        print(f"Error fetching full email details: {e}")
        return None

# --- UPDATED: Added mailbox parameter. No longer hard-coded to 'inbox' ---
def toggle_email_flag(account: EmployeeEmailAccount, email_id: str, is_flagged: bool, mailbox='inbox'):
    try:
        mail = imaplib.IMAP4_SSL(HOSTINGER_IMAP_HOST, HOSTINGER_IMAP_PORT)
        mail.login(account.email_address, account.email_password)
        mail.select(mailbox) # <-- USES PARAMETER
        
        if is_flagged:
            mail.store(email_id, '+FLAGS', '\\Flagged')
        else:
            mail.store(email_id, '-FLAGS', '\\Flagged')
            
        mail.logout()
        return True
    except Exception as e:
        print(f"Error toggling flag for {email_id}: {e}")
        return False

# --- UPDATED: Selects source mailbox correctly ---
def move_email_to_trash(account: EmployeeEmailAccount, email_id: str, mailbox='inbox'):
    try:
        mail = imaplib.IMAP4_SSL(HOSTINGER_IMAP_HOST, HOSTINGER_IMAP_PORT)
        mail.login(account.email_address, account.email_password)
        
        # Select the source mailbox
        mail.select(mailbox) # <-- USES PARAMETER
        
        # Copy the email to the 'Trash' folder
        mail.copy(email_id, 'Trash')
        
        # Add the \Deleted flag in the source mailbox
        mail.store(email_id, '+FLAGS', '\\Deleted')
        
        # Expunge to permanently delete from the source mailbox
        mail.expunge()
        
        mail.logout()
        return True
    except Exception as e:
        print(f"Error moving email to trash: {e}")
        return False

# --- (send_hostinger_email & append_to_sent_folder - No changes) ---
def send_hostinger_email(account: EmployeeEmailAccount, to_email, subject, html_body, attachments=None):
    sender_email = account.email_address
    sender_password = account.email_password
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(html_body, 'html'))
    if attachments:
        for f in attachments:
            try:
                file_data = f.read()
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(file_data)
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="{f.name}"')
                msg.attach(part)
            except Exception as e:
                print(f"Error attaching file {f.name}: {e}")
                return (False, None)
    try:
        server = smtplib.SMTP_SSL(HOSTINGER_SMTP_HOST, HOSTINGER_SMTP_PORT)
        server.login(sender_email, sender_password)
        raw_message_string = msg.as_string()
        server.sendmail(sender_email, to_email, raw_message_string)
        server.quit()
        return (True, raw_message_string)
    except Exception as e:
        print(f"Error sending email for {sender_email}: {e}")
        return (False, None)

def append_to_sent_folder(account: EmployeeEmailAccount, raw_message_string: str):
    try:
        mail = imaplib.IMAP4_SSL(HOSTINGER_IMAP_HOST, HOSTINGER_IMAP_PORT)
        mail.login(account.email_address, account.email_password)
        mail.select('Sent') 
        mail.append(
            'Sent',
            '\\Seen',
            imaplib.Time2Internaldate(time.time()),
            raw_message_string.encode('utf-8')
        )
        print(f"Successfully appended sent mail to 'Sent' folder for {account.email_address}")
        mail.logout()
        return True
    except Exception as e:
        print(f"Error appending to 'Sent' folder: {e}")
        return False

# --- (get_unread_email_count & Gmail placeholders - No changes) ---
def get_unread_email_count(account: EmployeeEmailAccount, mailbox='inbox'):
    try:
        mail = imaplib.IMAP4_SSL(HOSTINGER_IMAP_HOST, HOSTINGER_IMAP_PORT)
        mail.login(account.email_address, account.email_password)
        mail.select(mailbox)
        status, messages = mail.search(None, 'UNSEEN')
        if status != 'OK':
            mail.logout()
            return 0
        unread_count = len(messages[0].split())
        mail.logout()
        return unread_count
    except Exception as e:
        print(f"Error getting unread count: {e}")
        return 0
    
    
def get_gmail_unread_count(account: EmployeeEmailAccount, mailbox='inbox'):
    print("Gmail unread count logic goes here.")
    return 0
def fetch_gmail_inbox(account: EmployeeEmailAccount, limit=50, mailbox='inbox'):
    print("Gmail fetch logic goes here.")
    return []
def send_gmail_email(account: EmployeeEmailAccount, to_email, subject, html_body, attachments=None):
    print("Gmail send logic goes here.")
    return (True, "Fake Gmail message string") # Placeholder
def get_gmail_email_details(account: EmployeeEmailAccount, email_id: str, mailbox='inbox'):
    print("Gmail details logic goes here.")
    return {}