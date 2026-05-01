from django.urls import path
from . import views

urlpatterns = [
    path('broker/stats/', views.broker_dashboard_stats, name='broker_stats'),
    path('broker/performance/', views.property_performance, name='property_performance'),
    path('broker/views-over-time/', views.views_over_time, name='views_over_time'),
    path('broker/inquiries-over-time/', views.inquiries_over_time, name='inquiries_over_time'),
]
