from ..data_access import aktivite_dal


def logla(cursor, kullanici_id, islem_tipi, sayfa=None, detay=None, ip_adresi=None):
    aktivite_dal.log_ekle(cursor, kullanici_id, islem_tipi, sayfa, detay, ip_adresi)


def listele(cursor, kullanici_id=None, islem_tipi=None, baslangic=None, bitis=None, limit=50, offset=0):
    return aktivite_dal.log_listele(cursor, kullanici_id, islem_tipi, baslangic, bitis, limit, offset)
