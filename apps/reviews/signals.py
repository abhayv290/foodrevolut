from django.db.models.signals import post_save
from django.dispatch import receiver 
from django.db.models import Avg
from .models import RestaurantReview,DeliveryReview


@receiver(post_save,sender=RestaurantReview)
def update_restaurant_stats(sender,instance,created,**kwargs):
    '''
    Fires Every time the RestaurantReview is saved 
    Recalculate Total rating and Average ratings on the restaurants'''
    print('Signal Fired for restaurant')
    if created:
        restaurant = instance.restaurant
        stats = RestaurantReview.objects.filter(restaurant=restaurant).aggregate(average = Avg('rating'))

        restaurant.average_rating =round(stats['average'] or 0,2)
        restaurant.total_ratings = RestaurantReview.objects.filter(
            restaurant=restaurant
        ).count()
        restaurant.save(update_fields = ['average_rating','total_ratings'])

@receiver(post_save,sender=DeliveryReview)
def update_agent_stats(sender,instance ,created, **kwargs):
    '''
    Fires Every time delivery review is saved'''

    if created:
        agent = instance.agent 
        agent_profile = agent.agent_profile 
        stats = DeliveryReview.objects.filter(
            agent = agent 
        ).aggregate(average = Avg('rating'))

        agent_profile.average_rating = round(stats['average'] or 0,2)
        agent_profile.total_deliveries = DeliveryReview.objects.filter(agent =agent).count()
        agent_profile.save(update_fields = ['average_rating','total_deliveries'])
