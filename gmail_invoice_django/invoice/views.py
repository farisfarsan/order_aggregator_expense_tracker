import os
import requests
from django.shortcuts import redirect, render
from django.http import HttpResponse
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from .email_fetcher import fetch_invoice_summary

# Enable insecure HTTP for local testing
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Path to OAuth credential.json inside the invoice app
CLIENT_SECRETS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'credential.json'
)

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


# ✅ Dashboard view
def dashboard(request):
    return render(request, 'invoice/dashboard.html')


# ✅ Landing page
def index(request):
    return render(request, 'invoice/index.html')


# ✅ Sync Gmail (triggers OAuth)
def sync_gmail(request):
    print("🔄 Sync request initiated")
    return redirect('/authorize/')


# ✅ Start Gmail OAuth2 flow
def authorize(request):
    print("🔐 Starting Gmail OAuth flow")
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=request.build_absolute_uri('/oauth2callback/')
    )

    auth_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )

    request.session['state'] = state
    print(f"➡️ Redirecting to Google OAuth: {auth_url}")
    return redirect(auth_url)


# ✅ Callback after Google login
def oauth2callback(request):
    print("🌀 Returned from Google OAuth")
    state = request.session.get('state')
    if not state:
        return redirect('/')

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=request.build_absolute_uri('/oauth2callback/')
    )
    flow.fetch_token(authorization_response=request.build_absolute_uri())

    creds = flow.credentials
    request.session['credentials'] = {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes
    }

    print("✅ Tokens stored in session")
    return redirect('/summary/')


# ✅ Fetch Gmail invoices and push to FastAPI
def summary(request):
    creds_dict = request.session.get('credentials')
    if not creds_dict:
        return redirect('/')

    credentials = Credentials(**creds_dict)
    service = build('gmail', 'v1', credentials=credentials)

    # ✅ Fix: Ensure user_id is an integer, not None
    user_id = 1  # Hardcoded fallback until auth is added

    print("📬 Starting Gmail invoice fetch...")
    print(f"🧠 Fetching invoices for user_id: {user_id}")

    try:
        summary_text, count = fetch_invoice_summary(service, user_id=user_id)
        print(f"✅ Invoice fetching complete. Pushed {count} invoices to FastAPI.")
    except Exception as e:
        print("❌ Error during Gmail fetch:", e)
        return HttpResponse(f"<pre>Error: {str(e)}</pre>", status=500)

    return HttpResponse(f"<pre>{summary_text}\n\n✅ Pushed {count} invoices</pre>")
