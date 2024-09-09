from ebooklib import epub
from auxiliar import MyPandaNovelBook, MyRoyalRoadBook
import requests
import os

# livro_teste1 = MyPandaNovelBook("https://pandanovel.co/panda-novel/shadow-slave", 20, 15)
# book_metadata = livro_teste1.get_book_metadata()
# chapters_url_list = livro_teste1.get_chapters_link()

# print(chapters_url_list)

# livro_teste2 = MyRoyalRoadBook("https://www.royalroad.com/fiction/36735/the-perfect-run", 20, 15)
# book_metadata = livro_teste2.get_book_metadata()
# chapters_url_list = livro_teste2.get_chapters_link()

# print(book_metadata[-1])





def create_epub(metadata_list, chapters_url_list, id, language):

    # Criando o Objeto epub
    book = epub.EpubBook()

    # Meta Dados Obrigatórios
    book.set_identifier(id)
    book.set_title(metadata_list[0].text)
    book.set_language(language)

    # Meta Dados Opcionais
    book.add_author(metadata_list[1])


    # Criando seção de informaões importantes (descrição e sobre)
    book_desc = epub.EpubHtml(title='Description', file_name='description.xhtml')
    book_desc.content = str(metadata_list[2])

    book_about = epub.EpubHtml(title='About', file_name='about.xhtml')
    book_about.content = '<h1>About this book</h1><p>Hello, this is epub was created as a personal project. Repository at https://github.com/1loadz</p>'

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
        infos = get_chapter_content(url, 'chapter-title', 'content')

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




livro_teste1 = MyPandaNovelBook("https://pandanovel.co/panda-novel/shadow-slave", 20, 15)
book_metadata = livro_teste1.get_book_metadata()
chapters_url_list = livro_teste1.get_chapters_link()

# create_epub(book_metadata, chapters_url_list, 'teste', 'en')


# refinar essa funcao chamada create epub