import requests
with open('token_clean.txt') as f:
    token = f.read().strip()
headers = {'Authorization': f'Bearer {token}'}
r = requests.get('http://127.0.0.1:8000/api/v1/admin/requests/', headers=headers)
print("Admin Response code:", r.status_code)
print("Admin Preview:", str(r.json())[:500])
