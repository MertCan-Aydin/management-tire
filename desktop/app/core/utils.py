"""Ortak yardımcı fonksiyonlar."""


def tr_para(deger, ondalik: int = 2) -> str:
    """
    Türkçe para formatı: binlik ayraç nokta, ondalık virgül.
    1234567.89  →  1.234.567,89
    """
    val = float(deger or 0)
    formatted = f"{val:,.{ondalik}f}"
    return formatted.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def tr_sayi(deger, ondalik: int = 0) -> str:
    """Tam sayı Türkçe formatı: 1234567 → 1.234.567"""
    return tr_para(deger, ondalik=ondalik)
