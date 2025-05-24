from auxiliar import MyBook, MyPandaNovelBook, MyRoyalRoadBook

def main() -> None:


    infos = {
                "main_url": "https://pandanovel.co/panda-novel/cultivation-is-creation",
                "chapters_quantity": 50,
                "start_chapter": 55,
            }

    livro_teste2 = MyPandaNovelBook(**infos)
    # book_metadata = livro_teste2.get_book_metadata()   
    # print(book_metadata[0])
    # chapters_url_list = livro_teste1.get_chapters_link()
    # print(chapters_url_list)
    livro_teste2.create_epub('teste02', 'en')


    # infos3 = {
    #             "main_url": "https://www.royalroad.com/fiction/36735/the-perfect-run",
    #             "chapters_quantity": 5,
    #             "start_chapter": 1,
    #         }

    # livro_teste3 = MyRoyalRoadBook(**infos3)
    # livro_teste3.create_epub('teste03', 'en')


if __name__ == '__main__':
    main()
