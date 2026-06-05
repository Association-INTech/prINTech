import requests
with open('token_clean.txt') as f:
    token = f.read().strip()
headers = {'Authorization': f'Bearer {token}'}
r = requests.get('http://127.0.0.1:8000/api/v1/requests/', headers=headers)
print("Response code:", r.status_code)
print("Preview:", str(r.json())[:300])
