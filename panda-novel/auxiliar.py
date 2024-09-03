import requests
from bs4 import BeautifulSoup


def get_chapter_content(url, title_class, main_content_class):
    response = requests.get(url)

    # Criando o Objeto Beautiful Soup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Filtrando o Conteúdo Desejado de Acordo com Tags e Classes HTML
    chapter_title = soup.find('span', class_ = title_class) #chapter-title
    main_content_div = soup.find('div', id = main_content_class) #content

    return [chapter_title, main_content_div]


"""
def get_chapters_link(main_url, chapters_quantity):
    chapters_url_list = []
    for i in range((chapters_quantity // 100) + 1):
        url = main_url + f'/chapters?page={i+1}'
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        chapters_list = soup.find('ul', class_='chapter-list')
        partial_list = chapters_list.find_all('a')

        for item in partial_list:
            chapters_url_list.append(item['href'])

    return chapters_url_list[:chapters_quantity]
"""

def get_chapters_link(main_url, chapters_quantity, start_chapter=1):
    chapters_url_list = []
    title = main_url.split('/')[-1]
    for i in range(chapters_quantity):
        url = f'https://novelfire.noveljk.org/book/{title}/chapter-{i+start_chapter}'
        chapters_url_list.append(url)
        
    return chapters_url_list



# continuar alterando essa funcao para o site panda novel
def get_novel_metadata(main_url):
    response = requests.get(main_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    novel_metadata_div = soup.find('div', class_='header-body container')
    novel_info = novel_metadata_div.find('div', class_='novel-info')

    novel_title = novel_info.find('h1')
    novel_author = novel_info.find('div', class_='author').find('a')['title']
    novel_description = soup.find('div', class_='inner')

    novel_cover_link = novel_metadata_div.find('img')['data-src']

    return [novel_title, novel_author, novel_description, novel_cover_link]



# Código Usado para Testes
# main_url = 'https://novelfire.noveljk.org/book/shadow-slave/chapter-2'
# a = get_chapter_content(main_url, 'chapter-title', 'content')
# print(a[0].text)

