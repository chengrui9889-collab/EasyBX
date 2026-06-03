import requests

api = 'http://localhost:2233/api'

# Login with existing user
r = requests.post(f'{api}/auth/login', json={'username':'admin','password':'admin123'})
print('Login:', r.status_code)
token = r.json()['access_token']

# Dashboard stats - check
r2 = requests.get(f'{api}/dashboard/stats', headers={'Authorization': f'Bearer {token}'})
print('Dashboard:', r2.status_code, r2.json())