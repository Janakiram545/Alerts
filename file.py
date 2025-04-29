import streamlit as st
import pandas as pd
import os
import base64
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from email.mime.text import MIMEText

# Constants
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"

# Step 1: Write credentials.json from Streamlit secrets (before anything)
if not os.path.exists(CREDENTIALS_FILE):
    with open(CREDENTIALS_FILE, "w") as f:
        f.write(st.secrets["GOOGLE_CREDS"])

# Auth Helper: Check if Gmail service is authenticated
def get_gmail_service():
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        if creds and creds.valid:
            return build('gmail', 'v1', credentials=creds)
    return None

# Auth Helper: Run manual OAuth flow if needed
def manual_auth_flow():
    flow = Flow.from_client_secrets_file(CREDENTIALS_FILE, scopes=SCOPES)
    flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
    auth_url, _ = flow.authorization_url(prompt='consent')

    st.info(f"👉 Please authorize: [Click here to authorize]({auth_url})")
    auth_code = st.text_input("🔑 Paste the authorization code here:")

    if auth_code:
    try:
        flow.fetch_token(code=auth_code)
        creds = flow.credentials
        with open('token.json', 'w') as token_file:
            token_file.write(creds.to_json())
        st.success("✅ Authorization successful! Please now click 'Send Alerts'.")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Failed to fetch token: {e}")
        st.stop()


# Gmail Email Creation
def create_html_message(sender, to, subject, html_content):
    message = MIMEText(html_content, "html")
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    return {'raw': raw_message}

# Gmail Email Sending
def send_email(service, user_id, message):
    return service.users().messages().send(userId=user_id, body=message).execute()

# Billing Logic
def process_alerts(df, service):
    today = datetime.now().date()
    alert_days = {
        'Monthly': 4,
        'Quarterly': 7,
        'Half-yearly': 15,
        'Annually': 30
    }

    sender_email = 'janakiram@techprofuse.com'
    receiver_email = 'kumara@techprofuse.com'
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

# Streamlit UI
st.title("📧 Zoho Billing Alert System")

uploaded_file = st.file_uploader("📂 Upload Zoho Alert Excel", type=["xlsx"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file, engine="openpyxl")
        st.success("✅ File uploaded successfully!")
        st.dataframe(df)

        # Step 1: Check if authorized
        service = get_gmail_service()
        if not service:
            st.warning("⚠️ Gmail is not authenticated. Please authorize.")
            manual_auth_flow()
        else:
            # Step 2: Show Send Alerts button
            if st.button("🚀 Send Alerts"):
                logs = process_alerts(df, service)
                st.success("📬 Alerts processed!")
                st.write("📄 Log Summary:")
                st.dataframe(pd.DataFrame(logs, columns=['Domain', 'End Date', 'Frequency', 'Status', 'Message ID']))

    except Exception as e:
        st.error(f"❌ Error reading the file: {e}")
