"""Módulo Auxiliar

Esse módulo foi utilizado para implementar classes e métodos que serão utilizados
no módulo main. Dessa forma, os módulos ficam mais organizados e com um propósito
mais específico, além de facilitar o entendimento do código.
"""

import requests
import os
from ebooklib import epub
from bs4 import BeautifulSoup
from abc import ABC, abstractmethod


class MyBook():
    """SuperClasse"""
    def __init__(self, main_url, chapters_quantity, start_chapter=1):
        self._main_url = main_url
        self._chapters_quantity = chapters_quantity
        self._start_chapter = start_chapter

        # Devo criar getter/setter para esses atributos?

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
    

    def create_epub(self, id: str, language: str) -> None:

        # Fonte das Informações Necessárias
        metadata_list = self.get_book_metadata()
        chapters_url_list = self.get_chapters_link()

        # Criando o Objeto epub
        book = epub.EpubBook()

        # Meta Dados Obrigatórios
        book.set_identifier(id)
        book.set_title(metadata_list[0].text)
        book.set_language(language)

        # Meta Dados Opcionais
        book.add_author(metadata_list[1])


        # Criando seção de informações importantes (descrição e sobre)
        book_desc = epub.EpubHtml(title='Description', file_name='description.xhtml')
        book_desc.content = str(metadata_list[2])

        book_about = epub.EpubHtml(title='About', file_name='about.xhtml')
        book_about.content = '<h1>About this book</h1><p>Hello, this epub was created as a personal project. Repository at https://github.com/1loadz</p>'

        book.add_item(book_desc)
        book.add_item(book_about)



        # Adicionando a Capa do Livro
        book_cover_link = metadata_list[3]
        book_cover_img = requests.get(book_cover_link)

        with open('book_cover_img.jpg', 'wb') as f:
            noop = f.write(book_cover_img.content)

        book.set_cover("image.jpg", open('book_cover_img.jpg', 'rb').read())



        # Bloco de Código que Gera os Capítulos Dinamicamente
        num_capitulos = len(chapters_url_list)
        variables_dict = {}

        for i in range(num_capitulos):
            url = chapters_url_list[i]
            infos = self.get_chapter_content(url, 'span', 'chapter-title', 'content')

            title = infos[0]
            content = infos[1]

            key = f'chapter{i+1}'
            variables_dict[key] = epub.EpubHtml(title=title.text, file_name=f'ch{i+1}.xhtml', lang='en')
            variables_dict[key].content = f"<html><body><h1>{title}</h1>{str(content)}</body></html>"
            book.add_item(variables_dict[key])
            os.system('cls')
            print(f"Downloads: {i+1}/{num_capitulos}")



        # Criando a Table of Contents
        book.toc = ((epub.Section('Important Infos'), (book_desc, book_about)), 
                (epub.Section('Contents'), tuple(variables_dict.values())))


        # Adicionando Arquivos de Navegação
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())


        # Criando a spine
        book.spine = ['nav', book_desc, book_about]
        book.spine += list(variables_dict.values())

        # Deletando o Arquivo da Imagem (ele já foi utilizado)
        os.remove('book_cover_img.jpg')

        # Criando o Arquivo .epub
        epub.write_epub(f'{metadata_list[0].text}.epub', book, {})
    


# talvez eu deva criar uma funcao ou um decorator para:
 # response = requests.get(main_url)
 # soup = BeautifulSoup(response.text, 'html.parser'

# refinar a funcao create_epub, acho que ela faz muita coisa




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
        # return {'book_title': book_title, 'book_author': book_author, 'book_description': book_description, 'book_cover_link': book_cover_link}
    
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
        # return {'novel_title': novel_title, 'novel_author': novel_author, 'novel_description': novel_description, 'novel_cover_link': novel_cover_link}


    def get_chapters_link(self):
        chapters_url_list = []
        title = self._main_url.split('/')[-1]
        for i in range(self._chapters_quantity):
            url = f'https://novelfire.noveljk.org/book/{title}/chapter-{i+self._start_chapter}'
            chapters_url_list.append(url)
            
        return chapters_url_list
    


class MyCentralNovelBook(MyBook):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
    
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



if __name__ == '__main__':
    livro1 = MyPandaNovelBook('url', 20, 10)
    print(type(livro1))
