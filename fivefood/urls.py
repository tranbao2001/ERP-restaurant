from django.contrib import admin
from django.urls import path, include
from myapp import views
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from myapp.views import DishViewSet, CategoryViewSet, TableViewSet

router = DefaultRouter()
router.register(r'dishes', DishViewSet, basename='dishes')
router.register(r'categories', CategoryViewSet, basename='categories')
router.register(r'tables', TableViewSet, basename='tables')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('contact/', views.contact_us, name='contact'),
    path('about/', views.about, name='about'),
    path('team/', views.team_members, name='team'),
    path('dishes/', views.all_dishes, name='all_dishes'),
    path('register/', views.register, name='register'),
    path('check_user_exists/', views.check_user_exists, name='check_user_exist'),
    path('login/', views.signin, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.user_logout, name='logout'),
    path('dish/<int:id>/', views.single_dish, name='dish'),
    path('paypal/', include('paypal.standard.ipn.urls')),
    path('payment_done/', views.payment_done, name='payment_done'),
    path('payment_cancel/', views.payment_cancel, name='payment_cancel'),
    path('book_table/', views.book_table, name='book_table'),
    path('menu/', views.menu, name='menu'),
    path('edit-table/<int:table_id>/', views.edit_table, name='edit_table'),
    path('delete-table/<int:table_id>/',
         views.delete_table, name='delete_table'),
    path('api/', include(router.urls)),
    path('api/book_table/', views.book_table_api, name='book_table_api'),
    path('api/cancel_table/<int:table_id>/',
         views.cancel_table_api, name='cancel_table_api'),
    path('api/edit_table/<int:table_id>/',
         views.edit_table_api, name='edit_table_api'),
]+static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
