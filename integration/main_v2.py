from auxiliar_v2 import MyBook, MyPandaNovelBook, MyRoyalRoadBook


url = 'https://pandanovel.co/panda-novel/a-regressors-tale-of-cultivation'
livro_teste2 = MyPandaNovelBook(url, 50, 49)
# book_metadata = livro_teste1.get_book_metadata()
# chapters_url_list = livro_teste1.get_chapters_link()
# print(chapters_url_list)

livro_teste2.create_epub('teste02', 'en')
