import requests
import os

payload = {"id":"32168"}

books_dir='books'
os.makedirs(books_dir, exist_ok=True)
for id in range(1, 11):
    url = 'https://tululu.org/txt.php?id={}'.format(id)
    response = requests.get(url, verify=False, allow_redirects=False)
    response.raise_for_status()

    if not response.is_redirect:
        filename = '{}/id{}.txt'.format(books_dir, id)
        with open(filename, 'wb') as file:
            file.write(response.content)