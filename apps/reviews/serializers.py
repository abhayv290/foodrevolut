from rest_framework import serializers 
from apps.orders.models import Order 
from .models import DeliveryReview,RestaurantReview


class RestaurantReviewSerializer(serializers.ModelSerializer):
    customer_name =  serializers.CharField(source = 'customer.name',read_only=True)

    class Meta:
        model = RestaurantReview
        fields= ('id','customer_name','rating','review','created_at')
        read_only_fields= ('id','customer_name','created_at')
    
    def validate(self,attrs):
        request  = self.context['request']
        order = self.context['order']

        #order must be delivered 
        if order.status  != Order.Status.DELIVERED:
            raise serializers.ValidationError(
                'You can only review after the order is delivered'
            )
        
        #order must belong to customer who is reviewing 
        if order.customer != request.user:
            raise serializers.ValidationError('Order not found')
        

        if RestaurantReview.objects.filter(customer=request.user,order=order).exists():
            raise serializers.ValidationError('You have already reviewed this order')
        
        return attrs
    

    def create(self,validated_data):
        request = self.context['request']
        order = self.context['order']

        return RestaurantReview.objects.create(
            customer = request.user,
            restaurant = order.restaurant,
            order = order,
            **validated_data
        )


class DeliveryReviewSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source = 'customer.name',read_only=True)
    agent_name = serializers.CharField(source = 'agent.name',read_only=True)

    class Meta:
        model = DeliveryReview
        fields = ('id','customer_name','agent_name','rating','review','created_at')
        read_only_fields = ('id','created_at')
    
    def validate(self,attrs):
        request = self.context['request']
        order =self.context['order']

        if order.status != Order.Status.DELIVERED:
            raise serializers.ValidationError('This order is not completed yet')
        
        if order.customer!=request.user:
            raise serializers.ValidationError('Order not found')
        
        #must have assigned to this order
        if not  order.delivery_agent:
            raise serializers.ValidationError('No agent assigned for this order')
        
        if DeliveryReview.objects.filter(order=order).exists():
            raise serializers.ValidationError('You already given a rating to this agent')

        return attrs

    
    def create(self,validated_data):
        request = self.context['request']
        order =self.context['order']

        return DeliveryReview.objects.create(
            customer = request.user,
            agent = order.delivery_agent,
            order = order,
            **validated_data
        )
    


class RestaurantReviewListSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
 
    class Meta:
        model  = RestaurantReview
        fields = ("id", "customer_name", "rating", "review", "created_at")    
