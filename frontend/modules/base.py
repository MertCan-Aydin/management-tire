from PyQt6.QtWidgets import QWidget

class BaseModule(QWidget):
    """
    Base class for all application modules (Suppliers, Inventory, Sales, Reports).
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Initialize the UI layout and components."""
        pass

    def refresh_data(self):
        """Called when the module becomes active or data needs refreshing."""
        pass


# ── Yardımcı: "[Mevsim] ModelAdı" → (season, model_name) ──────────────────────
def parse_brand_model(brand_model: str):
    """Ürünün brand_model alanını parçalar.

    brand_model örnekleri:
      "[Kislik] Blizzak LM005"  → ("Kislik", "Blizzak LM005")
      "Turanza T005"            → (None,     "Turanza T005")
      ""                        → (None,     "")
    """
    if not brand_model:
        return None, ""
    bm = str(brand_model).strip()
    if bm.startswith("["):
        end = bm.find("]")
        if end > 0:
            return bm[1:end].strip(), bm[end+1:].strip()
    return None, bm


def product_display_name(p: dict) -> str:
    """Ürünü "Ad · Marka Model (Mevsim)" şeklinde tek satırda özetler."""
    name  = p.get("name") or "Ürün"
    brand = p.get("brand_name") or ""
    season, model = parse_brand_model(p.get("brand_model") or "")
    extras = []
    if brand: extras.append(brand)
    if model: extras.append(model)
    if season: extras.append(f"({season})")
    tail = " ".join(extras)
    return f"{name}  ·  {tail}" if tail else name
