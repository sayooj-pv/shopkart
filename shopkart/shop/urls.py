from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('category/<slug:slug>/', views.product_list, name='category_products'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),

    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:item_id>/', views.cart_remove, name='cart_remove'),

    path('favorites/', views.favorites_list, name='favorites_list'),
    path('favorites/add/<int:product_id>/', views.favorites_add, name='favorites_add'),
    path('favorites/remove/<int:product_id>/', views.favorites_remove, name='favorites_remove'),

    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('checkout/', views.checkout, name='checkout'),
    path('payment/success/', views.payment_success, name='payment_success'),

    path("update-cart/<int:item_id>/<int:qty>/", views.update_cart, name="update_cart"),
    path("favorite/<int:product_id>/", views.toggle_favorite, name="toggle_favorite"),
    path("favorites/", views.favorites_page, name="favorites"),

    path('collections/', views.collections, name='collections'),
    path('collections/<str:name>',views.collectionsview,name="collections"),
    path('collections/<str:cname>/<str:pname>',views.product_list,name="product_list"),
    



]
