import os
import json
import requests
import codecs
import argparse
import sys
from time import sleep
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urljoin
from urllib.error import HTTPError
from tqdm import tqdm


def get_response(url):
    try:
        response = requests.get(url, verify=False, allow_redirects=False)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(e, file=sys.stderr)
    except requests.exceptions.ConnectionError as e:
        print(e, file=sys.stderr)
        sleep(10)
        return get_response(url)
    else:
        return response


def download_txt(url, filename, folder='books/'):
    """Функция для скачивания текстовых файлов.
    Args:
        url (str): Cсылка на текст, который хочется скачать.
        filename (str): Имя файла, с которым сохранять.
        folder (str): Папка, куда сохранять.
    Returns:
        str: Путь до файла, куда сохранён текст.
    """
    print(url) 
    text_book_response = get_response(url)
    if text_book_response.is_redirect:
        print(
            'Error downloading book text from {}!\
            File not found!'.format(url),
            file=sys.stderr
        )
        return None

    os.makedirs(folder, exist_ok=True)
    filename = os.path.join(folder, sanitize_filename(filename))
    with open(filename, 'wb') as file:
        file.write(text_book_response.content)
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
    image_book_response = get_response(url)
    if not image_book_response.ok:
        print(
            'Error downloading book image from {}!\
            File not found!'.format(url),
            file=sys.stderr
        )

    os.makedirs(folder, exist_ok=True)
    filename = os.path.join(folder, sanitize_filename(filename))
    with open(filename, 'wb') as file:
        file.write(image_book_response.content)
    return filename


def get_books_links(start_page=1, end_page=sys.maxsize,
                    base_url='https://tululu.org/l55/'):
    books_href = []
    for page in range(start_page, end_page):
        url = urljoin(base_url, str(page))
        page_response = get_response(url)
        if page_response.is_redirect:
            print('Error: page books {} not found! Break.'.format(page),
                  file=sys.stderr)
            break

        soup = BeautifulSoup(page_response.text, 'lxml')
        content = soup.find('div', id='content')
        book_cards = content.find_all('table', class_='d_book')
        books_href += [urljoin(url, card.find('a')['href'])
                       for card in book_cards]
    return books_href


def parse_book_page(book_url, page):
    soup = BeautifulSoup(page, 'lxml')

    content = soup.select_one('#content')

    selector_title = 'h1 > a'
    selector_author = 'h1 a'
    title = content.select_one(selector_title).previous_sibling
    title = title.strip().strip(':').strip().capitalize()
    author = content.select_one(selector_author).text.strip().title()

    image_selector = '.bookimage img'
    image_src = content.select_one(image_selector)['src']
    image_url = urljoin(book_url, image_src)

    comments_selector = '.texts .black'
    comments = [comment.get_text() for comment
                in content.select(comments_selector)]

    genres_selector = 'span.d_book a'
    genres = [genre.get_text() for genre
              in content.select(genres_selector)]

    return {
        'title': title,
        'author': author,
        'img_src': image_url,
        'comments': comments,
        'genres': genres,
    }


def add_books_to_json(books_info, dest_folder, json_path):
    json_file = os.path.join(dest_folder, json_path)
    os.makedirs(os.path.dirname(json_file), exist_ok=True)
    with codecs.open(json_file, "a", encoding='utf8') as books_file:
        json.dump(books_info, books_file, ensure_ascii=False)


def download_book(book_url, book_page, dest_folder='',
                  skip_imgs=False, skip_txt=False,
                  json_path='books.json'):
    id = book_url.split('/')[-2].lstrip('b')
    book_info = parse_book_page(book_url, book_page)
    if not skip_txt:
        book_info['book_path'] = download_txt(
            urljoin(book_url, '/txt.php?id={}'.format(id)),
            '{}. {}.txt'.format(id, book_info['title']),
            os.path.join(dest_folder, 'books/')
        )
    if not skip_imgs:
        book_info['img_src'] = download_image(
            book_info['img_src'],
            book_info['img_src'].split('/')[-1],
            os.path.join(dest_folder, 'images/')
        )
    return book_info


def download_books(books_links, dest_folder='',
                   skip_imgs=False, skip_txt=False,
                   json_path='books.json'):
    books_info = []

    for url in tqdm(books_links, file=sys.stdout):
        book_page_response = get_response(url)
        if book_page_response.is_redirect:
            print(
                'Error getting book page from {}!\
                Page not found!'.format(url),
                file=sys.stderr
            )
            continue
        books_info.append(
            download_book(url, book_page_response.text, dest_folder,
                      skip_imgs, skip_txt, json_path)
        )
    add_books_to_json(books_info, dest_folder, json_path)


def create_parser():
    parser = argparse.ArgumentParser(
        description='Программа скачивает книги с сайта'
    )
    parser.add_argument('--start_page', help='Стартовая страница',
                        type=int, default=1)
    parser.add_argument('--end_page', help='Конечная страница(не скачивается)',
                        type=int, default=sys.maxsize)
    parser.add_argument('--dest_folder', help='Каталог для загрузки',
                        default='download')
    parser.add_argument('--skip_imgs', help='Признак пропуска картинок',
                        action='store_true')
    parser.add_argument('--skip_txt', help='Признак пропуска текстов',
                        action='store_true')
    parser.add_argument('--json_path', help='Путь к файлу результатов',
                        default='books.json')
    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()
    books_links = get_books_links(args.start_page, args.end_page)
    download_books(books_links, args.dest_folder, args.skip_imgs,
                   args.skip_txt, args.json_path)


if __name__ == '__main__':
    main()
