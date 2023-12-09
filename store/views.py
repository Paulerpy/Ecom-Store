from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
import json
import datetime
from .models import *
from .utils import cookieCart, cartData
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

import stripe
# Create your views here.

def store(request):
  
  data = cartData(request)

  cartItems = data['cartItems']
      
  products = Product.objects.all()
  context = {'products': products, 'cartItems': cartItems}
  return render(request, 'store/store.html', context)

def cart(request):

  data = cartData(request)

  items = data['items']
  order = data['order']
  cartItems = data['cartItems']

  context = {'items': items, 'order': order, 'cartItems': cartItems}
  return render(request, 'store/cart.html', context)

def checkout(request):
  data = cartData(request)

  items = data['items']
  order = data['order']
  cartItems = data['cartItems']
    
  context = {'items': items, 'order': order, 'cartItems': cartItems}
  return render(request, 'store/checkout.html', context)

def updateItem(request):

  data = json.loads(request.body)
  productId = data['productId']
  action = data['action']

  customer = request.user.customer
  product = Product.objects.get(id=productId)
  order, created = Order.objects.get_or_create(customer=customer, complete=False)

  orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

  if action == 'add':
    orderItem.quantity += 1
  elif action == 'remove':
    orderItem.quantity -= 1
  
  orderItem.save()

  if orderItem.quantity <= 0:
    orderItem.delete()

  return JsonResponse('Item was added', safe=False)

def processOrder(request):
  transaction_id = datetime.datetime.now().timestamp()

  data = json.loads(request.body)

  if request.user.is_authenticated:
    customer = request.user.customer
    order, created = Order.objects.get_or_create(customer=customer, complete=False)
    total = float(data['form']['total'])
    order.transaction_id = transaction_id  

    
  else:   
    print('User is not logged in...')

    print('COOKIES', request.COOKIES)
    name = data['form']['name']
    email = data['form']['email']

    cookieData = cookieCart(request)
    items = cookieData['items']

    customer, created = Customer.objects.get_or_create(
      email=email
    )

    customer.name = name 
    customer.save()

    order = Order.objects.create(
      customer=customer,
      complete=False
    )

    for item in items:
      product = Product.objects.create(
        product=product,
        order=order,
        quantity=item['quantity']
      )

  if total == order.get_cart_total:
    order.complete = True
  order.save()  

  if order.shipping == True:
    ShippingAddress.objects.create(
      customer=customer,
      order=order,
      address=data['shipping']['address'],
      city=data['shipping']['city'],
      state=data['shipping']['state'],
      zipcode=data['shipping']['zipcode'],
    )
    
  return JsonResponse('Payment Complete', safe=False)

@csrf_exempt
def stripe_config(request):
  if request.method == 'GET':
    stripe_config = {'publicKey': settings.STRIPE_PUBLISHABLE_KEY}
    return JsonResponse(stripe_config, safe=False)


@csrf_exempt
def create_checkout_session(request):
  domain_url = 'http://127.0.0.1:8000/'
  stripe.api_key = settings.STRIPE_SECRET_KEY

  try:
    checkout_session = stripe.checkout.Session.create(
      success_url=domain_url + 'success?session_id={CHECKOUT_SESSION_ID}',
      cancel_url=domain_url + 'cancelled/',
      payment_method_types= ['card'],
      mode='payment',
      line_items= [
        {
          'quantity': 1,
          'price': 'price_1OK5cYL4dnedMSOxl6surECP',
        }
      ]
    )
    return JsonResponse({'sessionId': checkout_session['id']})
  except Exception as e: 
    return JsonResponse({'error': str(e)})


@csrf_exempt
def stripe_webhook(request):
  payload = request.body
  stripe.api_key = settings.STRIPE_SECRET_KEY
  event = None

  try:
    event = stripe.Event.construct_from(
      json.loads(payload), stripe.api_key
    )
  except ValueError as e:
    return HttpResponse(status=400)
  
  if event.type == 'payment_intent.succeeded':
    payment_intent = event.data.object
  elif event.type == 'payment_method.attached':
    payment_intent = event.data.object
  else:
    print('Unhandled event type {}'.format(event.type))

  return HttpResponse(status=200)

def successView(request):
  return render(request, 'store/success.html')

def cancelledView(request):
  return render(request, 'store/cancelled.html')


  
