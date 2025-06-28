import requests

response = requests.post(
    "http://127.0.0.1:8000/command",
    json={"command": "solid", "args": ["3"]},
    timeout=5
)
print(response.json())
