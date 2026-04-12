from django.urls import path
from .views import MenuItemSearchView,AutoCompleteSearch ,RestaurantSearchView

app_name='search'


urlpatterns = [
    path('menu-items/',MenuItemSearchView.as_view(),name='menu-items-search'),
    path('restaurants/',RestaurantSearchView.as_view(),name='restaurant-search'),
    path('auto/',AutoCompleteSearch.as_view(),name='auto-complete-search'),
]
