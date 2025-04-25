import streamlit as st
import pandas as pd
import os
import base64
import json
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from email.mime.text import MIMEText

# Step 1: Write credentials.json from secrets (MUST be done before Gmail access)
# Google credentials will be retrieved from Streamlit secrets
google_creds = json.loads(st.secrets["GOOGLE_CREDS"])

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# Gmail API auth
def get_gmail_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_config(google_creds, SCOPES)
            creds = flow.run_console()  # This will use console-based OAuth2 authorization
        with open('token.json', 'w') as token_file:
            token_file.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)
    return service

# Create email message
def create_html_message(sender, to, subject, html_content):
    message = MIMEText(html_content, "html")
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    return {'raw': raw_message}

# Send the email
def send_email(service, user_id, message):
    return service.users().messages().send(userId=user_id, body=message).execute()

# Alert sending logic
def process_alerts(df):
    today = datetime.now().date()
    alert_days = {
        'Monthly': 4,
        'Quarterly': 7,
        'Half-yearly': 15,
        'Annually': 30
    }

    sender_email = 'janakiram@techprofuse.com'
    receiver_email = 'rakshitham@techprofuse.com'
    service = get_gmail_service()

    logs = []
    for index, row in df.iterrows():
        domain = row['domain name']
        end_date = pd.to_datetime(row['Zoho_end period']).date()
        frequency = row['billing frequency']
        days_before = alert_days.get(frequency)

        if not days_before:
            continue

        alert_date = end_date - timedelta(days=days_before)
        if today == alert_date:
            subject = f"Billing Alert: {domain}"
            html_content = f"""
            <p>Dear Team,</p>
            <p>This is a reminder that billing for <strong>{domain}</strong> is due on <strong>{end_date}</strong>.</p>
            <p><strong>Billing Frequency:</strong> {frequency}</p>
            <p>Please take necessary action.</p>
            <br><p>Regards,<br>Automated Alert System</p>
            """
            message = create_html_message(sender_email, receiver_email, subject, html_content)
            result = send_email(service, 'me', message)
            logs.append((domain, str(end_date), frequency, '✅ Sent', result['id']))
        else:
            logs.append((domain, str(end_date), frequency, '⏳ Not due today', ''))

    return logs

# UI starts here
st.title("📧 Zoho Billing Alert System")

uploaded_file = st.file_uploader("Upload Zoho Alert Excel", type=["xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file, engine="openpyxl")  # force openpyxl
    st.success("File uploaded successfully!")
    st.dataframe(df)

    if st.button("🚀 Send Alerts"):
        logs = process_alerts(df)
        st.success("Alerts processed!")
        st.write("Log Summary:")
        st.dataframe(pd.DataFrame(logs, columns=['Domain', 'End Date', 'Frequency', 'Status', 'Message ID']))
