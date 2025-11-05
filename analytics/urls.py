from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CustomerViewSet,
    ProductViewSet,
    OrderViewSet,
    SalesSummaryView,
    TopCustomersView,
    TopProductsView,
)

router = DefaultRouter()
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'orders', OrderViewSet, basename='order')

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/analytics/sales-summary/', SalesSummaryView.as_view(), name='sales-summary'),
    path('api/analytics/top-customers/', TopCustomersView.as_view(), name='top-customers'),
    path('api/analytics/top-products/', TopProductsView.as_view(), name='top-products'),
]
