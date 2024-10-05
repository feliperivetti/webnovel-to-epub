import requests
import os
from ebooklib import epub
from bs4 import BeautifulSoup
from abc import ABC, abstractmethod


# FUNCAO PARA SETAR METADADOS (ID, TITLE, LANGUAGE, AUTHOR)
# FUNCAO PARA SETAR INFORMACOES IMPORTANTES (DESC E SOBRE)
# FUNCAO PARA ADICIONAR A CAPA
# FUNCAO PARA GERACAO DE CAPITULOS DINAMICAMENTE
# FUNCAO QUE CRIA A TOC
# FUNCAO PARA ADICIONAR ARQUIVOS DE NAVEGACAO
# FUNCAO PARA CRIAR A SPINE

# FUNCAO QUE UTILIZA TUDO ISSO


metadata_list = self.get_book_metadata()
def set_metadata(self, book_object: epub.EpubBook, metadata_list: list, id: str, language: str) -> None:
    # Meta Dados Obrigatórios
    book_object.set_identifier(id)
    book_object.set_title(metadata_list[0].text)
    book_object.set_language(language)

    # Meta Dados Opcionais
    book_object.add_author(metadata_list[1])


def set_important_infos(self, book_object: epub.EpubBook, metadata_list: list) -> None:
    # Criando seção de informações importantes (descrição e sobre)
        book_desc = epub.EpubHtml(title='Description', file_name='description.xhtml')
        book_desc.content = str(metadata_list[2])

        book_about = epub.EpubHtml(title='About', file_name='about.xhtml')
        book_about.content = '<h1>About this book</h1><p>Hello, this epub was created as a personal project. Repository at https://github.com/1loadz</p>'

        book_object.add_item(book_desc)
        book_object.add_item(book_about)


def set_cover(self, book_object: epub.EpubBook, metadata_list: list) -> None:
    # Adicionando a Capa do Livro
    book_cover_link = metadata_list[3]
    book_cover_img = requests.get(book_cover_link)

    with open('book_cover_img.jpg', 'wb') as f:
        noop = f.write(book_cover_img.content)

    book_object.set_cover("image.jpg", open('book_cover_img.jpg', 'rb').read())


def set_chapters_content(self, book_object: epub.EpubBook, chapters_url_list: list) -> None:
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
        book_object.add_item(variables_dict[key])
        os.system('cls')
        print(f"Downloads: {i+1}/{num_capitulos}")

        return variables_dict



# continuar daqui pra baixo
"""def set_toc()
    # Criando a Table of Contents
    book.toc = ((epub.Section('Important Infos'), (book_desc, book_about)), 
               (epub.Section('Contents'), tuple(variables_dict.values())))


def create_epub(self, id: str, language: str) -> None:

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
        epub.write_epub(f'{metadata_list[0].text}.epub', book, {})"""




