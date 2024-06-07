from django.urls import path, include
from rest_framework_nested import routers
from . import views

app_name = 'store'

router = routers.DefaultRouter()

router.register('products', views.ProductViewSet, basename='product') # product-list | product-detail

router.register('carts', views.CartViewSet, basename='cart')
router.register('customers', views.CustomerViewSet, basename='customer')
router.register('orders', views.OrderViewSet, basename='order')



cart_items_router = routers.NestedDefaultRouter(router, 'carts', lookup='cart')
cart_items_router.register('items', views.CartItemViewSet, basename='cart-items')

# urlpatterns = router.urls + cart_items_router.urls


urlpatterns = [

    path('', include(
                router.urls
                +
                cart_items_router.urls
               )),
    path('orders/<int:order_id>/pay/', views.OrderPayView.as_view(), name='order-pay'),
    path('orders/verify', views.OrderVerifyView.as_view(), name='order_verify')
]