from typing import Any
from django.contrib import admin, messages
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.db.models import Count
from django.utils.html import format_html
from django.urls import reverse
from django.utils.http import urlencode
from jalali_date.admin import ModelAdminJalaliMixin



from .models import BannerImage, Cart, CartItem, Customer, Order, OrderItem, Product, ProductImages

class InventoryFilter(admin.SimpleListFilter):

    LESS_THAN_3 = '<3'
    BETWEEN_3_AND_10 = '3<=10'
    MORE_THAN_10 = '>10'

    title = 'Critical Inventory Status'
    parameter_name = 'inventory'

    def lookups(self, request, model_admin):
        return [
            (InventoryFilter.LESS_THAN_3, 'High'),
            (InventoryFilter.BETWEEN_3_AND_10, 'Meduim'),
            (InventoryFilter.MORE_THAN_10, 'OK'),
        ]
    def queryset(self, request: Any, queryset):
        if self.value() == InventoryFilter.LESS_THAN_3 :
            return queryset.filter(inventory__lt=3)
        if self.value() == InventoryFilter.BETWEEN_3_AND_10 :
            return queryset.filter(inventory__range=(3, 10))
        if self.value() == InventoryFilter.MORE_THAN_10:
            return queryset.filter(inventory__gt=10)
        
        

class BannerImageAdmin(admin.ModelAdmin):
    model = BannerImage
    
class ProductImagesAdmin(admin.TabularInline):
    model = ProductImages        

class ProductAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    inlines = [ProductImagesAdmin]
    list_display = ['id', 'name', 'unit_price', 'inventory_status', 'inventory', 'cover', 'datetime_created']
    list_per_page = 10
    list_editable = ['inventory', 'unit_price']

    list_filter = ['datetime_created', InventoryFilter]
    actions = ['clear_inventory']
    search_fields = ['name']
   
    prepopulated_fields = {
        'slug': ['name', ]
    }


    def inventory_status(self, product : Product):
        if product.inventory < 10 :
            return 'low'
        elif  10 < product.inventory < 50 :
            return 'medium'
        else :
            return 'high' 

  

    @admin.action(description='Clear inventory')
    def clear_inventory(self, request, queryset):
        update_count = queryset.update(inventory=0)
        self.message_user(
            request,
            f'{update_count} of products inventories cleared to zero',
            # messages.ERROR,
        )


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    fields = ['product', 'quantity', 'unit_price']
    extra = 0
    min_num = 1


class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'status','datetime_created', 'num_of_items']
    list_editable = ['status']
    list_per_page = 5
    ordering = ['-datetime_created',]
    inlines =[OrderItemInline]


    def get_queryset(self, request: HttpRequest):
        return super().get_queryset(request).prefetch_related('items').annotate(items_count=Count('items'))


    @admin.display(ordering='items_count', description='# items')
    def num_of_items(self, order):
        return order.items_count


admin.site.register(Product, ProductAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(BannerImage, BannerImageAdmin)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name']
    list_per_page = 10
    ordering = ['user__first_name', 'user__last_name']
    search_fields = ['user__first_name__istartswith', 'user__last_name__istartswith']

    def first_name(self, customer):
        return customer.user.first_name

    def last_name(self, customer):
        return customer.user.last_name
    


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'unit_price']  
    list_per_page = 10
    autocomplete_fields = ['product']


class CartItemInline(admin.TabularInline):
    model =  CartItem
    fields = ['id', 'product', 'quantity']
    extra = 0
    min_num = 1

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'created_at']
    inlines = [CartItemInline]
