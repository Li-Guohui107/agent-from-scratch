from database import get_schema, query


def print_schema():
    schema = get_schema()

    print("\n=== Database Schema ===")

    for table_name, columns in schema.items():
        print(f"\n表：{table_name}")

        for column in columns:
            flags = []
            if column["primary_key"]:
                flags.append("PK")
            if column["not_null"]:
                flags.append("NOT NULL")

            suffix = f" ({', '.join(flags)})" if flags else ""
            print(f"  - {column['name']}: {column['type']}{suffix}")


def main():
    print_schema()

    print("\n=== 示例查询 ===")

    sql = """
    SELECT
        product,
        quantity,
        unit_price,
        quantity * unit_price AS total_amount
    FROM sales
    ORDER BY total_amount DESC
    """

    columns, rows = query(sql)

    print(" | ".join(columns))

    for row in rows:
        print(" | ".join(str(value) for value in row))


if __name__ == "__main__":
    main()
