# undo_manager.py - Son 1 işlemi geri alma sistemi
# Uygulama genelinde tek bir UndoManager instance kullanılır (Singleton).

from dataclasses import dataclass, field
from typing import Optional, Any
from enum import Enum


class ActionType(Enum):
    SALE        = "SATIŞ"
    EXPENSE     = "GİDER"
    PURCHASE    = "ALIM (Stok Girişi)"


@dataclass
class UndoAction:
    """Geri alınabilecek tek bir işlemin snapshot'ı."""
    action_type: ActionType
    description: str          # Kullanıcıya gösterilecek özet
    db_record_id: int         # Ana kaydın DB id'si (sale.id, expense.id, purchase.id)
    extra: dict = field(default_factory=dict)  # Ek veri (ör. stok değişimleri)


class UndoManager:
    """
    Basit tek-adım geri alma yöneticisi.
    Her yeni işlem önceki işlemin üzerine yazar.
    """
    _instance: Optional["UndoManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._action = None
        return cls._instance

    def push(self, action: UndoAction):
        """Yeni bir işlemi geri alma stack'ine ekle."""
        self._action = action

    def pop(self) -> Optional[UndoAction]:
        """Bekleyen işlemi al ve temizle."""
        action = self._action
        self._action = None
        return action

    def peek(self) -> Optional[UndoAction]:
        """Bekleyen işlemi silmeden göster."""
        return self._action

    def clear(self):
        self._action = None


# Global singleton erişimi
undo_manager = UndoManager()
