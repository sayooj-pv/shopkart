from django.contrib import admin
from .models import Category, Product, Cart, CartItem, Favorite, Order

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Favorite)
admin.site.register(Order)


