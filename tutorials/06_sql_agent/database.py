import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "sales.db"


def get_connection():
    """创建 SQLite 数据库连接。"""
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"数据库不存在：{DB_PATH}\n"
            "请先运行：python tutorials/06_sql_agent/init_db.py"
        )

    return sqlite3.connect(DB_PATH)


def get_schema():
    """读取数据库中的表名和字段信息。"""
    conn = get_connection()

    try:
        cursor = conn.cursor()

        tables = cursor.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()

        schema = {}

        for (table_name,) in tables:
            columns = cursor.execute(
                f'PRAGMA table_info("{table_name}")'
            ).fetchall()

            schema[table_name] = [
                {
                    "name": column[1],
                    "type": column[2],
                    "not_null": bool(column[3]),
                    "primary_key": bool(column[5]),
                }
                for column in columns
            ]

        return schema

    finally:
        conn.close()


def query(sql: str, params=()):
    """执行只读查询并返回列名和结果。"""
    normalized = sql.strip().lower()

    if not normalized.startswith(("select", "with")):
        raise ValueError("本课程基础版本只允许执行 SELECT / WITH 查询。")

    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)

        columns = [item[0] for item in cursor.description]
        rows = cursor.fetchall()

        return columns, rows

    finally:
        conn.close()
