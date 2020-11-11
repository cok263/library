import os
import json
import requests
import codecs
import argparse
import sys
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

def get_books_links(start_page=1, end_page=sys.maxsize, base_url='https://tululu.org/l55/'):
    books_href = []
    for page in range(start_page, end_page):
        url = urljoin(base_url, str(page))
        response = requests.get(url, verify=False, allow_redirects=False)
        response.raise_for_status()
        if not response.is_redirect:
            soup = BeautifulSoup(response.text, 'lxml')

            content = soup.find('div', id='content')
            book_cards = content.find_all('table', class_='d_book')
            books_href += [urljoin(url, card.find('a')['href']) for card in book_cards]
        else: break
    return books_href

def main():
    parser = argparse.ArgumentParser(
        description='Программа скачивает книги с сайта'
    )
    parser.add_argument('--start_page', help='Стартовая страница для парсинга', type=int, default=1)
    parser.add_argument('--end_page', help='Страница окончания парсинга(не парсится)', type=int, default=sys.maxsize)
    args = parser.parse_args()

    books_links = get_books_links(args.start_page, args.end_page)
    for url in books_links:
        print(url)
        id = url.split('/')[-2].lstrip('b')
        response = requests.get(url, verify=False, allow_redirects=False)
        response.raise_for_status()
        if not response.is_redirect:
            soup = BeautifulSoup(response.text, 'lxml')

            content = soup.select_one('#content')
            
            selector_title = 'h1 > a'
            selector_author = 'h1 a'
            title = content.select_one(selector_title).previous_sibling.strip().strip(':').strip().capitalize()
            author = content.select_one(selector_author).text.strip().title()
            
            image_selector = '.bookimage img [src]'
            image_src = content.select_one(image_selector)
            url = 'https://tululu.org/txt.php?id={}'.format(id)  
            image_url = urljoin(url, image_src)

            comments_selector = '.texts .black'
            comments = [comment.get_text() for comment in content.select(comments_selector)]
            
            genres_selector = 'span.d_book a'
            genres = [genre.get_text() for genre in content.select(genres_selector)]
            
            book_dict = {
                'title': title,
                'author': author,
                'img src': image_url,
                'comments': comments,
                'genres': genres,
            }

            with codecs.open("books.json", "a", encoding='utf8') as books_file:
                json.dump(book_dict, books_file, ensure_ascii=False)
            download_txt(url, '{}. {}.txt'.format(id, title))
            download_image(image_url, image_url.split('/')[-1])

if __name__ == '__main__':
    main()
