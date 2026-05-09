from app.db.session import get_supabase_client

client = get_supabase_client()

response = client.table("users").select("*").limit(1).execute()

print(response)
print(response.data)