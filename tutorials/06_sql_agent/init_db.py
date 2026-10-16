import sqlite3
from pathlib import Path


DB_PATH = Path("data/sales.db")


def init_database():
    # 创建 data 文件夹
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # 连接数据库
    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    # 创建 products 表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    """)

    # 创建 sales 表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            sale_date TEXT NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    # 插入产品数据
    products = [
        ("笔记本电脑", "电子产品", 5999.0, 50),
        ("机械键盘", "电子产品", 499.0, 120),
        ("无线鼠标", "电子产品", 199.0, 200),
        ("显示器", "电子产品", 1899.0, 80),
        ("办公椅", "办公用品", 1299.0, 60),
        ("办公桌", "办公用品", 1599.0, 40),
        ("耳机", "电子产品", 699.0, 150),
        ("摄像头", "电子产品", 399.0, 100),
    ]

    cursor.executemany("""
        INSERT INTO products (name, category, price, stock)
        VALUES (?, ?, ?, ?)
    """, products)

    # 插入销售数据
    sales = [
        (1, 3, "2026-10-01"),
        (2, 10, "2026-10-01"),
        (3, 20, "2026-10-02"),
        (4, 5, "2026-10-03"),
        (5, 8, "2026-10-04"),
        (6, 4, "2026-10-05"),
        (7, 15, "2026-10-06"),
        (8, 12, "2026-10-07"),
        (1, 2, "2026-10-08"),
        (2, 8, "2026-10-09"),
        (3, 25, "2026-10-10"),
        (4, 6, "2026-10-11"),
        (7, 20, "2026-10-12"),
        (8, 10, "2026-10-13"),
    ]

    cursor.executemany("""
        INSERT INTO sales (product_id, quantity, sale_date)
        VALUES (?, ?, ?)
    """, sales)

    conn.commit()
    conn.close()

    print("数据库初始化完成！")
    print(f"数据库位置：{DB_PATH}")


if __name__ == "__main__":
    init_database()
