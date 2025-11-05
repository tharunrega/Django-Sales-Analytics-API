
# Django Sales Analytics API

Lightweight REST API for sales analytics built with **Django + Django REST Framework**.  
Provides CRUD for customers, products, and orders, plus analytics endpoints for sales summaries and top performers.

---

## Features

- **Customers, Products, Orders CRUD** via DRF ViewSets (router)
- **Analytics endpoints**
  - Sales summary (time/windowed totals)
  - Top customers by revenue
  - Top products by sales
  - Pagination and optional search
- Clean, testable views suitable for extension

---

## Quick Setup (Windows / PowerShell)

1. **Create virtual environment and install dependencies**
   ```powershell
   python -m venv .venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
````

2. **Run migrations and start server**

   ```powershell
   python manage.py makemigrations
   python manage.py migrate
   python manage.py runserver
   ```

3. **(Optional) Create admin user**

   ```powershell
   python manage.py createsuperuser
   ```

Open the server at: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

## API Endpoints

**Base path prefix:** `/api/`

### CRUD Routers (DefaultRouter)

#### Customers

* `GET /api/customers/` — list customers
* `POST /api/customers/` — create customer
* `GET /api/customers/{id}/` — retrieve
* `PATCH /api/customers/{id}/` — partial update
* `PUT /api/customers/{id}/` — full update
* `DELETE /api/customers/{id}/` — delete customer

#### Products

* `GET /api/products/` — list products
* `POST /api/products/` — create product
* `GET /api/products/{id}/` — retrieve
* `PATCH /api/products/{id}/` — partial update
* `DELETE /api/products/{id}/` — delete product

#### Orders

* `GET /api/orders/` — list orders
* `POST /api/orders/` — create order
* `GET /api/orders/{id}/` — retrieve
* `PATCH /api/orders/{id}/` — partial update
* `DELETE /api/orders/{id}/` — delete order

---

## Analytics Endpoints

* `GET /api/analytics/sales-summary/` — aggregated sales summary (supports date range query params)
* `GET /api/analytics/top-customers/?limit=10` — top customers by revenue
* `GET /api/analytics/top-products/?limit=10` — top products by sales

---

## Example Requests

### List top products

```bash
curl "http://127.0.0.1:8000/api/analytics/top-products/?limit=10"
```

### Sales summary (example date params)

```bash
curl "http://127.0.0.1:8000/api/analytics/sales-summary/?start=2025-01-01&end=2025-01-31"
```

---

## Configuration / Environment

Set environment variables (or use a `.env` library):

```
DJANGO_SECRET_KEY=<your_secret_key>
DEBUG=True/False
DATABASE_URL=<database_url>  # optional external DB, default SQLite
```

Optional: configure pagination size and authentication settings in `REST_FRAMEWORK`.

---

## Tests

Run unit tests:

```bash
python manage.py test
```

---

## Development Notes

* Router is defined in `analytics/urls.py` using DRF `DefaultRouter`
* Analytics views are **class-based** (`APIView` / `GenericAPIView`)
* Extend to add filters, date ranges, caching
* Add DB indexes on commonly queried fields (order date, customer id, product id)
* Consider precomputing heavy aggregates using **Celery** for very large data volumes

---

## Contributing

1. Fork the repo
2. Create a feature branch
3. Add tests for new behavior
4. Open a PR with a description of changes

---

## License

**MIT License**
© Django Sales Analytics API

```

---

