from django.contrib.auth import update_session_auth_hash
from .serializers import *
from .permissions import IsVendor
from rest_framework.pagination import PageNumberPagination
from .models import *
from django.core.mail import send_mail
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from .serializers import ReviewSerializer
from .permissions import IsReviewOwnerOrReadOnly
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view, permission_classes, parser_classes


@api_view(['POST'])
def register(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'msg': 'Registration Successful'}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    user = request.user
    if request.method == 'GET':
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)

    elif request.method in ['PUT', 'PATCH']:
        serializer = UserProfileSerializer(user, data=request.data, partial=(request.method == 'PATCH'))
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    user = request.user
    serializer = ChangePasswordSerializer(data=request.data)
    if serializer.is_valid():
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({'old_password': ['Wrong password.']}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        # To keep user logged in after password change
        update_session_auth_hash(request, user)
        return Response({'msg': 'Password updated successfully'})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsVendor])
def vendor_products_list_create(request):
    vendor = request.user
    if request.method == 'GET':
        products = Product.objects.filter(vendor=vendor)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(vendor=vendor)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated, IsVendor])
def vendor_product_detail(request, pk):
    vendor = request.user
    try:
        product = Product.objects.get(pk=pk, vendor=vendor)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = ProductSerializer(product)
        return Response(serializer.data)

    elif request.method in ['PUT', 'PATCH']:
        serializer = ProductSerializer(product, data=request.data, partial=(request.method == 'PATCH'))
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
def public_product_list(request):
    '''
    Returns a paginated, optionally filtered list of available products.
    Query params: search (by product name)
    '''
    queryset = Product.objects.filter(available=True)
    search = request.GET.get('search')
    if search:
        queryset = queryset.filter(name__icontains=search)

    paginator = PageNumberPagination()
    paginator.page_size = 10  # or adjust as needed
    result_page = paginator.paginate_queryset(queryset, request)
    serializer = PublicProductSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)

@api_view(['GET'])
def public_product_detail(request, pk):
    try:
        product = Product.objects.get(pk=pk, available=True)
    except Product.DoesNotExist:
        return Response({'detail': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

    serializer = PublicProductSerializer(product)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cart_list(request):
    items = CartItem.objects.filter(user=request.user)
    serializer = CartItemSerializer(items, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cart_add(request):
    user = request.user
    product_id = request.data.get('product')
    quantity = int(request.data.get('quantity', 1))
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({'detail': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)
    item, created = CartItem.objects.get_or_create(user=user, product=product)
    if not created:
        item.quantity += quantity
    else:
        item.quantity = quantity
    item.save()
    return Response({'msg': 'Product added to cart.'}, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cart_remove(request):
    user = request.user
    product_id = request.data.get('product')
    try:
        item = CartItem.objects.get(user=user, product_id=product_id)
        item.delete()
        return Response({'msg': 'Product removed from cart.'})
    except CartItem.DoesNotExist:
        return Response({'detail': 'Cart item not found.'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def wishlist_list(request):
    items = WishlistItem.objects.filter(user=request.user)
    serializer = WishlistItemSerializer(items, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def wishlist_add(request):
    user = request.user
    product_id = request.data.get('product')
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({'detail': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)
    WishlistItem.objects.get_or_create(user=user, product=product)
    return Response({'msg': 'Product added to wishlist.'}, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def wishlist_remove(request):
    user = request.user
    product_id = request.data.get('product')
    try:
        item = WishlistItem.objects.get(user=user, product_id=product_id)
        item.delete()
        return Response({'msg': 'Product removed from wishlist.'})
    except WishlistItem.DoesNotExist:
        return Response({'detail': 'Wishlist item not found.'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def place_order(request):
    user = request.user
    cart_items = CartItem.objects.filter(user=user)
    if not cart_items.exists():
        return Response({"msg": "Cart is empty."}, status=status.HTTP_400_BAD_REQUEST)
    # Calculate total
    total = sum(item.product.price * item.quantity for item in cart_items)
    order = Order.objects.create(user=user, total=total)
    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            vendor=item.product.vendor,
            quantity=item.quantity,
            price=item.product.price
        )
    cart_items.delete()
    serializer = OrderSerializer(order)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_order_list(request):
    orders = Order.objects.filter(user=request.user)
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_order_detail(request, pk):
    try:
        order = Order.objects.get(pk=pk, user=request.user)
    except Order.DoesNotExist:
        return Response({"msg": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    serializer = OrderSerializer(order)
    return Response(serializer.data)


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def checkout_order(request, pk):
    try:
        order = Order.objects.get(pk=pk, user=request.user)
    except Order.DoesNotExist:
        return Response({'detail': 'Order not found.'}, status=404)

    if order.payment_status == "paid":
        return Response({'msg': 'Order is already paid.'})

    # Simulate a payment gateway process here.
    # In a real app, integrate with Stripe, Razorpay, etc.
    order.payment_status = "paid"
    order.save()
    subject_user = "Your FusionMart Order Payment Successful!"
    message_user = f"Hi {order.user.name},\n\nYour order #{order.id} payment was received successfully. We will notify you when your order ships!"
    send_mail(subject_user, message_user, None, [order.user.email])

    # Email to vendor(s) -- one for each product's vendor
    subject_vendor = "Order Placed for Your Product on FusionMart"
    for item in order.items.all():
        vendor_email = item.vendor.email
        vendor_message = f"Hello {item.vendor.name},\n\nA user has paid for order #{order.id} including your product: {item.product.name}. Please process this order."
        send_mail(subject_vendor, vendor_message, None, [vendor_email])

    return Response({'msg': 'Payment successful! Email sent to user and vendors.', 'order_id': order.id})




def user_has_purchased_product(user, product):
    return OrderItem.objects.filter(order__user=user, product=product).exists()

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def product_reviews_list_create(request, product_id):
    try:
        product = Product.objects.get(id=product_id, available=True)
    except Product.DoesNotExist:
        return Response({'detail': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        reviews = Review.objects.filter(product=product).order_by('-created_at')
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        if not request.user.is_authenticated:
            return Response({'detail': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)
        if not user_has_purchased_product(request.user, product):
            return Response({'detail': 'You must purchase this product before reviewing.'}, status=status.HTTP_403_FORBIDDEN)

        existing_review = Review.objects.filter(product=product, user=request.user).first()
        if existing_review:
            return Response({'detail': 'You have already reviewed this product.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, product=product)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated, IsReviewOwnerOrReadOnly])
def review_detail_update_delete(request, product_id, review_id):
    try:
        review = Review.objects.get(id=review_id, product_id=product_id)
    except Review.DoesNotExist:
        return Response({'detail': 'Review not found.'}, status=status.HTTP_404_NOT_FOUND)

    if not IsReviewOwnerOrReadOnly().has_object_permission(request, None, review):
        return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method in ['PUT', 'PATCH']:
        serializer = ReviewSerializer(review, data=request.data, partial=(request.method == 'PATCH'))
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        review.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsVendor])
def vendor_order_items_list(request):
    order_items = OrderItem.objects.filter(vendor=request.user).order_by('-id')
    serializer = VendorOrderItemSerializer(order_items, many=True)
    return Response(serializer.data)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsVendor])
def update_order_item_status(request, pk):
    try:
        order_item = OrderItem.objects.get(id=pk, vendor=request.user)
    except OrderItem.DoesNotExist:
        return Response({'detail': 'Order item not found.'}, status=404)

    status_value = request.data.get('fulfillment_status')
    if status_value not in dict(OrderItem.fulfillment_status_choices):
        return Response({'detail': 'Invalid status.'}, status=400)

    order_item.fulfillment_status = status_value
    order_item.save()
    serializer = VendorOrderItemSerializer(order_item)
    return Response(serializer.data)



@api_view(['POST'])
@permission_classes([IsAuthenticated, IsVendor])
@parser_classes([MultiPartParser, FormParser])
def upload_product_images(request, product_id):
    user = request.user
    try:
        product = Product.objects.get(id=product_id, vendor=user)
    except Product.DoesNotExist:
        return Response({'detail': 'Product not found.'}, status=404)

    images_count = product.images.count()
    files = request.FILES.getlist('images')
    if images_count + len(files) > 4:
        return Response({'detail': 'Maximum 4 images per product allowed.'}, status=400)

    for file in files:
        ProductImage.objects.create(product=product, image=file)

    return Response({'msg': 'Images uploaded successfully.'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_order(request, pk):
    try:
        order = Order.objects.get(pk=pk, user=request.user)
    except Order.DoesNotExist:
        return Response({'detail': 'Order not found.'}, status=404)

    if order.status == 'delivered':
        return Response({'detail': 'Order already delivered, please request a return instead.'}, status=400)
    if order.is_cancelled:
        return Response({'detail': 'Order is already cancelled.'}, status=400)

    reason = request.data.get('reason', '')
    order.is_cancelled = True
    order.cancel_reason = reason
    order.status = 'cancelled'
    order.save()

    return Response({'msg': 'Order cancelled successfully.'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def return_order(request, pk):
    try:
        order = Order.objects.get(pk=pk, user=request.user)
    except Order.DoesNotExist:
        return Response({'detail': 'Order not found.'}, status=404)

    if order.status != 'delivered':
        return Response({'detail': 'Order not delivered yet, cannot return.'}, status=400)
    if order.is_returned:
        return Response({'detail': 'Order is already returned.'}, status=400)

    reason = request.data.get('reason', '')
    order.is_returned = True
    order.return_reason = reason
    order.status = 'returned'  # you can add to STATUS_CHOICES
    order.save()

    return Response({'msg': 'Return request successful.'})




