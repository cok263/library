import requests


payload = {"id":"32168"}

url = 'https://tululu.org/txt.php?id=32168'
response = requests.get(url, verify=False)
response.raise_for_status()

filename = 'book.txt'
with open(filename, 'wb') as file:
    file.write(response.content)