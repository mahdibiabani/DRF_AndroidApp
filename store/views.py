import requests
import json 
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Prefetch
from django.urls import reverse

from rest_framework.response import Response
from rest_framework import status


from rest_framework.filters import OrderingFilter, SearchFilter

from rest_framework.viewsets import ModelViewSet
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, DestroyModelMixin
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny 
#ReadOnlyModelViewSet   instead of     ModelViewSet | for only read and get objects without deleting and updating
from django_filters.rest_framework import DjangoFilterBackend

from store import zarinpal
from store.models import BannerImage, Cart, CartItem, Customer, Order, OrderItem, Product
from store.paginations import DefaultPagination
from store.permissions import CustomDjangoModelPermissions, IsAdminOrReadOnly
from store.serializers import AddCartItemSerializer, BannerImageSerializer, CartItemSerializer, CartSerializer, CustomerSerializer, OrderCreateSerializer, OrderForAdminSerializer, OrderItemSerializer, OrderSerializer, OrderUpdateSerializer, ProductSerializer, UpdateCartItemSerializer
from .filters import ProductFilter
from .signals import order_created
from rest_framework.views import APIView
from config import settings



#class-based view
#productlist and product detail both together including post put patch delete-------------------------------------------------

class BannerImageViewSet(ModelViewSet):
     serializer_class = BannerImageSerializer
     permission_classes  = [IsAdminOrReadOnly]
     queryset = BannerImage.objects.all()

     

class ProductViewSet(ModelViewSet):

     serializer_class = ProductSerializer
     filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
     ordering_fields = ['name', 'unit_price', 'inventory']
     search_fields = ['name']
    
     filterset_class = ProductFilter
     permission_classes = [IsAdminOrReadOnly]
     queryset = Product.objects.all()
      
     def get_serializer_context(self):
          return {'request': self.request}
     
     def destroy(self, request, pk):
          product = get_object_or_404(Product.objects.all(), pk=pk)
          if product.order_items.count() > 0:
              return Response({'error': 'there is some orderitems including this product'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
          product.delete()
          return Response(status=status.HTTP_204_NO_CONTENT)
#--------------------------------------------------------------------------------------------------



class CartItemViewSet(ModelViewSet):
     http_method_names = ['get', 'post', 'patch', 'delete']

     
     def get_queryset(self):
          cart_pk = self.kwargs['cart_pk']
          return CartItem.objects.select_related('product').filter(cart_id=cart_pk).all()


     def get_serializer_class(self):
          if self.request.method == 'POST':
               return AddCartItemSerializer
          elif self.request.method == 'PATCH':
               return UpdateCartItemSerializer
          return CartItemSerializer
     
     def get_serializer_context(self):
          return{'cart_pk': self.kwargs['cart_pk']}


class CartViewSet(CreateModelMixin,
                   RetrieveModelMixin,
                   DestroyModelMixin,
                   GenericViewSet):
     serializer_class = CartSerializer
     queryset = Cart.objects.prefetch_related('items__product').all()
     lookup_value_regex = '[0-9a-fA-F]{8}\-?[0-9a-fA-F]{4}\-?[0-9a-fA-F]{4}\-?[0-9a-fA-F]{4}\-?[0-9a-fA-F]{12}'

class CustomerViewSet(ModelViewSet):
     serializer_class = CustomerSerializer   
     queryset = Customer.objects.all()
     permission_classes = [IsAdminUser]

     @action(detail=False, methods=['GET', 'PUT'], permission_classes=[IsAuthenticated])
     def me(self, request):
          user_id = request.user.id
          customer = Customer.objects.get(user_id=user_id)
          if request.method == 'GET':
              serializer = CustomerSerializer(customer)
              return Response(serializer.data)
          elif request.method == 'PUT':
               serializer = CustomerSerializer(customer, data=request.data)
               serializer.is_valid(raise_exception=True)
               serializer.save()
               return Response(serializer.data)
          



class OrderViewSet(ModelViewSet):

     http_method_names = ['get', 'post', 'delete', 'patch', 'options','head']
     
     def get_permissions(self):
          if self.request.method in ['PATCH', 'DELETE']:
               return [IsAdminUser()]
          return [IsAuthenticated()]
          

     def get_queryset(self):
          queryset = Order.objects.prefetch_related(
               Prefetch(
                    'items', queryset=OrderItem.objects.select_related('product'),
                    )
          ).select_related('customer__user').all()
          
          user = self.request.user

          if user.is_staff:
               return queryset
          
          return queryset.filter(customer__user_id=user.id)
     

     def get_serializer_class(self):
          if self.request.method == 'POST':
               return OrderCreateSerializer
          
          if self.request.method == 'PATCH':
               return OrderUpdateSerializer
          
          if self.request.user.is_staff:
               return OrderForAdminSerializer
          return OrderSerializer 

          
     
     def get_serializer_context(self):
          return {'user_id': self.request.user.id}
     

     def create(self, request, *args, **kwargs):
          create_order_serializer  = OrderCreateSerializer(data=request.data,
                       context={'user_id': self.request.user.id},                                    
                    )
          create_order_serializer.is_valid(raise_exception=True)
          created_order = create_order_serializer.save()

          order_created.send_robust(self.__class__, order=created_order)

          serializer= OrderSerializer(created_order)
          return Response(serializer.data)

          


     def destroy(self, request, pk):
        order = Order.objects.prefetch_related('items').get(pk=pk)

        if order.items.all().count() > 0:
            return Response({
                'error':
                    'There is some order items including this order.'
                    'Please remove them first.'},
                    status=status.HTTP_405_METHOD_NOT_ALLOWED
                    )

        order.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
     


#zarinpall

class OrderPayView(APIView):
    http_method_names = ['get', 'option', 'head']
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)

        if order.status == 'p':
            return Response('This order has been paid!')

        request.session['order_pay'] = {
            'order_id': order.id,
        }

        request.session['order_id'] = {
            'order_id': int(order_id),
        }

        req_data = {
            "MerchantID": settings.ZARINPALL_MERCHANT_ID,
            "Amount": int(order.get_total_price()),
            "Description": 'Mystore',
            "Phone": '',
            "CallbackURL": request.build_absolute_uri(reverse('store:order_verify')),
        }

        request_header = {
            "accept": "application/json",
            "content-type": "application/json"
        }
        res = requests.post(zarinpal.ZP_API_REQUEST, data=json.dumps(req_data), headers=request_header)
        print(res)
        # print(res.json()['data'])

        data = res.json()
        print(data)
        authority = data['Authority']
        order.zarinpal_authority = authority
        order.save()

        if 'errors' not in data or len(data['errors']) == 0:
            return redirect(zarinpal.ZP_API_STARTPAY.format(sandbox=zarinpal.sandbox, authority=authority))
        else:
            print(data['errors'])
            # Need to ckeak for order.return_products_to_cart
            return Response({'error': 'Error from zarinpal'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class OrderVerifyView(APIView):
    http_method_names = ['get', 'option', 'head']
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payment_authority = request.GET.get('Authority')
        payment_status = request.GET.get('Status')

        order = get_object_or_404(Order, zarinpal_authority=payment_authority)

        if payment_status == 'OK':
            request_header = {
                "accept": "application/json",
                "content-type": "application/json",
            }

            req_data = {
                'MerchantID': settings.ZARINPALL_MERCHANT_ID,
                'Amount': int(order.get_total_price()),
                'Authority': payment_authority,
            }

            res = requests.post(
                    zarinpal.ZP_API_VERIFY,
                    data=json.dumps(req_data),
                    headers=request_header,

                )
            if 'errors' not in res.json():
                data = res.json()
                payment_code = data['Status']

                if payment_code == 100:
                    order.status = 'p'
                    order.zarinpal_ref_id = data['RefID']
                    order.zarinpal_data = data
                    order.save()
                    return Response({'success': 'Your payment has been successfully completed!'}, status=status.HTTP_200_OK)
                    # Need to ckeak for order.return_products_to_cart
                elif payment_code == 101:
                    return Response({'success': 'Your payment has been successfully completed.'
                                    ' Of course, this transaction has already been registered!'}, status=status.HTTP_200_OK)

                else:
                    # Need to ckeak for order.return_products_to_cart
                    error_code = res.json().get('errors', {}).get('code')
                    # error_message = res.json()['errors']['message']
                    error_message = res.json().get('errors', {}).get('message')
                    return Response({'error': f'The transaction was unsuccessful! {error_message} {error_code} '}, status=status.HTTP_400_BAD_REQUEST)

        else:

            # Need to ckeak for order.return_products_to_cart
            return Response({'error': 'The transaction was unsuccessful or canceled by user !'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
