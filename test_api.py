import requests

r = requests.post('http://127.0.0.1:8000/api/v1/user/', json={
    "username": "testuser",
    "password": "testpassword123!",
    "email": "test@test.com"
})

if r.status_code == 400:
    r = requests.post('http://127.0.0.1:8000/api/v1/token/', json={
        "username": "testuser",
        "password": "testpassword123!"
    })
    
token = r.json().get('access')

print("Token:", token[:10] if token else None)

headers = {'Authorization': f'Bearer {token}'}

r = requests.get('http://127.0.0.1:8000/api/v1/requests/', headers=headers)
print("Requests URL returned:", r.status_code)
print(r.json())
