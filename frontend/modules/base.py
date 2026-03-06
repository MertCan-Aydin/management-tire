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
