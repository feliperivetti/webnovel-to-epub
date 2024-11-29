from auxiliar import MyBook, MyPandaNovelBook, MyRoyalRoadBook

def main() -> None:

    infos = {
                "main_url": "https://pandanovel.co/panda-novel/data-driven-daoist",
                "chapters_quantity": 5,
                "start_chapter": 1,
            }

    livro_teste2 = MyPandaNovelBook(**infos)
    # book_metadata = livro_teste2.get_book_metadata()   
    # print(book_metadata[0])
    # chapters_url_list = livro_teste1.get_chapters_link()
    # print(chapters_url_list)

    livro_teste2.create_epub('teste02', 'en')


if __name__ == '__main__':
    main()
