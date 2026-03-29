from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from core.permissions import IsCustomer
from apps.orders.models import Order
from apps.restaurants.models import Restaurants
from .models import RestaurantReview, DeliveryReview
from .serializers import (
    RestaurantReviewSerializer,
    DeliveryReviewSerializer,
    RestaurantReviewListSerializer,
)

@extend_schema(tags=['Reviews'],request=RestaurantReviewSerializer,responses=RestaurantReviewSerializer)
class SubmitRestaurantReviewView(APIView):
    '''
    POST /reviews/orders/<order_id>/restaurant/
    
    Customer Submits a restaurant review for  a delivered order
    Order is the entry point - not the restaurant 

    '''

    permission_classes = [IsAuthenticated,IsCustomer]

    def post(self,request,order_id):
        order =  get_object_or_404(Order,pk=order_id,customer = request.user)
        serializer = RestaurantReviewSerializer(data=request.data,
                    context={'request':request,'order':order})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        #signal fires here automatically , restaurant stats updates
        return Response(serializer.data,status=status.HTTP_201_CREATED)
    

@extend_schema(tags=['Reviews'],request=DeliveryReviewSerializer,responses=DeliveryReviewSerializer)
class SubmitDeliveryReviewView(APIView):
    '''
    POST /reviews/orders/<order_id>/delivery/
    Customer submits a delivery agent review for a delivered order
    '''
    permission_classes = [IsAuthenticated,IsCustomer]

    def post(self,request,order_id):
        order = get_object_or_404(Order,pk=order_id,customer = request.user)
        serializer = DeliveryReviewSerializer(data=request.data,
            context={'request':request,'order':order})
        
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data,status = status.HTTP_201_CREATED)

@extend_schema(tags=['Reviews'])
class RestaurantReviewListView(generics.ListAPIView):
    '''
    GET /reviews/restaurants/<restaurant_id>/
    '''
    serializer_class = RestaurantReviewListSerializer
    permission_classes = [AllowAny]

    queryset = RestaurantReview.objects.all()

    def get_queryset(self):
        restaurant = get_object_or_404(Restaurants,pk=self.kwargs['restaurant_id'])
        return super().get_queryset().filter(restaurant=restaurant).select_related('customer')



@extend_schema(tags=['Reviews'])
class OrderReviewStatusView(APIView):
    '''
    GET /reviews/orders/<order_id>/status/
    return which review the customer already submitted for this order

    '''
    permission_classes = [IsAuthenticated,IsCustomer]
    @extend_schema(
    responses={'200': {'type': 'object', 'properties': {'restaurant_reviewed': {'type': 'boolean'}, 'delivery_reviewed': {'type': 'boolean'}}}}
    )
    def get(self,request,order_id):
        order = get_object_or_404(Order,pk=order_id,customer = request.user)
        return Response({
            'restaurant_reviewed':RestaurantReview.objects.filter(order=order).exists(),
            'delivery_reviewed' : DeliveryReview.objects.filter(order=order).exists(),
        })
    

