import requests
from bs4 import BeautifulSoup
from ebooklib import epub
from teste66 import get_chapters_link
from teste66 import get_book_metadata
from teste66 import get_chapter_content
import os



# Link da Pagina Principal do Livro, Quantidade de Capítulos Desejados e Função Criada por Mim 
# main_url = input("Link da Página do Livro (Royal Road): ")
# chapters_quantity = int(input("Quantidade de Capítulos: "))
main_url = 'https://centralnovel.com/series/shadow-slave-20230928/'
chapters_quantity = 10


chapters_url_list = get_chapters_link(main_url, chapters_quantity)
metadata_list = get_book_metadata(main_url)

print(chapters_url_list)
print(metadata_list)


# Criando o Objeto epub
book = epub.EpubBook()


# Meta Dados Obrigatórios
book.set_identifier('teste')
book.set_title(metadata_list[0])
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
book_cover_link = get_book_metadata(main_url)[3]
book_cover_img = requests.get(book_cover_link)

with open('book_cover_img.jpg', 'wb') as f:
    noop = f.write(book_cover_img.content)

book.set_cover("image.jpg", open('book_cover_img.jpg', 'rb').read())



# Bloco de Código que Gera os Capítulos
num_capitulos = len(chapters_url_list)
variables_dict = {}

for i in range(num_capitulos):
    url = chapters_url_list[i]
    infos = get_chapter_content(url, 'h1', 'chapter-inner chapter-content')

    title = infos[0]
    content = infos[1]

    key = f'chapter{i+1}'
    variables_dict[key] = epub.EpubHtml(title=title.text, file_name=f'ch{i+1}.xhtml', lang='en')
    variables_dict[key].content = f"<html><body><h1>{title}</h1>{str(content)}</body></html>"
    book.add_item(variables_dict[key])



# Criando a Table of Contents
book.toc = ((epub.Section('Important Infos'), (book_desc, book_about)), 
            (epub.Section('Chapters'), tuple(variables_dict.values())))


# Adicionando Arquivos de Navegação
book.add_item(epub.EpubNcx())
book.add_item(epub.EpubNav())


# Criando a spine
book.spine = ['nav', book_desc, book_about]
book.spine += list(variables_dict.values())

# Criando o Arquivo .epub
epub.write_epub(f'{metadata_list[0]}.epub', book, {})

# Deletando o Arquivo da Imagem (ele já foi utilizado)
os.remove('book_cover_img.jpg')


print('Download Realizado Com Sucesso!')



# DELETAR O ARQUIVO DE IMAGEM AO FINAL DO PROGRAMA
# ADICIONAR UM TITULO NO INICIO DE CADA CAPITULO
# DOCUMENTAR MELHOR O CODIGO
# ENTENDER MELHOR COMO FUNCIONA A NAV E A SPINE
# CONTINUAR PROCURANDO OUTROS SITES QUE EU CONSIGA FAZER WEB SCRAPING SEM MUITOS PROBLEMAS
