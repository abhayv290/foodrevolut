from django.urls import path
from .views import OrderReviewStatusView,RestaurantReviewListView,SubmitRestaurantReviewView,SubmitDeliveryReviewView

app_name = "reviews"

urlpatterns = [
    path("orders/<uuid:order_id>/restaurant/",SubmitRestaurantReviewView.as_view(),name="submit-restaurant-review",
    ),
    path("orders/<uuid:order_id>/delivery/",SubmitDeliveryReviewView.as_view(),name="submit-delivery-review",
    ),

    path(
        "restaurants/<uuid:restaurant_id>/",
        RestaurantReviewListView.as_view(),
        name="restaurant-reviews",
    ),
    path(
        "orders/<uuid:order_id>/status/",
        OrderReviewStatusView.as_view(),
        name="order-review-status",
    ),
]