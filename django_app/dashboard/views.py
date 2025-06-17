from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template.loader import render_to_string
from collections import defaultdict, OrderedDict
from django.contrib import messages
from weasyprint import HTML
import datetime
import json
import requests
import tempfile

# Utility to fetch invoices from FastAPI
def get_invoices_from_fastapi(user_id):
    try:
        print(f"📱 Fetching invoices from FastAPI for user {user_id}")
        response = requests.get(f"http://127.0.0.1:8005/invoices/{user_id}")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"⚠️ FastAPI returned status {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Exception in get_invoices_from_fastapi: {e}")
    return []

# Trigger invoice fetch via FastAPI
def trigger_email_fetch(email_user, email_pass, user_id):
    try:
        print(f"🚀 Triggering fetch for {email_user} (user_id={user_id})")
        response = requests.post("http://127.0.0.1:8005/fetch_invoices/", json={
            "email_user": email_user,
            "email_pass": email_pass,
            "user_id": user_id
        })
        print(f"✅ FastAPI POST response: {response.status_code}")
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"❌ Error triggering fetch: {e}")
        return False

# Dashboard context builder
def get_dashboard_context(request):
    user = request.user
    today = datetime.date.today()
    this_month = today.month
    this_year = today.year
    last_month_date = today.replace(day=1) - datetime.timedelta(days=1)
    last_month = last_month_date.month
    last_year = last_month_date.year

    selected_month_raw = request.GET.get("month")
    selected_platform = request.GET.get("platform", "")

    if selected_month_raw:
        try:
            selected_month_date = datetime.datetime.strptime(selected_month_raw, "%Y-%m")
            selected_month = selected_month_date.month
            selected_year = selected_month_date.year
        except ValueError:
            selected_month, selected_year = this_month, this_year
    else:
        selected_month, selected_year = this_month, this_year

    fastapi_invoices = get_invoices_from_fastapi(user.id)

    relevant_invoices = []
    for invoice in fastapi_invoices:
        try:
            invoice_date = datetime.date.fromisoformat(invoice["date_fetched"][:10])
            if (invoice_date.month, invoice_date.year) in [(this_month, this_year), (last_month, last_year)]:
                relevant_invoices.append(invoice)
        except:
            continue

    filtered_invoices = []
    for invoice in relevant_invoices:
        try:
            invoice_date = datetime.date.fromisoformat(invoice["date_fetched"][:10])
            amount = float(invoice.get("amount", 0))
        except:
            continue
        if (invoice_date.month != selected_month or invoice_date.year != selected_year) or \
           (selected_platform and selected_platform.lower() not in invoice.get("platform", "").lower()):
            continue
        invoice.update({
            "amount": amount,
            "date": invoice["date_fetched"][:10],
            "item_name": invoice.get("platform", "Other")
        })
        filtered_invoices.append(invoice)

    # Aggregation
    daily_spend = OrderedDict()
    platform_spend = defaultdict(float)
    platform_count = defaultdict(int)

    for invoice in filtered_invoices:
        try:
            day = datetime.date.fromisoformat(invoice["date"]).strftime("%d %b")
            daily_spend[day] = daily_spend.get(day, 0) + invoice["amount"]
        except:
            continue
        platform = invoice.get("platform", "Other").capitalize()
        if platform not in ["Amazon", "Flipkart", "Zomato", "Swiggy", "Zepto"]:
            platform = "Other"
        platform_spend[platform] += invoice["amount"]
        platform_count[platform] += 1

    budget_limit = getattr(user.profile, "budget_limit", 0)
    current_spend = sum(i["amount"] for i in filtered_invoices)
    overspent = current_spend > budget_limit

    # Alerts
    budget_alerts = []
    for platform, amount in platform_spend.items():
        if budget_limit and amount > 0.9 * budget_limit:
            budget_alerts.append(f"⚠️ You're at 90% of your {platform} budget!")
        elif amount < 0.5 * budget_limit:
            budget_alerts.append(f"✅ Great! You’ve spent less on {platform} this month than usual.")

    last_month_invoices = [
        i for i in relevant_invoices
        if datetime.date.fromisoformat(i["date_fetched"][:10]).month == last_month and
           datetime.date.fromisoformat(i["date_fetched"][:10]).year == last_year
    ]
    last_month_spend = sum(float(i["amount"]) for i in last_month_invoices)
    spend_diff = current_spend - last_month_spend
    percent_change = (spend_diff / last_month_spend * 100) if last_month_spend else 0

    smart_insights = [
        f"You ordered from {platform} {count} times this month, averaging ₹{round(platform_spend[platform]/count,2)} per order."
        for platform, count in platform_count.items()
    ]

    print(f"📊 Daily Spend Data: {daily_spend}")

    return {
        "budget_limit": budget_limit,
        "current_spend": current_spend,
        "overspent": overspent,
        "daily_spend": json.dumps(daily_spend),
        "selected_month": selected_month_raw or today.strftime("%Y-%m"),
        "selected_platform": selected_platform,
        "platform_spend_dict": dict(platform_spend),
        "filtered_orders": filtered_invoices,
        "last_month_spend": last_month_spend,
        "spend_diff": round(spend_diff, 2),
        "percent_change": round(percent_change, 1),
        "budget_alerts": budget_alerts,
        "smart_insights": smart_insights,
    }

@login_required
def dashboard(request):
    context = get_dashboard_context(request)
    return render(request, "dashboard.html", context)

@login_required
def download_pdf_report(request):
    context = get_dashboard_context(request)
    html_string = render_to_string("pdf_template.html", context)
    html = HTML(string=html_string)
    with tempfile.NamedTemporaryFile(delete=True, suffix=".pdf") as pdf_file:
        html.write_pdf(pdf_file.name)
        pdf_file.seek(0)
        response = HttpResponse(pdf_file.read(), content_type="application/pdf")
        response['Content-Disposition'] = 'inline; filename="monthly_report.pdf"'
        return response

@login_required
def fetch_invoices_view(request):
    if request.method == "POST":
        email_user = request.POST.get("email")
        email_pass = request.POST.get("password")
        user_id = request.user.id

        if email_user and email_pass:
            messages.info(request, "⏳ Fetching invoices... This may take a few seconds.")
            print(f"📬 Fetch form submitted by {email_user}")
            success = trigger_email_fetch(email_user, email_pass, user_id)
            if success:
                messages.success(request, "✅ Invoice fetch complete! You can check now.")
            else:
                messages.error(request, "❌ Failed to fetch invoices. Please check credentials.")
        else:
            messages.error(request, "❌ Email or password missing.")
    else:
        messages.error(request, "❌ Invalid request method.")

    return redirect("dashboard")
