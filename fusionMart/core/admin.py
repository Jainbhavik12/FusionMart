from django.contrib import admin
from django.utils.html import format_html

from .models import *

# Register your models here.
admin.site.register(User)
admin.site.register(Product)
admin.site.register(CartItem)
admin.site.register(WishlistItem)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Review)

