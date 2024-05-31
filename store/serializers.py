from decimal import Decimal
from rest_framework import serializers
from django.core.validators import MinValueValidator
from django.utils.text import slugify
from django.db import transaction
from store.models import Cart, CartItem, Customer, Order, OrderItem, Product




class ProductSerializer(serializers.ModelSerializer):
    title = serializers.CharField(max_length=255, source='name')
    price = serializers.DecimalField(max_digits=255, decimal_places=2, source='unit_price')
    

    class Meta:
        model = Product
        fields = ['id', 'title', 'price', 'inventory', 'description', 'cover']



    #extra validation for is_valid method
    def validate(self, data):
        if  len(data['name']) < 6:
            raise serializers.ValidationError('product title should be at least 6 characters')
        return data

    def create(self, validated_data):
        product = Product(**validated_data)
        product.slug = slugify(product.name)
        product.save()
        return
    


class CartProductSerializer(serializers.ModelSerializer):

    class Meta:
        model= Product
        fields = ['id', 'name', 'unit_price']


class UpdateCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['quantity']



class AddCartItemSerializer(serializers.ModelSerializer):

    class Meta: 
        model = CartItem
        fields = ['id', 'product', 'quantity']

    def create(self, validated_data):
        cart_id = self.context['cart_pk']

        product = validated_data.get('product')
        quantity = validated_data.get('quantity')

        try:
            cart_item =CartItem.objects.get(cart_id=cart_id, product_id=product.id)
            cart_item.quantity += quantity
            cart_item.save()

        except CartItem.DoesNotExist:
            cart_item = CartItem.objects.create(cart_id=cart_id, **validated_data)

        self.instance = cart_item
        return cart_item         


class CartItemSerializer(serializers.ModelSerializer):
    product = CartProductSerializer()
    item_total = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity','item_total']

    def get_item_total(self, cart_item):
        return cart_item.quantity * cart_item.product.unit_price
    

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

   
    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_price']
        read_only_fields= ['id']

    def get_total_price(self, cart):
       return sum([item.quantity * item.product.unit_price for item in cart.items.all()])
    

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'user', 'birth_date']
        read_only_fields = ['user']



class OrderProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields =['id', 'name', 'unit_price']



class OrderCustomerSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=255, source='user.first_name')
    last_name = serializers.CharField(max_length=255, source='user.last_name')
  
    class Meta:
        model = Customer
        fields = ['id', 'first_name', 'last_name']



class OrderItemSerializer(serializers.ModelSerializer):
    product = OrderProductSerializer()
    class Meta:
         model = OrderItem
         fields = ['id', 'product', 'quantity', 'unit_price' ]            



class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    
    class Meta:
        model = Order
        fields = ['id', 'customer', 'status', 'datetime_created', 'items' ]




class OrderForAdminSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    customer = OrderCustomerSerializer()
    
    class Meta:
        model = Order
        fields = ['id', 'customer', 'status', 'datetime_created', 'items' ]


class OrderUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['status']         


class OrderCreateSerializer(serializers.Serializer):
    cart_id = serializers.UUIDField()

    def validate_cart_id(self, cart_id):
          

         if not Cart.objects.filter(id=cart_id).exists():
            raise serializers.ValidationError('There is no cart with this cart id')

         if CartItem.objects.filter(cart_id=cart_id).count() == 0:
             raise serializers.ValidationError('Your cart is empty, please add some products')
         return cart_id
    
    def save(self, **kwargs):
        with transaction.atomic():
            cart_id = self.validated_data['cart_id']
            user_id = self.context['user_id']
            customer = Customer.objects.get(user_id=user_id)

            order = Order()
            order.customer = customer
            order.save()

            cart_items = CartItem.objects.select_related('product').filter(cart_id=cart_id)

            order_items = [
                OrderItem(
                    order=order,
                    product=cart_item.product,
                    unit_price=cart_item.product.unit_price,
                    quantity=cart_item.quantity,
                ) for cart_item in cart_items
            ]


            OrderItem.objects.bulk_create(order_items)   

            Cart.objects.get(id=cart_id).delete()

            return order
