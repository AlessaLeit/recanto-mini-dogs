import requests
import json

base_url = 'http://localhost:8000/api/v1'

def test_endpoint(path):
    try:
        r = requests.get(f'{base_url}/{path}')
        print(f'GET /{path}: {r.status_code}')
        if r.status_code == 200:
            print(f'Response preview: {json.dumps(r.json()[:2] if isinstance(r.json(), list) else r.json(), indent=2)[:500]}...')
        else:
            print(f'Error: {r.text}')
    except Exception as e:
        print(f'Exception {path}: {e}')

print('Testing API endpoints:')
test_endpoint('clientes')
test_endpoint('clientes/')
test_endpoint('cachorros')
test_endpoint('health')
test_endpoint('')
print('\nRoot /health:')
try:
    r = requests.get('http://localhost:8000/health')
    print(f'Status: {r.status_code}, Response: {r.text}')
except Exception as e:
    print(e)
