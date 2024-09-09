import requests
from bs4 import BeautifulSoup
from abc import ABC, abstractmethod


class MyBook():
    def __init__(self, main_url, chapters_quantity, start_chapter=1):
        self._main_url = main_url
        self._chapters_quantity = chapters_quantity
        self._start_chapter = start_chapter

    @abstractmethod
    def get_book_metadata(self):
        pass
    
    @abstractmethod
    def get_chapters_link(self):
        pass

    def get_chapter_content(self, url, title_tag, title_class, main_content_id):
        response = requests.get(url)

        # Criando o Objeto Beautiful Soup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Filtrando o Conteúdo Desejado de Acordo com Tags e Classes HTML
        chapter_title = soup.find(title_tag, class_ = title_class) #chapter-title
        main_content_div = soup.find('div', id = main_content_id) #content
        # main_content_div = soup.find('div', class_= main_content_class) #"chapter-inner chapter-content"
        
        # ajustar para que a funcao possa receber tanto class quanto id
        # atualmente so recebe um dos dois

        return [chapter_title, main_content_div]
    


#talvez eu deva criar um funcao para:
# response = requests.get(main_url)
# soup = BeautifulSoup(response.text, 'html.parser')




class MyRoyalRoadBook(MyBook):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def get_book_metadata(self):
        response = requests.get(self._main_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        book_metadata_div = soup.find('div', class_='row fic-header')
        book_title = book_metadata_div.find('h1')
        book_author = book_metadata_div.find('a')
        book_description = soup.find('div', class_='description')
        book_cover_link = book_metadata_div.find('img')['src']

        return [book_title, book_author, book_description, book_cover_link]
    
    def get_chapters_link(self):
        chapters_url_list = []
        response = requests.get(self._main_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        chapters_table = soup.find_all('tr', class_='chapter-row')

        for i in range(self._chapters_quantity):
            data_url = chapters_table[i+self._start_chapter]['data-url']
            final_url = 'https://www.royalroad.com' + data_url
            chapters_url_list.append(final_url)
        return chapters_url_list
    
    

class MyPandaNovelBook(MyBook):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
    
    def get_book_metadata(self):
        response = requests.get(self._main_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        novel_metadata_div = soup.find('div', class_='header-body container')
        novel_info = novel_metadata_div.find('div', class_='novel-info')

        novel_title = novel_info.find('h1')
        novel_author = novel_info.find('div', class_='author').find('a')['title']
        novel_description = soup.find('div', class_='inner')

        novel_cover_link = novel_metadata_div.find('img')['data-src']

        return [novel_title, novel_author, novel_description, novel_cover_link]

    def get_chapters_link(self):
        chapters_url_list = []
        title = self._main_url.split('/')[-1]
        for i in range(self._chapters_quantity):
            url = f'https://novelfire.noveljk.org/book/{title}/chapter-{i+self._start_chapter}'
            chapters_url_list.append(url)
            
        return chapters_url_list
    



# Funçao alternativa usada no PandaNovel
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