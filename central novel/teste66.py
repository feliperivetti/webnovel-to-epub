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


def get_chapters_link(main_url, chapters_quantity):
    response = requests.get(main_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    chapters_tables = soup.find_all('div', class_='eplister eplisterfull')

    chapters_links = []
    for item in chapters_tables:
        teste = item.find_all('a')
        for link in teste:
            chapters_links.append(link['href'])
    
    chapters_url_list = []
    for i in range(chapters_quantity):
        chapters_url_list.append(chapters_links[-i-1])

    return chapters_url_list


def get_book_metadata(main_url):
    response = requests.get(main_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    book_metadata_div = soup.find('div', class_='bigcontent nobigcv')
    book_title = book_metadata_div.find('h1', class_='entry-title').text

    info_content_div = book_metadata_div.find('div', class_='info-content')
    book_author = info_content_div.find_all('span')[2].text

    entry_content_div = soup.find('div', class_='entry-content')
    book_description = entry_content_div.find('p').text

    book_cover_link = book_metadata_div.find('img')['src']

    return [book_title, book_author, book_description, book_cover_link]



# Código Usado para Testes
# main_url = 'https://centralnovel.com/series/shadow-slave-20230928/'
# chapters_quantity = 5
# teste = get_book_metadata(main_url)

# print(teste)


