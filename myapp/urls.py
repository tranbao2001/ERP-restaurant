from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),  # Trang chủ
    path('book_table/', views.book_table, name='book_table'),  # Đặt bàn
]
