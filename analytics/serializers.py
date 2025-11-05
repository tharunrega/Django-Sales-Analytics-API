from decimal import Decimal
from django.db.models import F, Sum
from django.db.models.functions import Coalesce
from rest_framework import serializers

from .models import Customer, Product, Order, OrderItem


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "name", "email", "joined_on"]


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "price"]


class OrderItemSerializer(serializers.ModelSerializer):
    # Validation: quantity >= 1
    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value

    class Meta:
        model = OrderItem
        fields = ["id", "product", "quantity"]
        read_only_fields = ["id"]


class OrderSerializer(serializers.ModelSerializer):
    # Nested items for create/list
    items = OrderItemSerializer(many=True)
    # total_price (read-only, computed via annotation when possible)
    total_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "customer", "order_date", "items", "total_price"]
        read_only_fields = ["id", "order_date", "total_price"]

    def validate_items(self, value):
        # Ensure order has at least one item
        if not value or len(value) == 0:
            raise serializers.ValidationError("An order must contain at least one item.")
        return value

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        order = Order.objects.create(**validated_data)
        # bulk_create for efficiency; rely on serializer validation for quantity
        OrderItem.objects.bulk_create([
            OrderItem(order=order, product=item["product"], quantity=item.get("quantity", 1))
            for item in items_data
        ])
        # Attach computed total_price to instance (for immediate serializer output)
        total = (
            OrderItem.objects
            .filter(order=order)
            .aggregate(
                total=Coalesce(Sum(F("quantity") * F("product__price")), Decimal("0.00"))
            )["total"]
        )
        # set a non-db attribute so response includes it
        order.total_price = total
        return order
