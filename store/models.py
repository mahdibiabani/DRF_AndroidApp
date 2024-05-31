from django.utils import timezone
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from uuid import uuid4
from ckeditor.fields import RichTextField


class BannerImage(models.Model):
    banner = models.ImageField(upload_to='banner/', blank=True)

class Product(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField()
    description = RichTextField()
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)
    inventory = models.IntegerField(validators=[MinValueValidator(0)])
    cover = models.ImageField(upload_to='cover/', blank=True)
    datetime_created = models.DateTimeField(default=timezone.now)
    datetime_modified = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.name


class ProductImages(models.Model):
    images = models.ImageField(upload_to="product-images", default="product.jpg")
    product = models.ForeignKey(Product, related_name="product_images", on_delete=models.SET_NULL, null=True)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Product Images"



class Customer(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,)
    phone_number = models.CharField(max_length=255)
    
    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name}'

class UnpaidOrderManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset().filter(status=Order.ORDER_STATUS_UNPAID)
    
# class OrderManager(models.Manager):
#     def get_by_status(self, status):
#         if status in [Order.ORDER_STATUS_PAID, Order.ORDER_STATUS_UNPAID, Order.ORDER_STATUS_CANCELED]:
#             return super().get_queryset().filter(status=status)
#         return super().get_queryset()


class Order(models.Model):
    ORDER_STATUS_PAID = 'p'
    ORDER_STATUS_UNPAID = 'u'
    ORDER_STATUS_CANCELED = 'c'
    ORDER_STATUS = [
        (ORDER_STATUS_PAID,'Paid'),
        (ORDER_STATUS_UNPAID,'Unpaid'),
        (ORDER_STATUS_CANCELED,'Canceled'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='orders')
    datetime_created = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=1, choices=ORDER_STATUS, default=ORDER_STATUS_UNPAID)

    objects = models.Manager()
    unpaid_orders = UnpaidOrderManager()

    def __str__(self):
        return f'Order id={self.id}'

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='order_items')
    quantity = models.PositiveSmallIntegerField()
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        unique_together = [['order', 'product']]


class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    created_at = models.DateTimeField(auto_now_add=True)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = [['cart', 'product']]        