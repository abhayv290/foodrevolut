from django.contrib import admin

from .models import RestaurantReview, DeliveryReview
 
 
@admin.register(RestaurantReview)
class RestaurantReviewAdmin(admin.ModelAdmin):
    list_display   = ("customer", "restaurant", "rating", "created_at")
    list_filter    = ("rating",)
    search_fields  = ("customer__email", "restaurant__name")
    readonly_fields = ("customer", "restaurant", "order", "rating", "review", "created_at")
    ordering       = ("-created_at",)
 
 
@admin.register(DeliveryReview)
class DeliveryReviewAdmin(admin.ModelAdmin):
    list_display   = ("customer", "agent", "rating", "created_at")
    list_filter    = ("rating",)
    search_fields  = ("customer__email", "agent__email")
    readonly_fields = ("customer", "agent", "order", "rating", "review", "created_at")
    ordering       = ("-created_at",)
 
