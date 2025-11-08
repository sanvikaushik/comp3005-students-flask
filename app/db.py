import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_conn():

    host = os.getenv("PGHOST")
    port = os.getenv("PGPORT")
    db   = os.getenv("PGDATABASE")
    user = os.getenv("PGUSER")
    pwd  = os.getenv("PGPASSWORD")  

    return psycopg2.connect(
        host=host,
        port=port,
        dbname=db,
        user=user,
        password=pwd if pwd else None, 
    )
