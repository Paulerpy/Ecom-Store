from django.urls import path
from .views import *

urlpatterns = [
  path('', store, name='store'),
  path('cart/', cart, name='cart'),
  path('checkout/', checkout, name='checkout'),
  path('update_item/', updateItem, name='update_item'),
  path('process_order/', processOrder, name='process_order'),
  path('config/', stripe_config, name='stripe_config'),
  path('create_checkout_session/', create_checkout_session, name='create_checkout_session'),
  path('success/', successView, name='success'),
  path('cancelled/', successView, name='cancelled'),
  path('webhook/', stripe_webhook)
]