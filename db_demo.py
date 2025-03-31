import psycopg2

try:
    conn = psycopg2.connect(
        dbname="rag_human_rights",
        user="postgres",
        password="user12345",
        host="localhost",
        port="5432"
    )
    print("✅ Connection successful!")
    conn.close()
except Exception as e:
    print(f"❌ Error: {e}")
