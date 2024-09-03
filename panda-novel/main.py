import requests
from bs4 import BeautifulSoup
from ebooklib import epub
from auxiliar import get_chapters_link
from auxiliar import get_novel_metadata
from auxiliar import get_chapter_content
import os


# Link da Pagina Principal do Livro, Quantidade de Capítulos Desejados e Função Criada por Mim 
# main_url = input("Link da Página do Livro (Panda Novel): ")
# start_chapter = int(input("Capítulo Inicial: "))
# chapters_quantity = int(input("Quantidade de Capítulos: "))
# main_url = 'https://pandanovel.co/panda-novel/shadow-slave'
main_url = 'https://pandanovel.co/panda-novel/supreme-magus'
start_chapter = 20
chapters_quantity = 15


chapters_url_list = get_chapters_link(main_url, chapters_quantity, start_chapter)
metadata_list = get_novel_metadata(main_url)


# Criando o Objeto epub
book = epub.EpubBook()


# Meta Dados Obrigatórios
book.set_identifier('teste')
book.set_title(metadata_list[0].text)
book.set_language('en')

# Meta Dados Opcionais
book.add_author(metadata_list[1])


# Criando seção de informaões importantes (descrição e sobre)
book_desc = epub.EpubHtml(title='Description', file_name='description.xhtml')
book_desc.content = str(metadata_list[2])

book_about = epub.EpubHtml(title='About', file_name='about.xhtml')
book_about.content = '<h1>About this book</h1><p>Hello, this is epub was created as a personal project. Follow me on instagram @_feliperpp</p>'

book.add_item(book_desc)
book.add_item(book_about)



# Código pra pegar a Capa do Livro
book_cover_link = get_novel_metadata(main_url)[3]
book_cover_img = requests.get(book_cover_link)

with open('book_cover_img.jpg', 'wb') as f:
    noop = f.write(book_cover_img.content)

book.set_cover("image.jpg", open('book_cover_img.jpg', 'rb').read())



# Bloco de Código que Gera os Capítulos
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


print('Download Realizado Com Sucesso!')


# DOCUMENTAR MELHOR O CODIGO
# ENTENDER MELHOR COMO FUNCIONA A NAV E A SPINE
