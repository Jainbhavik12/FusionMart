from django.urls import path
from .views import *
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('register/', register, name='register'),
    path('v1/users/profile/', user_profile, name='user-profile'),
    path('v1/users/change-password/', change_password, name='change-password'),
    path('v1/vendor/products/', vendor_products_list_create, name='vendor-products-list-create'),
    path('v1/vendor/products/<int:pk>/', vendor_product_detail, name='vendor-product-detail'),
    path('v1/products/', public_product_list, name='public-product-list'),
    path('v1/products/<int:pk>/', public_product_detail, name='public-product-detail'),
    path('v1/cart/', cart_list, name='cart-list'),
    path('v1/cart/add/', cart_add, name='cart-add'),
    path('v1/cart/remove/', cart_remove, name='cart-remove'),
    path('v1/wishlist/', wishlist_list, name='wishlist-list'),
    path('v1/wishlist/add/', wishlist_add, name='wishlist-add'),
    path('v1/wishlist/remove/', wishlist_remove, name='wishlist-remove'),
    path('v1/orders/', user_order_list, name='order-list'),
    path('v1/orders/place/', place_order, name='place-order'),
    path('v1/orders/<int:pk>/', user_order_detail, name='order-detail'),
    path('v1/orders/<int:pk>/checkout/', checkout_order, name='checkout-order'),
    path('v1/products/<int:product_id>/reviews/', product_reviews_list_create, name='product-reviews-list-create'),
    path('v1/products/<int:product_id>/reviews/<int:review_id>/', review_detail_update_delete, name='review-detail-update-delete'),
    path('v1/vendor/order-items/', vendor_order_items_list, name='vendor-order-items-list'),
    path('v1/vendor/order-items/<int:pk>/update/', update_order_item_status, name='update-order-item-status'),
    path('v1/vendor/products/<int:product_id>/images/', upload_product_images, name='upload-product-images'),
    path('v1/orders/<int:pk>/cancel/', cancel_order, name='cancel-order'),
    path('v1/orders/<int:pk>/return/', return_order, name='return-order'),
]

urlpatterns += [
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

