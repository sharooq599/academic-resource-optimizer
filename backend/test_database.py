from app.database.connection import engine, Base

try:
    with engine.connect() as connection:
        print("Database connected successfully!")

    print("Database URL:", engine.url)

except Exception as e:
    print("Database connection failed:", e)