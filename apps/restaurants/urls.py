from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    RestaurantViewSets,
    CategoryViewSets,
    MenuItemViewSets,
    MenuItemVariantViewSets,
)

app_name = "restaurants"

list_create    = {"get": "list",     "post": "create"}
detail_actions = {"get": "retrieve", "put": "update",
                  "patch": "partial_update", "delete": "destroy"}

router = DefaultRouter()
router.register(r"", RestaurantViewSets, basename="restaurants")
#              

nested_urls = [
    # ── Categories ────────────────────────────────────────
    path(
        "<uuid:restaurant_pk>/categories/",
        CategoryViewSets.as_view(list_create),
        name="restaurant-categories",
    ),
    path(
        "<uuid:restaurant_pk>/categories/<uuid:pk>/",
        CategoryViewSets.as_view(detail_actions),
        name="restaurant-category-detail",
    ),

    # ── Menu items ────────────────────────────────────────
    path(
        "<uuid:restaurant_pk>/menu-items/",
        MenuItemViewSets.as_view(list_create),
        name="restaurant-menu-items",
    ),
    path(
        "<uuid:restaurant_pk>/menu-items/<uuid:pk>/",
        MenuItemViewSets.as_view(detail_actions),
        name="restaurant-menu-item-detail",
    ),
    path(
        "<uuid:restaurant_pk>/menu-items/<uuid:pk>/toggle/",
        MenuItemViewSets.as_view({"patch": "toggle_availability"}),
        name="menu-item-toggle",
    ),

    # ── Variants ──────────────────────────────────────────
    path(
        "<uuid:restaurant_pk>/menu-items/<uuid:menu_item_pk>/variants/",
        MenuItemVariantViewSets.as_view(list_create),
        name="menu-item-variants",
    ),
    path(
        "<uuid:restaurant_pk>/menu-items/<uuid:menu_item_pk>/variants/<uuid:pk>/",
        MenuItemVariantViewSets.as_view(detail_actions),
        name="menu-item-variant-detail",
    ),
]

urlpatterns = router.urls + nested_urls