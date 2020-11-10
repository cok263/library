import os
import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urljoin

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

def download_image(url, filename, folder='images/'):
    """Функция для скачивания картинок.
    Args:
        url (str): Cсылка на картинку, которую хочется скачать.
        filename (str): Имя файла, с которым сохранять.
        folder (str): Папка, куда сохранять.
    Returns:
        str: Путь до файла, куда сохранён текст.
    """
    response = requests.get(url, verify=False, allow_redirects=False)
    response.raise_for_status()

    os.makedirs(folder, exist_ok=True)
    filename = os.path.join(folder, sanitize_filename(filename))
    with open(filename, 'wb') as file:
        file.write(response.content)
    return filename


books_count = 10
for id in range(1, books_count + 1):
    url = 'https://tululu.org/b{}/'.format(id)
    response = requests.get(url, verify=False, allow_redirects=False)
    response.raise_for_status()
    if not response.is_redirect:
        soup = BeautifulSoup(response.text, 'lxml')

        header = soup.find('td', class_='ow_px_td').find('h1')
        headers = str(header).strip('</h1>').split('::')
        title = headers[0].strip()
        author = headers[1].split('">')[1].rstrip('</a')
        
        image_src = soup.find('div', class_='bookimage').find('img')['src']

        url = 'https://tululu.org/txt.php?id={}'.format(id)
        print(download_txt(url, '{}. {}.txt'.format(id, title)))
    
        image_url = urljoin(url, image_src)
        print(download_image(image_url, image_url.split('/')[-1]))

        comments = soup.find_all('div', class_='texts')
        for comment in comments:
            print(comment.span.get_text())
