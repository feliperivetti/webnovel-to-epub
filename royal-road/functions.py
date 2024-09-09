import requests
from bs4 import BeautifulSoup


def get_chapter_content(url, title_tag, main_content_class):
    response = requests.get(url)

    # Criando o Objeto Beautiful Soup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Filtrando o Conteúdo Desejado de Acordo com Tags e Classes HTML
    chapter_title = soup.find(title_tag) #h1
    main_content_div = soup.find('div', class_= main_content_class) #"chapter-inner chapter-content"

    return (chapter_title, main_content_div)


def get_chapters_link(main_url, chapters_quantity, start_chapter=1):
    chapters_url_list = []
    response = requests.get(main_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    chapters_table = soup.find_all('tr', class_='chapter-row')

    for i in range(chapters_quantity):
        data_url = chapters_table[i+start_chapter]['data-url']
        final_url = 'https://www.royalroad.com' + data_url
        chapters_url_list.append(final_url)
    return chapters_url_list


def get_book_metadata(main_url):
    response = requests.get(main_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    book_metadata_div = soup.find('div', class_='row fic-header')
    book_title = book_metadata_div.find('h1').text
    book_author = book_metadata_div.find('a').text
    book_description = soup.find('div', class_='description')

    book_cover_link = book_metadata_div.find('img')['src']

    return [book_title, book_author, book_description, book_cover_link]



# Código Usado para Testes
if __name__ == '__main__':
    main_url = 'https://www.royalroad.com/fiction/69480/the-land-of-broken-roads'
    get_book_metadata(main_url)
