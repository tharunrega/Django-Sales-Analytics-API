from decimal import Decimal
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Customer, Product, Order, OrderItem

User = get_user_model()

class SalesSummaryTests(APITestCase):
    def setUp(self):
        # Auth user + JWT
        self.user = User.objects.create_user(username="tester", password="pass1234")
        refresh = RefreshToken.for_user(self.user)
        self.access = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access}")

        # Seed data
        self.c1 = Customer.objects.create(name="Alice", email="alice@example.com")
        self.c2 = Customer.objects.create(name="Bob", email="bob@example.com")

        self.p1 = Product.objects.create(name="Laptop", price=Decimal("1000.00"))
        self.p2 = Product.objects.create(name="Mouse", price=Decimal("25.00"))

        # Recent order (counted if in range)
        self.o1 = Order.objects.create(customer=self.c1)  # order_date auto_now_add
        OrderItem.objects.create(order=self.o1, product=self.p1, quantity=1)   # 1000
        OrderItem.objects.create(order=self.o1, product=self.p2, quantity=2)   # 50

        # Another order
        self.o2 = Order.objects.create(customer=self.c2)
        OrderItem.objects.create(order=self.o2, product=self.p2, quantity=4)   # 100

    def test_sales_summary_no_range(self):
        url = reverse("sales-summary")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        body = resp.json()
        # total: 1000 + 50 + 100 = 1150
        self.assertIn("total_sales", body)
        self.assertEqual(Decimal(str(body["total_sales"])), Decimal("1150.00"))
        self.assertEqual(body["total_orders"], 2)
        self.assertEqual(body["unique_customers"], 2)
        self.assertEqual(body["total_quantity_sold"], 7)

    def test_sales_summary_with_range(self):
        url = reverse("sales-summary")
        today = timezone.localdate()
        params = {"from": today.isoformat(), "to": today.isoformat()}
        resp = self.client.get(url, params)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        body = resp.json()
        # Same-day orders included (since created in setUp with now)
        self.assertEqual(Decimal(str(body["total_sales"])), Decimal("1150.00"))
