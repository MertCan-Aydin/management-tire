from contextlib import contextmanager
from typing import Generator, Tuple

import pymysql
import pymysql.cursors

from .config import settings


def _new_connection() -> pymysql.Connection:
    return pymysql.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        # Tarihler (DEFAULT CURRENT_TIMESTAMP, NOW(), CURDATE()) Türkiye
        # saatiyle yazılsın/karşılaştırılsın; VPS UTC'de olsa bile.
        init_command="SET time_zone = '+03:00'",
    )


@contextmanager
def get_cursor() -> Generator[Tuple[pymysql.cursors.DictCursor, pymysql.Connection], None, None]:
    """
    Her istek için bağımsız bir DB bağlantısı açar.
    Başarılıysa commit, hata varsa rollback yapar ve bağlantıyı kapatır.
    """
    conn = _new_connection()
    try:
        with conn.cursor() as cursor:
            yield cursor, conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def call_sp(cursor: pymysql.cursors.DictCursor, sp_name: str, params: list = None) -> list:
    """
    Stored procedure çağırır ve sonuç kümesini döner.
    Tüm DAL'lar bu yardımcıyı kullanır — doğrudan SQL yasak.
    """
    if params is None:
        params = []
    placeholders = ", ".join(["%s"] * len(params))
    sql = f"CALL {sp_name}({placeholders})"
    cursor.execute(sql, params)
    try:
        return cursor.fetchall()
    except Exception:
        return []


def call_sp_one(cursor: pymysql.cursors.DictCursor, sp_name: str, params: list = None):
    """Tek satır dönen SP'ler için kısayol."""
    rows = call_sp(cursor, sp_name, params)
    return rows[0] if rows else None
