import requests
from config import Config


class APIError(Exception):
    pass


class APIClient:
    def __init__(self):
        self.base_url = Config.API_BASE_URL
        self.session  = requests.Session()
        self.session.headers.update({
            "Content-Type":  "application/json",
            "X-API-Key":     Config.API_KEY,
            "Connection":    "close",
        })

    def set_token(self, token: str):
        """Login sonrası JWT token'ı header'a ekle."""
        self.session.headers.update({
            "Authorization": f"Bearer {token}"
        })

    def get(self, path):
        try:
            r = self.session.get(f"{self.base_url}{path}", timeout=10)
            if r.status_code >= 400:
                raise APIError(r.json().get("detail", r.text))
            return r.json()
        except APIError:
            raise
        except Exception as e:
            raise APIError(str(e))

    def post(self, path, data):
        try:
            r = self.session.post(f"{self.base_url}{path}", json=data, timeout=10)
            if r.status_code >= 400:
                raise APIError(r.json().get("detail", r.text))
            return r.json()
        except APIError:
            raise
        except Exception as e:
            raise APIError(str(e))

    def put(self, path, data):
        try:
            r = self.session.put(f"{self.base_url}{path}", json=data, timeout=10)
            if r.status_code >= 400:
                raise APIError(r.json().get("detail", r.text))
            return r.json()
        except APIError:
            raise
        except Exception as e:
            raise APIError(str(e))

    def patch(self, path, data=None):
        try:
            r = self.session.patch(f"{self.base_url}{path}", json=data or {}, timeout=10)
            if r.status_code >= 400:
                raise APIError(r.json().get("detail", r.text))
            return r.json()
        except APIError:
            raise
        except Exception as e:
            raise APIError(str(e))

    def delete(self, path):
        try:
            r = self.session.delete(f"{self.base_url}{path}", timeout=10)
            if r.status_code >= 400:
                raise APIError(r.json().get("detail", r.text))
            return r.json()
        except APIError:
            raise
        except Exception as e:
            raise APIError(str(e))

    # ── Dashboard ──────────────────────────────────────────────────
    def get_dashboard(self):
        return self.get("/api/dashboard")

    # ── Suppliers ─────────────────────────────────────────────────
    def get_suppliers(self):
        return self.get("/api/suppliers")
    def create_supplier(self, data):
        return self.post("/api/suppliers", data)
    def update_supplier(self, sid, data):
        return self.put(f"/api/suppliers/{sid}", data)
    def delete_supplier(self, sid):
        return self.delete(f"/api/suppliers/{sid}")
    def pay_supplier(self, sid, amount):
        return self.post(f"/api/suppliers/{sid}/pay", {"amount": amount})
    def undo_supplier_payment(self, sid, pid):
        return self.delete(f"/api/suppliers/{sid}/payments/{pid}")

    # ── Products ──────────────────────────────────────────────────
    def get_products(self):
        return self.get("/api/products")
    def create_product(self, data):
        return self.post("/api/products", data)
    def update_product(self, pid, data):
        return self.put(f"/api/products/{pid}", data)
    def delete_product(self, pid):
        return self.delete(f"/api/products/{pid}")

    # ── Customers ─────────────────────────────────────────────────
    def get_customers(self, search: str = ""):
        return self.get("/api/customers")
    def create_customer(self, data):
        return self.post("/api/customers", data)
    def update_customer(self, cid, data):
        return self.put(f"/api/customers/{cid}", data)
    def delete_customer(self, cid):
        return self.delete(f"/api/customers/{cid}")
    def get_customer_sales(self, cid):
        return self.get(f"/api/customers/{cid}/sales")

    # ── Sales ─────────────────────────────────────────────────────
    def get_sales(self):
        return self.get("/api/sales")
    def create_sale(self, items, discount, payment_method, customer_id):
        return self.post("/api/sales", {
            "items": items,
            "discount": discount,
            "payment_method": payment_method,
            "customer_id": customer_id,
        })
    def undo_sale(self, sale_id):
        return self.delete(f"/api/sales/{sale_id}")
    def cancel_sale_item(self, sale_id, item_id):
        return self.patch(f"/api/sales/{sale_id}/items/{item_id}/cancel")
    def cancel_full_sale(self, sale_id):
        return self.patch(f"/api/sales/{sale_id}/cancel-full")

    # ── Purchases ─────────────────────────────────────────────────
    def get_purchases(self):
        return self.get("/api/purchases")
    def cancel_purchase(self, pid):
        return self.patch(f"/api/purchases/{pid}/cancel")

    # ── Expenses ──────────────────────────────────────────────────
    def get_expenses(self):
        return self.get("/api/expenses")
    def create_expense(self, data):
        return self.post("/api/expenses", data)
    def delete_expense(self, eid):
        return self.delete(f"/api/expenses/{eid}")

    # ── Reports (dönem) ───────────────────────────────────────────
    def get_daily_report(self):
        return self.get("/api/reports/daily")
    def get_weekly_report(self):
        return self.get("/api/reports/weekly")
    def get_monthly_report(self):
        return self.get("/api/reports/monthly")
    def get_cancellation_logs(self):
        return self.get("/api/reports/cancellations")

    # ── Reports (analitik) ────────────────────────────────────────
    def get_top_products(self):
        return self.get("/api/reports/top-products")
    def get_supplier_summary(self):
        return self.get("/api/reports/supplier-summary")
    def get_customer_summary(self):
        return self.get("/api/reports/customer-summary")


api = APIClient()
