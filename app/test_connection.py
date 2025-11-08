import db

try:
    
    conn = db.get_conn()
    print("YAY. database connection successful")
    with conn.cursor() as cur:
        cur.execute("select current_user, current_database();")
        print("User/DB:", cur.fetchone())
    conn.close()

except Exception as e:
    print("NOOO. connection failed:", e)
