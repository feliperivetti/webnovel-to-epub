from auxiliar import MyBook, MyPandaNovelBook, MyRoyalRoadBook

def main() -> None:

    infos = {
                "main_url": 'https://pandanovel.co/panda-novel/a-regressors-tale-of-cultivation',
                "chapters_quantity": 5,
                "start_chapter": 180,
            }

    livro_teste2 = MyPandaNovelBook(**infos)
    # book_metadata = livro_teste1.get_book_metadata()
    # chapters_url_list = livro_teste1.get_chapters_link()
    # print(chapters_url_list)

    livro_teste2.create_epub('teste02', 'en')


if __name__ == '__main__':
    main()
