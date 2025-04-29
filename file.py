# import streamlit as st
# import pandas as pd
# import os
# import base64
# from datetime import datetime, timedelta
# from googleapiclient.discovery import build
# from google_auth_oauthlib.flow import Flow
# from google.auth.transport.requests import Request
# from google.oauth2.credentials import Credentials
# from email.mime.text import MIMEText

# # Constants
# SCOPES = ['https://www.googleapis.com/auth/gmail.send']
# CREDENTIALS_FILE = "credentials.json"
# TOKEN_FILE = "token.json"

# # Step 1: Write credentials.json from Streamlit secrets (before anything)
# if not os.path.exists(CREDENTIALS_FILE):
#     with open(CREDENTIALS_FILE, "w") as f:
#         f.write(st.secrets["GOOGLE_CREDS"])

# # Auth Helper: Check if Gmail service is authenticated
# def get_gmail_service():
#     if os.path.exists(TOKEN_FILE):
#         creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
#         if creds and creds.valid:
#             return build('gmail', 'v1', credentials=creds)
#     return None

# # Auth Helper: Run manual OAuth flow if needed
# def manual_auth_flow():
#     flow = Flow.from_client_secrets_file(CREDENTIALS_FILE, scopes=SCOPES)
#     flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
#     auth_url, _ = flow.authorization_url(prompt='consent')

#     st.info(f"👉 Please authorize: [Click here to authorize]({auth_url})")
#     auth_code = st.text_input("🔑 Paste the authorization code here:")

#     if auth_code:
#         try:
#             flow.fetch_token(code=auth_code)
#             creds = flow.credentials
#             with open(TOKEN_FILE, 'w') as token_file:
#                 token_file.write(creds.to_json())
#             st.success("✅ Authorization successful! Please now click 'Send Alerts'.")
#             st.rerun()
#         except Exception as e:
#             st.error(f"❌ Failed to fetch token: {e}")
#             st.stop()
#     else:
#         st.stop()




# # Gmail Email Creation
# def create_html_message(sender, to, subject, html_content):
#     message = MIMEText(html_content, "html")
#     message['to'] = to
#     message['from'] = sender
#     message['subject'] = subject
#     raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
#     return {'raw': raw_message}

# # Gmail Email Sending
# def send_email(service, user_id, message):
#     return service.users().messages().send(userId=user_id, body=message).execute()

# # Billing Logic
# def process_alerts(df, service):
#     today = datetime.now().date()
#     alert_days = {
#         'Monthly': 3,
#         'Quarterly': 6,
#         'Half-yearly': 15,
#         'Annually': 30
#     }

#     sender_email = 'janakiram@techprofuse.com'
#     receiver_email = 'kumara@techprofuse.com'
#     logs = []

#     for index, row in df.iterrows():
#         domain = row['domain name']
#         end_date = pd.to_datetime(row['Zoho_end period']).date()
#         frequency = row['billing frequency']
#         days_before = alert_days.get(frequency)

#         if not days_before:
#             continue

#         alert_date = end_date - timedelta(days=days_before)
#         if today == alert_date:
#             subject = f"Billing Alert: {domain}"
#             html_content = f"""
#             <p>Dear Team,</p>
#             <p>This is a reminder that billing for <strong>{domain}</strong> is due on <strong>{end_date}</strong>.</p>
#             <p><strong>Billing Frequency:</strong> {frequency}</p>
#             <p>Please take necessary action.</p>
#             <br><p>Regards,<br>Automated Alert System</p>
#             """
#             message = create_html_message(sender_email, receiver_email, subject, html_content)
#             result = send_email(service, 'me', message)
#             logs.append((domain, str(end_date), frequency, '✅ Sent', result['id']))
#         # else:
#         #     logs.append((domain, str(end_date), frequency, '⏳ Not due today', ''))

#     return logs

# # Streamlit UI
# st.title("📧 Zoho Billing Alert System")

# uploaded_file = st.file_uploader("📂 Upload Zoho Alert Excel", type=["xlsx"])

# if uploaded_file is not None:
#     try:
#         df = pd.read_excel(uploaded_file, engine="openpyxl")
#         st.success("✅ File uploaded successfully!")
#         st.dataframe(df)

#         # Step 1: Check if authorized
#         service = get_gmail_service()
#         if not service:
#             st.warning("⚠️ Gmail is not authenticated. Please authorize.")
#             manual_auth_flow()
#         else:
#             # Step 2: Show Send Alerts button
#             if st.button("🚀 Send Alerts"):
#                 logs = process_alerts(df, service)
#                 st.success("📬 Alerts processed!")
#                 st.write("📄 Log Summary:")
#                 st.dataframe(pd.DataFrame(logs, columns=['Domain', 'End Date', 'Frequency', 'Status', 'Message ID']))

#     except Exception as e:
#         st.error(f"❌ Error reading the file: {e}")


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
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import tempfile

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
            with open(TOKEN_FILE, 'w') as token_file:
                token_file.write(creds.to_json())
            st.success("✅ Authorization successful! Please now click 'Send Alerts'.")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Failed to fetch token: {e}")
            st.stop()
    else:
        st.stop()

# Create email with attachment
def create_email_with_attachment(sender, to, subject, body_html, attachment_path):
    message = MIMEMultipart()
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject

    # Add body
    message.attach(MIMEText(body_html, 'html'))

    # Attach Excel file
    with open(attachment_path, 'rb') as f:
        part = MIMEBase('application', 'vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(attachment_path))
        message.attach(part)

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    return {'raw': raw_message}

# Send email
def send_email(service, user_id, message):
    return service.users().messages().send(userId=user_id, body=message).execute()

# Collect all due alerts and create temp Excel file
def prepare_alerts_file(df):
    today = datetime.now().date()
    alert_days = {
        'Monthly': 3,
        'Quarterly': 6,
        'Half-yearly': 15,
        'Annually': 30
    }

    due_alerts = []

    for _, row in df.iterrows():
        domain = row['domain name']
        end_date = pd.to_datetime(row['Zoho_end period']).date()
        frequency = row['billing frequency']
        days_before = alert_days.get(frequency)

        if not days_before:
            continue

        alert_date = end_date - timedelta(days=days_before)
        if today == alert_date:
            due_alerts.append({
                'Domain': domain,
                'End Date': end_date,
                'Frequency': frequency
            })

    if due_alerts:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
        pd.DataFrame(due_alerts).to_excel(temp_file.name, index=False)
        return temp_file.name, due_alerts
    return None, []

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
                file_path, due_alerts = prepare_alerts_file(df)
                if file_path and due_alerts:
                    sender_email = 'janakiram@techprofuse.com'
                    receiver_email = 'kumara@techprofuse.com'
                    subject = "🔔 Zoho Billing Alerts Summary"
                    html_content = f"""
                    <p>Dear Team,</p>
                    <p>Please find attached the billing alerts due today.</p>
                    <p>Regards,<br>Automated Alert System</p>
                    """
                    message = create_email_with_attachment(sender_email, receiver_email, subject, html_content, file_path)
                    result = send_email(service, 'me', message)
                    st.success(f"📬 Email sent with alerts attached. Message ID: {result['id']}")
                    st.dataframe(pd.DataFrame(due_alerts))
                else:
                    st.info("✅ No alerts due today.")

    except Exception as e:
        st.error(f"❌ Error reading the file: {e}")
















