from decimal import Decimal
from datetime import date, datetime, time

from django.db import models
from django.db.models import F, Sum, Count
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.dateparse import parse_date

from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .models import Customer, Product, Order, OrderItem
from .serializers import (
    CustomerSerializer,
    ProductSerializer,
    OrderSerializer,
)

# ---------- Helpers ----------

def _parse_date_range(request, dt_field="order_date"):
    """
    Parse ?from=YYYY-MM-DD&to=YYYY-MM-DD into a Django ORM filter dict.
    Inclusive on both ends. Defaults to the full range if not supplied.
    """
    qs_filters = {}
    from_str = request.query_params.get("from")
    to_str = request.query_params.get("to")

    start_dt = None
    end_dt = None

    if from_str:
        d = parse_date(from_str)
        if d:
            start_dt = timezone.make_aware(datetime.combine(d, time.min))
    if to_str:
        d = parse_date(to_str)
        if d:
            # inclusive end-of-day
            end_dt = timezone.make_aware(datetime.combine(d, time.max))

    if start_dt:
        qs_filters[f"{dt_field}__gte"] = start_dt
    if end_dt:
        qs_filters[f"{dt_field}__lte"] = end_dt

    return qs_filters


# ---------- ViewSets ----------

class CustomerViewSet(mixins.ListModelMixin,
                      mixins.CreateModelMixin,
                      viewsets.GenericViewSet):
    queryset = Customer.objects.all().order_by("id")
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]


class ProductViewSet(mixins.ListModelMixin,
                     mixins.CreateModelMixin,
                     viewsets.GenericViewSet):
    queryset = Product.objects.all().order_by("id")
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]


class OrderViewSet(mixins.ListModelMixin,
                   mixins.CreateModelMixin,
                   viewsets.GenericViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Optimize with select_related and prefetch_related; annotate total_price for serializer
        qs = (
            Order.objects
            .select_related("customer")
            .prefetch_related(
                # Pull related products in same query for items
                models.Prefetch(
                    "items",
                    queryset=OrderItem.objects.select_related("product")
                )
            )
            .annotate(
                total_price=Coalesce(Sum(F("items__quantity") * F("items__product__price")), Decimal("0.00"))
            )
            .order_by("-id")
        )
        return qs

    def list(self, request, *args, **kwargs):
        print("==== AUTH HEADER RECEIVED ====")
        print(request.headers.get("Authorization"))
        return super().list(request, *args, **kwargs)


    def create(self, request, *args, **kwargs):
        # Use nested serializer; validations ensure quantity>=1 and at least one item
        return super().create(request, *args, **kwargs)


# ---------- Analytics ----------

class SalesSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        filters = _parse_date_range(request, dt_field="order_date")
        order_qs = Order.objects.filter(**filters)

        # Compute total sales by joining items
        totals = (
            OrderItem.objects
            .filter(order__in=order_qs)
            .aggregate(
                total_sales=Coalesce(Sum(F("quantity") * F("product__price")), Decimal("0.00")),
                total_quantity=Coalesce(Sum("quantity"), 0),
            )
        )

        summary = {
            "total_sales": totals["total_sales"],
            "total_orders": order_qs.count(),
            "unique_customers": order_qs.values("customer").distinct().count(),
            "total_quantity_sold": totals["total_quantity"],
            "from": request.query_params.get("from"),
            "to": request.query_params.get("to"),
        }
        return Response(summary, status=status.HTTP_200_OK)


class TopCustomersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        filters = _parse_date_range(request, dt_field="order_date")
        order_qs = Order.objects.filter(**filters)

        # Sum per customer: quantity * price
        rows = (
            OrderItem.objects
            .filter(order__in=order_qs)
            .values("order__customer", "order__customer__name", "order__customer__email")
            .annotate(
                amount=Coalesce(Sum(F("quantity") * F("product__price")), Decimal("0.00"))
            )
            .order_by("-amount")[:5]
        )

        data = [
            {
                "customer_id": r["order__customer"],
                "name": r["order__customer__name"],
                "email": r["order__customer__email"],
                "amount": r["amount"],
            }
            for r in rows
        ]
        return Response({"results": data}, status=status.HTTP_200_OK)


class TopProductsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        filters = _parse_date_range(request, dt_field="order_date")
        order_qs = Order.objects.filter(**filters)

        rows = (
            OrderItem.objects
            .filter(order__in=order_qs)
            .values("product", "product__name")
            .annotate(
                total_qty=Coalesce(Sum("quantity"), 0),
                revenue=Coalesce(Sum(F("quantity") * F("product__price")), Decimal("0.00")),
            )
            .order_by("-total_qty")[:5]
        )

        data = [
            {
                "product_id": r["product"],
                "name": r["product__name"],
                "total_quantity_sold": r["total_qty"],
                "revenue": r["revenue"],
            }
            for r in rows
        ]
        return Response({"results": data}, status=status.HTTP_200_OK)
