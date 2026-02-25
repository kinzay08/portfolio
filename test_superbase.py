from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    resp = supabase.table("messages").select("*").execute()
    print("Connected!", resp.data)
except Exception as e:
    print("Connection failed:", e)