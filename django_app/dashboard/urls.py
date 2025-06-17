from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),  # Main dashboard
    path('fetch-invoices/', views.fetch_invoices_view, name='fetch_invoices'),  # Trigger invoice fetching
    path('download_pdf/', views.download_pdf_report, name='download_pdf_report'),  # PDF report download
]
