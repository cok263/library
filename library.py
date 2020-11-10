import os
import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename

def download_txt(url, filename, folder='books/'):
    """Функция для скачивания текстовых файлов.
    Args:
        url (str): Cсылка на текст, который хочется скачать.
        filename (str): Имя файла, с которым сохранять.
        folder (str): Папка, куда сохранять.
    Returns:
        str: Путь до файла, куда сохранён текст.
    """
    response = requests.get(url, verify=False, allow_redirects=False)
    response.raise_for_status()

    if not response.is_redirect:
        os.makedirs(folder, exist_ok=True)
        filename = os.path.join(folder, sanitize_filename(filename))
        with open(filename, 'wb') as file:
            file.write(response.content)
        return filename


for id in range(1, 11):
    url = 'https://tululu.org/b{}/'.format(id)
    response = requests.get(url, verify=False, allow_redirects=False)
    response.raise_for_status()
    if not response.is_redirect:
        soup = BeautifulSoup(response.text, 'lxml')
        header = soup.find('td', class_='ow_px_td').find('h1')
        headers = str(header).strip('</h1>').split('::')
        title = headers[0].strip()
        author = headers[1].split('">')[1].rstrip('</a')

        url = 'https://tululu.org/txt.php?id={}'.format(id)
        print(download_txt(url, '{}. {}.txt'.format(id, title)))
    