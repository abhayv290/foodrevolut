from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from apps.restaurants.models import MenuItem

class MenuItemSearchSerializer(ModelSerializer):
    '''
    Extending MenuItemListSerializer with restaurant info
    For giving the customer context to decide where to order from 
    by giving appropriate info like restaurant name,rating etc '''

    restaurant_id = serializers.UUIDField(source ='category.restaurant.id',read_only=True)
    restaurant_name = serializers.CharField(source='category.restaurant.name',read_only=True)
    restaurant_rating  = serializers.DecimalField(source='category.restaurant.average_rating',read_only=True,max_digits=3,decimal_places=2)
    variants = serializers.SerializerMethodField()

    class Meta:
        model = MenuItem
        fields = ('id','name','description','image','base_price','is_veg','is_bestseller',
                'restaurant_id','restaurant_name','restaurant_rating','variants')

    def get_variants(self,obj):
        from apps.restaurants.serializers import MenuItemVariantSerializer
        return MenuItemVariantSerializer(obj.variants.filter(is_available=True),many=True).data
    

