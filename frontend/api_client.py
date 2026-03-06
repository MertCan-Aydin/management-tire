"""
api_client.py - Tum HTTP isteklerini yoneten merkezi istemci.
"""
import requests
from typing import Optional
from config import Config


class APIError(Exception):
    def __init__(self, message: str, status_code: int = 0):
        super().__init__(message)
        self.status_code = status_code


class APIClient:
    _instance: Optional["APIClient"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.base_url = Config.API_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "X-API-Key": Config.API_KEY
        })

    def _handle_response(self, resp: requests.Response):
        try:
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError:
            try:
                detail = resp.json().get("detail", resp.text)
            except Exception:
                detail = resp.text
            raise APIError(str(detail), resp.status_code)
        except requests.exceptions.ConnectionError:
            raise APIError(
                f"Sunucuya baglaниlamadi!\n\nAdres: {self.base_url}\n\n"
                "VPS sunucusunun acik oldugunden ve adresi dogru girdiginizden emin olun."
            )
        except requests.exceptions.Timeout:
            raise APIError("Istek zaman asimina ugradi. Sunucu yanit vermiyor.")

    def get(self, path: str, params: dict = None):
        resp = self.session.get(f"{self.base_url}{path}", params=params, timeout=10)
        return self._handle_response(resp)

    def post(self, path: str, data: dict):
        resp = self.session.post(f"{self.base_url}{path}", json=data, timeout=10)
        return self._handle_response(resp)

    def put(self, path: str, data: dict):
        resp = self.session.put(f"{self.base_url}{path}", json=data, timeout=10)
        return self._handle_response(resp)

    def patch(self, path: str, data: dict = None):
        resp = self.session.patch(f"{self.base_url}{path}", json=data or {}, timeout=10)
        return self._handle_response(resp)

    def delete(self, path: str):
        resp = self.session.delete(f"{self.base_url}{path}", timeout=10)
        return self._handle_response(resp)

    # Dashboard
    def get_dashboard(self):
        return self.get("/api/dashboard")

    # Suppliers
    def get_suppliers(self):
        return self.get("/api/suppliers")

    def create_supplier(self, name: str, contact_info: str = ""):
        return self.post("/api/suppliers", {"name": name, "contact_info": contact_info})

    def update_supplier(self, supplier_id: int, name: str, contact_info: str = ""):
        return self.put(f"/api/suppliers/{supplier_id}", {"name": name, "contact_info": contact_info})

    def delete_supplier(self, supplier_id: int):
        return self.delete(f"/api/suppliers/{supplier_id}")

    def pay_supplier(self, supplier_id: int, amount: float):
        return self.post(f"/api/suppliers/{supplier_id}/pay", {"amount": amount})

    def undo_supplier_payment(self, supplier_id: int, payment_id: int):
        return self.delete(f"/api/suppliers/{supplier_id}/payments/{payment_id}")

    # Products
    def get_products(self):
        return self.get("/api/products")

    def create_product(self, data: dict):
        return self.post("/api/products", data)

    def update_product(self, product_id: int, data: dict):
        return self.put(f"/api/products/{product_id}", data)

    def delete_product(self, product_id: int):
        return self.delete(f"/api/products/{product_id}")

    # Customers
    def get_customers(self, search: str = ""):
        params = {"search": search} if search else None
        return self.get("/api/customers", params)

    def create_customer(self, data: dict):
        return self.post("/api/customers", data)

    def update_customer(self, customer_id: int, data: dict):
        return self.put(f"/api/customers/{customer_id}", data)

    def delete_customer(self, customer_id: int):
        return self.delete(f"/api/customers/{customer_id}")

    def get_customer_sales(self, customer_id: int):
        return self.get(f"/api/customers/{customer_id}/sales")

    # Sales
    def get_sales(self):
        return self.get("/api/sales")

    def create_sale(self, items: list, discount: float, payment_method: str, customer_id=None):
        return self.post("/api/sales", {
            "items": items,
            "discount": discount,
            "payment_method": payment_method,
            "customer_id": customer_id
        })

    def undo_sale(self, sale_id: int):
        return self.delete(f"/api/sales/{sale_id}")

    def cancel_sale_item(self, sale_id: int, item_id: int):
        return self.patch(f"/api/sales/{sale_id}/items/{item_id}/cancel")

    def cancel_full_sale(self, sale_id: int):
        return self.patch(f"/api/sales/{sale_id}/cancel-full")

    # Purchases
    def get_purchases(self):
        return self.get("/api/purchases")

    def cancel_purchase(self, purchase_id: int):
        return self.patch(f"/api/purchases/{purchase_id}/cancel")

    # Expenses
    def get_expenses(self):
        return self.get("/api/expenses")

    def create_expense(self, description: str, amount: float):
        return self.post("/api/expenses", {"description": description, "amount": amount})

    def delete_expense(self, expense_id: int):
        return self.delete(f"/api/expenses/{expense_id}")

    # Reports
    def get_daily_report(self):
        return self.get("/api/reports/daily")

    def get_weekly_report(self):
        return self.get("/api/reports/weekly")

    def get_monthly_report(self):
        return self.get("/api/reports/monthly")

    def get_cancellation_logs(self):
        return self.get("/api/reports/cancellations")


# Global singleton
api = APIClient()