from classes.classes import MyBook, MyPandaNovelBook, MyRoyalRoadBook
import streamlit as st

def main() -> None:

    st.set_page_config(page_title="Book Downloader", page_icon=":book:")
    st.write("# Novel Downloader")

    main_url = st.text_input("Enter the book URL:", key="book_url")
    chapters_quantity = st.number_input("Enter the number of chapters to download:", min_value=1, value=10, key="chapters_quantity")
    start_chapter = st.number_input("Enter the starting chapter number:", min_value=1, value=1, key="start_chapter")

    infos = {
        "main_url": main_url,
        "chapters_quantity": chapters_quantity,
        "start_chapter": start_chapter,
    }

    if st.button("Download Book"):
        if main_url and chapters_quantity > 0 and start_chapter > 0:
            try:
                livro_teste = MyPandaNovelBook(**infos)
                livro_teste.create_epub('teste01', 'en')
                # st.success("Book downloaded successfully!")
            except Exception as e:
                st.error(f"An error occurred: {e}")
        else:
            st.warning("Please fill in all fields correctly.")

    # livro_teste2 = MyPandaNovelBook(**infos)
    # book_metadata = livro_teste2.get_book_metadata()   
    # print(book_metadata[0])
    # chapters_url_list = livro_teste1.get_chapters_link()
    # print(chapters_url_list)
    # livro_teste2.create_epub('teste02', 'en')


    # infos3 = {
    #             "main_url": "https://www.royalroad.com/fiction/36735/the-perfect-run",
    #             "chapters_quantity": 5,
    #             "start_chapter": 1,
    #         }

    # livro_teste3 = MyRoyalRoadBook(**infos3)
    # livro_teste3.create_epub('teste03', 'en')


if __name__ == '__main__':
    main()
