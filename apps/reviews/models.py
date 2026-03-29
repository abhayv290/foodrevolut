import uuid 
from django.conf import settings 
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from apps.users.models import UserRole
from apps.orders.models import Order
from apps.restaurants.models import Restaurants
from django.utils.translation import gettext_lazy as _

class RestaurantReview(models.Model):
    id =  models.UUIDField(_('Id'),primary_key=True,default=uuid.uuid4,editable=False)
    customer = models.ForeignKey(settings.AUTH_USER_MODEL,verbose_name=_('Customer'),related_name='restaurant_reviews',on_delete=models.CASCADE,limit_choices_to={'role':UserRole.CUSTOMER})
    restaurant = models.ForeignKey(Restaurants,verbose_name=_('Restaurants'),related_name='reviews',on_delete=models.CASCADE)
    order = models.OneToOneField(Order, verbose_name=_('Order'), on_delete=models.CASCADE,related_name='restaurant_reviews')
    #Rating 1 to 5 
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1),MaxValueValidator(5)])
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = _('Restaurant Reviews')
    
    def __str__(self):
        return f"{self.customer.name}->{self.restaurant.name} -> {self.rating}⭐"
    

class DeliveryReview(models.Model):
    id = models.UUIDField(_('Id'),primary_key=True,default=uuid.uuid4,editable=False)
    customer = models.ForeignKey(settings.AUTH_USER_MODEL,verbose_name=_('Customer'),related_name='delivery_reviews',on_delete=models.CASCADE,limit_choices_to={'role':UserRole.CUSTOMER})
    agent =  models.ForeignKey(settings.AUTH_USER_MODEL,verbose_name=_('Delivery Agent'),related_name='received_delivery_reviews',on_delete=models.CASCADE,limit_choices_to={'role':UserRole.DELIVERY_AGENT})
    order = models.OneToOneField(Order, verbose_name=_('Order'), on_delete=models.CASCADE,related_name='delivery_reviews')

    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1),MaxValueValidator(5)])
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = _('Delivery Reviews')

    
    def __str__(self):
        return f"{self.customer.name}->{self.agent.name}->{self.rating}⭐"
