import requests
from bs4 import BeautifulSoup

def get_chapter_content(url):
    response = requests.get(url)

    """
    with open('teste_royalroad.html', 'w', encoding='utf-8') as f:
        f.write(response.text)

    with open('teste_royalroad.html', 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    """

    # Criando o Objeto Beautiful Soup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Filtrando o Conteúdo Desejado
    chapter_title = soup.find('h1')
    main_content_div = soup.find('div', class_="chapter-inner chapter-content")


    # Escrevendo um Arquivo .txt com o Conteúdo Desejado
    with open('teste_royalroad.txt', 'w', encoding='utf-8') as f:
        f.write(chapter_title.text)
        f.write(main_content_div.text)


# Chamando a Função
get_chapter_content('https://www.royalroad.com/fiction/36735/the-perfect-run/chapter/569531/2-story-branching')