from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Category, Cart, CartItem, Favorite, Order
from .forms import RegisterForm, CartAddProductForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from django.conf import settings
import razorpay
from django.http import JsonResponse
from django.contrib import messages


# Utility: get or create cart (session-based for anonymous users)
from django.db import transaction

def _get_cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        cart_id = request.session.get('cart_id')
        if cart_id:
            try:
                cart = Cart.objects.get(id=cart_id, user__isnull=True)
            except Cart.DoesNotExist:
                cart = Cart.objects.create()
                request.session['cart_id'] = cart.id
        else:
            cart = Cart.objects.create()
            request.session['cart_id'] = cart.id
    return cart

# Product listing & detail

def product_list(request, slug=None):
    # smartphones = Product.objects.filter(category='smartphone')
    # watches = Product.objects.filter(category='watch')
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)
    if slug:
        category = get_object_or_404(Category, slug=slug)
        products = products.filter(category=category)
    return render(request, 'store/product_list.html',{'category': category, 'categories': categories, 'products': products })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, available=True)
    form = CartAddProductForm()
    return render(request, 'store/product_detail.html', {'product': product, 'form': form})

# Cart operations

def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = _get_cart(request)
    quantity = int(request.POST.get('quantity', 1))
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity += quantity
    else:
        item.quantity = quantity
    item.save()
    return redirect('store:cart_detail')


def cart_remove(request, item_id):
    item = get_object_or_404(CartItem, id=item_id)
    cart_id = request.session.get('cart_id')
    # simple permission: allow remove if session cart or owner
    item.delete()
    return redirect('store:cart_detail')


def cart_detail(request):
    cart = _get_cart(request)
    return render(request, 'store/cart.html', {'cart': cart})

# Favorites

@login_required
def favorites_list(request):
    favs = Favorite.objects.filter(user=request.user).select_related('product')
    return render(request, 'store/favorites.html', {'favs': favs})

@login_required
def favorites_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Favorite.objects.get_or_create(user=request.user, product=product)
    return redirect('store:product_detail', slug=product.slug)

@login_required
def favorites_remove(request, product_id):
    Favorite.objects.filter(user=request.user, product_id=product_id).delete()
    return redirect('store:favorites_list')

def favorites_page(request):
    if not request.user.is_authenticated:
        return redirect('login')

    favorites = request.user.profile.favorites.all()

    return render(request, "store/favorites.html", {
        "favorites": favorites
    })

# Auth

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('store:product_list')
    else:
        form = RegisterForm()
    return render(request, 'store/register.html', {'form': form})

from django.contrib.auth.forms import AuthenticationForm

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('store:product_list')
    else:
        form = AuthenticationForm()
    return render(request, 'store/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('store:product_list')

# Checkout (Razorpay example)

@login_required
@transaction.atomic
def checkout(request):
    cart = _get_cart(request)
    amount = Decimal(cart.total)
    # razorpay expects amount in paise (if INR)
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    razorpay_order = client.order.create(dict(amount=int(amount * 100), currency='INR', payment_capture='1'))

    order = Order.objects.create(user=request.user, razorpay_order_id=razorpay_order['id'], amount=amount)

    context = {
        'cart': cart,
        'order': order,
        'razorpay_order_id': razorpay_order['id'],
        'razorpay_merchant_key': settings.RAZORPAY_KEY_ID,
        'amount_rupees': amount,
    }
    return render(request, 'store/checkout.html', context)

# Payment success callback (simple)
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def payment_success(request):
    # You should verify signature and payment status via razorpay client in production!
    if request.method == 'POST':
        data = request.POST
        # Example: take razorpay_order_id and mark local Order as paid
        razorpay_order_id = data.get('razorpay_order_id')
        order = Order.objects.filter(razorpay_order_id=razorpay_order_id).first()
        if order:
            order.paid = True
            order.save()
        return render(request, 'store/payment_success.html', {'order': order})
    return redirect('store:product_list')

def update_cart(request, item_id, qty):
    item = CartItem.objects.get(id=item_id)
    item.quantity = qty
    item.save()
    return JsonResponse({"success": True})


def toggle_favorite(request, product_id):
    product = Product.objects.get(id=product_id)
    user = request.user

    if product in user.profile.favorites.all():
        user.profile.favorites.remove(product)
        return JsonResponse({"message": "Removed from favorites"})
    else:
        user.profile.favorites.add(product)
        return JsonResponse({"message": "Added to favorites"})

def toggle_favorite(request, product_id):
    product = Product.objects.get(id=product_id)
    user = request.user

    # Check if already fav
    fav_exists = Favorite.objects.filter(user=user, product=product).exists()

    if fav_exists:
        Favorite.objects.get(user=user, product=product).delete()
        return JsonResponse({"message": "removed", "status": "removed"})
    else:
        Favorite.objects.create(user=user, product=product)
        return JsonResponse({"message": "added", "status": "added"})
    
def collections(request):
    return render(request, 'store/collections.html')


def collectionsview(request,name):
  if(Category.objects.filter(name=name,status=0)):
      products=Product.objects.filter(category__name=name)
      return render(request,"store/index.html",{"products":products,"category_name":name})
  else:
    messages.warning(request,"No Such Catagory Found")
    return redirect('collections')

