from rest_framework import serializers
from .models import *
from django.contrib.auth.password_validation import validate_password


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ('id', 'name', 'email', 'username', 'phone', 'role', 'password')
        extra_kwargs = {'email': {'required': True}, 'username': {'required': True}}

    def create(self, validated_data):
        user = User(
            name=validated_data['name'],
            email=validated_data['email'],
            username=validated_data['username'],
            phone=validated_data['phone'],
            role=validated_data['role'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'name', 'email', 'username', 'phone', 'role')
        read_only_fields = ['role', 'email', 'username']

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])




class ProductSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=True)  # vendor must upload one image during creation

    class Meta:
        model = Product
        fields = ['id', 'vendor', 'name', 'description', 'price', 'available', 'image', 'created_at']
        read_only_fields = ['id', 'vendor', 'created_at']

    def create(self, validated_data):
        return Product.objects.create(**validated_data)

class PublicProductSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'available', 'created_at', 'vendor_name']

class CartItemSerializer(serializers.ModelSerializer):
    product_detail = PublicProductSerializer(source='product', read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'product_detail']

class WishlistItemSerializer(serializers.ModelSerializer):
    product_detail = PublicProductSerializer(source='product', read_only=True)

    class Meta:
        model = WishlistItem
        fields = ['id', 'product', 'product_detail']

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'price', 'vendor']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    is_cancelled = serializers.BooleanField(read_only=True)
    is_returned = serializers.BooleanField(read_only=True)
    cancel_reason = serializers.CharField(allow_blank=True, required=False)
    return_reason = serializers.CharField(allow_blank=True, required=False)

    class Meta:
        model = Order
        fields = ['id', 'user', 'status', 'total', 'created_at','items', 'is_cancelled', 'is_returned', 'cancel_reason', 'return_reason']
        read_only_fields = ['user', 'total', 'status', 'created_at', 'items','is_cancelled', 'is_returned']


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'product', 'user', 'user_name', 'rating', 'comment', 'created_at', 'updated_at']
        read_only_fields = ['user', 'product', 'created_at', 'updated_at']


class VendorOrderItemSerializer(serializers.ModelSerializer):
    order_id = serializers.IntegerField(source='order.id', read_only=True)
    user = serializers.CharField(source='order.user.username', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    class Meta:
        model = OrderItem
        fields = ['id', 'order_id', 'user', 'product_name', 'quantity', 'price', 'fulfillment_status']
        read_only_fields = ['id', 'order_id', 'user', 'product_name', 'quantity', 'price']



