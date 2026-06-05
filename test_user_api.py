import requests
with open('token_clean.txt') as f:
    token = f.read().strip()
headers = {'Authorization': f'Bearer {token}'}
r = requests.get('http://127.0.0.1:8000/api/v1/requests/', headers=headers)
print("Code:", r.status_code)
content = r.json()
print("Type of response:", type(content))
print("Preview user requests:", str(content)[:300])

r = requests.get('http://127.0.0.1:8000/api/v1/admin/requests/', headers=headers)
print("Admin Code:", r.status_code)
content = r.json()
print("Type of response Admin:", type(content))
print("Preview admin requests:", str(content)[:300])
