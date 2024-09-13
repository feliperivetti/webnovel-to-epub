from auxiliar_v2 import MyBook, MyPandaNovelBook, MyRoyalRoadBook


livro_teste1 = MyPandaNovelBook("https://pandanovel.co/panda-novel/shadow-slave", 5, 15)
# book_metadata = livro_teste1.get_book_metadata()
# chapters_url_list = livro_teste1.get_chapters_link()
# print(chapters_url_list

livro_teste1.create_epub('teste01', 'en')


# refinar essa funcao chamada create epub
# implementar suporte à estilizacao via css
