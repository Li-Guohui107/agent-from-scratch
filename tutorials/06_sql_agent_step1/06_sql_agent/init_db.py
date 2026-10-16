import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent / "data" / "sales.db"


def init_database():
    # 创建 data 文件夹
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 清空旧表，保证重复运行时数据一致
    cursor.execute("DROP TABLE IF EXISTS sales")

    # 创建销售数据表
    cursor.execute(
        """
        CREATE TABLE sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product TEXT NOT NULL,
            category TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            salesperson TEXT NOT NULL,
            sale_date TEXT NOT NULL
        )
        """
    )

    data = [
        ("Laptop", "Electronics", 3, 6999.0, "Alice", "2026-10-01"),
        ("Phone", "Electronics", 8, 3999.0, "Bob", "2026-10-02"),
        ("Desk", "Furniture", 5, 1299.0, "Alice", "2026-10-03"),
        ("Chair", "Furniture", 10, 599.0, "Charlie", "2026-10-04"),
        ("Monitor", "Electronics", 6, 1899.0, "Bob", "2026-10-05"),
        ("Keyboard", "Accessories", 12, 299.0, "Alice", "2026-10-06"),
        ("Mouse", "Accessories", 15, 159.0, "Charlie", "2026-10-07"),
        ("Tablet", "Electronics", 4, 2999.0, "Bob", "2026-10-08"),
    ]

    cursor.executemany(
        """
        INSERT INTO sales
        (product, category, quantity, unit_price, salesperson, sale_date)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        data,
    )

    conn.commit()
    conn.close()

    print(f"数据库初始化完成：{DB_PATH}")


if __name__ == "__main__":
    init_database()
