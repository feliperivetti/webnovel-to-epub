import pytest
from bs4 import BeautifulSoup

from src.classes.pandanovel_book import MyPandaNovelBook
from src.classes.novelsbr_book import MyNovelsBrBook
from src.classes.centralnovel_book import MyCentralNovelBook

PANDA_URL = "https://novelphoenix.com/novel/shadow-slave"
CENTRAL_URL = "https://centralnovel.com/series/shadow-slave-20260913/"
NOVELSBR_URL = "https://novels-br.com/novels/escravo-das-sombras"
NOVELSBR_CHAPTER = NOVELSBR_URL + "/volume-unico-capitulo-1--o-pesadelo-comeca"

class TestPandaNovelScraper:
    def test_get_book_metadata(self, mock_cloudscraper, pandanovel_toc_html):
        mock_scraper, mock_response = mock_cloudscraper
        mock_response.text = pandanovel_toc_html
        
        book = MyPandaNovelBook(PANDA_URL, 10, 1)
        metadata = book.get_book_metadata()
        
        assert metadata.book_title == "Shadow Slave"
        assert metadata.book_author == "Guiltythree"
        assert metadata.book_cover_link == "https://novelphoenix.com/server-1/shadow-slave.jpg"
        assert "Growing up in poverty, Sunny never expected anything good from life." in metadata.book_description

    def test_get_chapters_link(self, mock_cloudscraper):
        # This provider generates URLs; it does not request a TOC.
        book = MyPandaNovelBook(PANDA_URL, 5, 1)
        links = book.get_chapters_link()
        
        assert len(links) == 5
        assert links[0] == "https://novelphoenix.com/novel/shadow-slave/chapter-1"
        assert links[-1] == "https://novelphoenix.com/novel/shadow-slave/chapter-5"

    @pytest.mark.parametrize("url", [
        "https://novelfire.net/book/shadow-slave",
        "https://novelfire.net/book/shadow-slave/",
        "https://novelfire.net/book/shadow-slave?noti=1",
        "https://novelfire.net/book/shadow-slave/?noti=0",
    ])
    def test_migrated_chapter_urls_preserve_slug_and_range(self, mock_cloudscraper, url):
        book = MyPandaNovelBook(url, 2, 3)
        assert book.get_chapters_link() == [
            "https://novelphoenix.com/novel/shadow-slave/chapter-3",
            "https://novelphoenix.com/novel/shadow-slave/chapter-4",
        ]

    def test_welcome_modal_outside_chapter_is_not_extracted(self, mock_cloudscraper, pandanovel_chap_html):
        _, response = mock_cloudscraper
        response.text = pandanovel_chap_html.replace("</body>", '''
            <div class="lnw-modal"><p>Welcome to Novel Phoenix !</p></div>
            <script>showWelcomeModal();</script>
            </body>''')
        book = MyPandaNovelBook(PANDA_URL, 1, 1)
        chapter = book.get_chapter_content(PANDA_URL + "/chapter-1")
        assert "Sunny decided to pamper himself." in chapter.content
        assert "Welcome to Novel Phoenix" not in chapter.content
        assert "showWelcomeModal" not in chapter.content

    def test_get_chapter_content(self, mock_cloudscraper, pandanovel_chap_html):
        mock_scraper, mock_response = mock_cloudscraper
        mock_response.text = pandanovel_chap_html
        
        book = MyPandaNovelBook(PANDA_URL, 10, 1)
        data = book.get_chapter_content(PANDA_URL + "/chapter-1")
        
        assert data.title == "Chapter 1 - 1: Nightmare Begins"
        assert "Sunny decided to pamper himself." in data.content
        assert "After all, his life was coming to an end." in data.content


class TestNovelsBrScraper:
    def test_get_book_metadata(self, mock_cloudscraper, novelsbr_toc_html):
        mock_scraper, mock_response = mock_cloudscraper
        mock_response.text = novelsbr_toc_html
        
        book = MyNovelsBrBook(NOVELSBR_URL, 10, 1)
        metadata = book.get_book_metadata()
        
        assert metadata.book_title == "Escravo das Sombras"
        assert metadata.book_author == "Guiltythree"
        assert metadata.book_cover_link == "https://novels-br.com/s3/escravo-das-sombras.jpeg"
        assert "Crescendo na pobreza, Sunny nunca esperou nada de bom da vida." in metadata.book_description

    def test_get_chapters_link(self, mock_cloudscraper, novelsbr_toc_html):
        mock_scraper, mock_response = mock_cloudscraper
        mock_response.text = novelsbr_toc_html
        
        # Fixture has 3 chapters. Try to ask for 5 starting from 1.
        book = MyNovelsBrBook(NOVELSBR_URL, 5, 1)
        links = book.get_chapters_link()
        
        # Should return all 3 available
        assert len(links) == 3
        assert links[0] == NOVELSBR_CHAPTER
        assert links[2] == NOVELSBR_URL + "/volume-unico-capitulo-3--as-cordas-do-destino"

    def test_get_chapter_content(self, mock_cloudscraper, novelsbr_chap_html):
        mock_scraper, mock_response = mock_cloudscraper
        mock_response.text = novelsbr_chap_html
        
        book = MyNovelsBrBook(NOVELSBR_URL, 10, 1)
        data = book.get_chapter_content(NOVELSBR_CHAPTER)
        
        assert data.title == "Capítulo 1: O Pesadelo Começa"
        assert "Afinal, sua vida estava chegando ao fim." in data.content
        assert "“Ah! Tão amargo!”" in data.content
        assert "Leia em https" not in data.content
        assert "page-link" not in data.content

    def test_removes_ads_and_hidden_paragraphs(self, mock_cloudscraper, novelsbr_chap_html):
        _, response = mock_cloudscraper
        response.text = novelsbr_chap_html.replace('<div class="chapter-content">', '''
            <div class="chapter-content">
              <div class="google-auto-placed">Ad junk</div>
              <p style="display: none">Hidden SEO text</p>
        ''', 1)
        book = MyNovelsBrBook(NOVELSBR_URL, 1, 1)
        data = book.get_chapter_content(NOVELSBR_CHAPTER)
        assert "Afinal, sua vida estava chegando ao fim." in data.content
        assert "Ad junk" not in data.content
        assert "Hidden SEO text" not in data.content


class TestCentralNovelScraper:
    def test_get_book_metadata(self, mock_cloudscraper, centralnovel_toc_html):
        mock_scraper, mock_response = mock_cloudscraper
        mock_response.text = centralnovel_toc_html
        
        book = MyCentralNovelBook(CENTRAL_URL, 10, 1)
        metadata = book.get_book_metadata()
        
        assert metadata.book_title == "Shadow Slave"
        assert metadata.book_author == "Guiltythree"
        assert metadata.book_cover_link == (
            "https://i2.wp.com/centralnovel.com/wp-content/uploads/2023/03/"
            "Shadow-Slave-capa-central.png?resize=370,500"
        )
        assert "Crescendo na pobreza, Sunny nunca esperou nada de bom da vida." in metadata.book_description

    def test_author_does_not_depend_on_metadata_field_order(self, mock_cloudscraper, centralnovel_toc_html):
        _, response = mock_cloudscraper
        soup = BeautifulSoup(centralnovel_toc_html, "lxml")
        author_field = soup.select_one('a[href*="/writer/"]').find_parent("span")
        author_field.extract()
        soup.select_one("div.info-content .spe").insert(0, author_field)
        response.text = str(soup)
        assert MyCentralNovelBook(CENTRAL_URL, 1, 1).get_book_metadata().book_author == "Guiltythree"

    @pytest.mark.parametrize("label", ["Autor:", "AUTOR :"])
    def test_author_without_link_uses_label_fallback(self, mock_cloudscraper, centralnovel_toc_html, label):
        _, response = mock_cloudscraper
        soup = BeautifulSoup(centralnovel_toc_html, "lxml")
        author_link = soup.select_one('a[href*="/writer/"]')
        author_link.find_parent("span").find("b").string = label
        author_link.unwrap()
        response.text = str(soup)
        assert MyCentralNovelBook(CENTRAL_URL, 1, 1).get_book_metadata().book_author == "Guiltythree"

    def test_missing_author_is_not_replaced_by_another_field(self, mock_cloudscraper, centralnovel_toc_html):
        _, response = mock_cloudscraper
        soup = BeautifulSoup(centralnovel_toc_html, "lxml")
        soup.select_one('a[href*="/writer/"]').find_parent("span").decompose()
        response.text = str(soup)
        assert MyCentralNovelBook(CENTRAL_URL, 1, 1).get_book_metadata().book_author == "Unknown Author"

    def test_author_link_text_is_not_blindly_stripped(self, mock_cloudscraper, centralnovel_toc_html):
        _, response = mock_cloudscraper
        soup = BeautifulSoup(centralnovel_toc_html, "lxml")
        soup.select_one('a[href*="/writer/"]').string = "Autor: Nome artístico"
        response.text = str(soup)
        assert MyCentralNovelBook(CENTRAL_URL, 1, 1).get_book_metadata().book_author == "Autor: Nome artístico"

    @pytest.mark.parametrize("start,expected_numbers", [(1, [1, 2, 3]), (2, [2, 3]), (4, [])])
    def test_get_chapters_link(self, mock_cloudscraper, centralnovel_toc_html, start, expected_numbers):
        mock_scraper, mock_response = mock_cloudscraper
        mock_response.text = centralnovel_toc_html
        
        # The fixture has 3 chapters.
        # Central scraper checks for total available logic.
        book = MyCentralNovelBook(CENTRAL_URL, 5, start)
        links = book.get_chapters_link()
        
        assert links == [f"https://centralnovel.com/shadow-slave-capitulo-{n}/" for n in expected_numbers]

    def test_direct_pdf_link_does_not_increase_available_chapters(self, mock_cloudscraper, centralnovel_toc_html):
        _, response = mock_cloudscraper
        soup = BeautifulSoup(centralnovel_toc_html, "lxml")
        row = soup.select_one("div.eplister li")
        for href in ("/shadow-slave-capitulo-4/pdf/?download=1", "/chapter-4.PDF?download=1"):
            link = soup.new_tag("a", href=href)
            link.string = "Download"
            row.append(link)
        response.text = str(soup)
        book = MyCentralNovelBook(CENTRAL_URL, 5, 1)
        assert len(book.get_chapters_link()) == 3

    def test_pdf_only_index_has_no_readable_chapters(self, mock_cloudscraper, centralnovel_toc_html):
        _, response = mock_cloudscraper
        soup = BeautifulSoup(centralnovel_toc_html, "lxml")
        for link in soup.select("div.eplister li > a"):
            link.decompose()
        response.text = str(soup)
        book = MyCentralNovelBook(CENTRAL_URL, 1, 1)
        with pytest.raises(ValueError, match="No chapters found"):
            book.get_chapters_link()

    def test_get_requested_chapters_link(self, mock_cloudscraper, centralnovel_toc_html):
        _, response = mock_cloudscraper
        response.text = centralnovel_toc_html
        book = MyCentralNovelBook(CENTRAL_URL, 3, 1)
        assert book.get_chapters_link() == [
            "https://centralnovel.com/shadow-slave-capitulo-1/",
            "https://centralnovel.com/shadow-slave-capitulo-2/",
            "https://centralnovel.com/shadow-slave-capitulo-3/",
        ]

    def test_get_chapter_content(self, mock_cloudscraper, centralnovel_chap_html):
        mock_scraper, mock_response = mock_cloudscraper
        mock_response.text = centralnovel_chap_html
        
        book = MyCentralNovelBook(CENTRAL_URL, 10, 1)
        data = book.get_chapter_content("https://centralnovel.com/shadow-slave-capitulo-1/")
        
        assert data.title == "O Pesadelo Começa"
        assert "Um jovem de aparência frágil, com pele pálida e olheiras escuras" in data.content
        assert "Afinal, sua vida estava chegando ao fim." in data.content
        assert "Traduzido usando o ChatGPT" in data.content

    @pytest.mark.parametrize("notice", [
        "Traduzido por Inteligência Artificial",
        "Traduzido usando o ChatGPT",
        "TRADUZIDO   USANDO O\nChatGPT",
    ])
    def test_preserves_translation_notice(self, mock_cloudscraper, centralnovel_chap_html, notice):
        _, response = mock_cloudscraper
        soup = BeautifulSoup(centralnovel_chap_html, "lxml")
        soup.select_one("div.epcontent p").string = notice
        response.text = str(soup)
        book = MyCentralNovelBook(CENTRAL_URL, 1, 1)
        data = book.get_chapter_content("https://centralnovel.com/shadow-slave-capitulo-1/")
        paragraphs = BeautifulSoup(data.content, "html.parser").select("p")
        assert paragraphs[0].get_text() == notice
        assert "Afinal, sua vida estava chegando ao fim." in data.content

    def test_preserves_story_when_first_paragraph_has_no_notice(self, mock_cloudscraper, centralnovel_chap_html):
        _, response = mock_cloudscraper
        soup = BeautifulSoup(centralnovel_chap_html, "lxml")
        soup.select_one("div.epcontent p").decompose()
        first_story = soup.select_one("div.epcontent p").get_text(strip=True)
        # References inside subsequent story paragraphs must not be removed.
        soup.select("div.epcontent p")[1].string = "A personagem perguntou sobre Inteligência Artificial."
        response.text = str(soup)
        book = MyCentralNovelBook(CENTRAL_URL, 1, 1)
        data = book.get_chapter_content("https://centralnovel.com/shadow-slave-capitulo-1/")
        assert first_story in data.content
        assert "A personagem perguntou sobre Inteligência Artificial." in data.content
