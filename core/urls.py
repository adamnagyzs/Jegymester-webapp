from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Public views (no login required)
    path('', views.home, name='home'),
    path('movies/', views.movie_list, name='movie_list'),
    path('movies/<int:pk>/', views.movie_detail, name='movie_detail'),
    path('screenings/', views.screening_list, name='screening_list'),
    path('screenings/<int:pk>/', views.screening_detail, name='screening_detail'),
    
    # Ticket purchase (login optional for guests)
    path('screenings/<int:pk>/buy/', views.buy_ticket, name='buy_ticket'),
    
    # Ticket lookup (public)
    path('ticket-lookup/', views.ticket_lookup, name='ticket_lookup'),
    
    # User ticket management (login required)
    path('my-tickets/', views.my_tickets, name='my_tickets'),
    path('tickets/<int:pk>/cancel/', views.cancel_ticket, name='cancel_ticket'),
    
    # Cashier views
    path('cashier/', views.cashier_dashboard, name='cashier_dashboard'),
    path('cashier/verify/<str:ticket_code>/', views.verify_ticket, name='verify_ticket'),
    path('cashier/sell/<int:screening_pk>/', views.cashier_sell_ticket, name='cashier_sell_ticket'),
    
    # Admin views
    path('management/', views.admin_dashboard, name='admin_dashboard'),
    path('management/movies/', views.admin_movie_list, name='admin_movie_list'),
    path('management/movies/add/', views.admin_movie_add, name='admin_movie_add'),
    path('management/movies/<int:pk>/edit/', views.admin_movie_edit, name='admin_movie_edit'),
    path('management/movies/<int:pk>/delete/', views.admin_movie_delete, name='admin_movie_delete'),
    path('management/screenings/', views.admin_screening_list, name='admin_screening_list'),
    path('management/screenings/add/', views.admin_screening_add, name='admin_screening_add'),
    path('management/screenings/<int:pk>/edit/', views.admin_screening_edit, name='admin_screening_edit'),
    path('management/users/', views.admin_user_list, name='admin_user_list'),
    path('management/users/<int:pk>/edit/', views.admin_user_edit, name='admin_user_edit'),
]
