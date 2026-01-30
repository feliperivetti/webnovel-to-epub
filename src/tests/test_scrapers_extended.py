import pytest
from src.classes.pandanovel_book import MyPandaNovelBook
from src.classes.novelsbr_book import MyNovelsBrBook
from src.classes.centralnovel_book import MyCentralNovelBook

class TestPandaNovelScraper:
    def test_get_book_metadata(self, mock_cloudscraper, pandanovel_toc_html):
        mock_scraper, mock_response = mock_cloudscraper
        mock_response.text = pandanovel_toc_html
        
        book = MyPandaNovelBook("https://www.pandanovel.com/details/panda-test-novel", 10, 1)
        metadata = book.get_book_metadata()
        
        assert metadata.book_title == "Panda Test Novel"
        assert metadata.book_author == "Panda Author"
        assert metadata.book_cover_link == "https://example.com/panda_cover.jpg"
        assert "Panda description" in metadata.book_description

    def test_get_chapters_link(self, mock_cloudscraper, pandanovel_toc_html):
        mock_scraper, mock_response = mock_cloudscraper
        # Panda mostly generates links proactively based on inputs, 
        # but it might check 'header-stats' or similar in some versions.
        # The current implementation in pandanovel_book.py calculates based on range ONLY 
        # (It doesn't scrape links from TOC for generation, just logs header stats if found).
        # Wait, get_chapters_link in Panda actually just ignores the HTML content usually?
        # Let's check the code: logic is purely mathematical loop.
        
        book = MyPandaNovelBook("https://www.pandanovel.com/details/panda-test-novel", 5, 1)
        links = book.get_chapters_link()
        
        assert len(links) == 5
        assert links[0] == "https://novelfire.noveljk.org/book/panda-test-novel/chapter-1"
        assert links[-1] == "https://novelfire.noveljk.org/book/panda-test-novel/chapter-5"

    def test_get_chapter_content(self, mock_cloudscraper, pandanovel_chap_html):
        mock_scraper, mock_response = mock_cloudscraper
        mock_response.text = pandanovel_chap_html
        
        book = MyPandaNovelBook("https://www.pandanovel.com/details/panda-test-novel", 10, 1)
        data = book.get_chapter_content("https://dummy.url")
        
        assert data.title == "Chapter 1: Panda Beginnings"
        assert "Panda content paragraph" in data.content


class TestNovelsBrScraper:
    def test_get_book_metadata(self, mock_cloudscraper, novelsbr_toc_html):
        mock_scraper, mock_response = mock_cloudscraper
        mock_response.text = novelsbr_toc_html
        
        book = MyNovelsBrBook("https://novels-br.com/livro/1", 10, 1)
        metadata = book.get_book_metadata()
        
        assert metadata.book_title == "NovelsBr Test Novel"
        assert metadata.book_author == "NovelsBr Author"
        assert metadata.book_cover_link == "https://example.com/novelsbr_cover.jpg"
        assert "NovelsBr description" in metadata.book_description

    def test_get_chapters_link(self, mock_cloudscraper, novelsbr_toc_html):
        mock_scraper, mock_response = mock_cloudscraper
        mock_response.text = novelsbr_toc_html
        
        # Fixture has 3 chapters. Try to ask for 5 starting from 1.
        book = MyNovelsBrBook("https://novels-br.com/livro/1", 5, 1)
        links = book.get_chapters_link()
        
        # Should return all 3 available
        assert len(links) == 3
        assert links[0] == "https://novels-br.com/livro/1/capitulo-1"
        assert links[2] == "https://novels-br.com/livro/1/capitulo-3"

    def test_get_chapter_content(self, mock_cloudscraper, novelsbr_chap_html):
        mock_scraper, mock_response = mock_cloudscraper
        mock_response.text = novelsbr_chap_html
        
        book = MyNovelsBrBook("https://novels-br.com/livro/1", 10, 1)
        data = book.get_chapter_content("https://dummy.url")
        
        assert data.title == "Capítulo 1: O Começo"
        assert "NovelsBr content paragraph" in data.content
        assert "Hidden SEO text" not in data.content
        assert "Ad junk" not in data.content


class TestCentralNovelScraper:
    def test_get_book_metadata(self, mock_cloudscraper, centralnovel_toc_html):
        mock_scraper, mock_response = mock_cloudscraper
        mock_response.text = centralnovel_toc_html
        
        book = MyCentralNovelBook("https://centralnovel.com/central-test-novel/", 10, 1)
        metadata = book.get_book_metadata()
        
        assert metadata.book_title == "Central Test Novel"
        assert metadata.book_author == "Central Author"
        assert metadata.book_cover_link == "https://example.com/central_cover.jpg"
        assert "Central description" in metadata.book_description

    def test_get_chapters_link(self, mock_cloudscraper, centralnovel_toc_html):
        mock_scraper, mock_response = mock_cloudscraper
        mock_response.text = centralnovel_toc_html
        
        # The fixture has 3 chapters.
        # Central scraper checks for total available logic.
        book = MyCentralNovelBook("https://centralnovel.com/central-test-novel/", 5, 1)
        links = book.get_chapters_link()
        
        # It should cap at 3 because total_available is 3 in the mock
        assert len(links) == 3
        # Central logic generates URLs, check format
        assert links[0] == "https://centralnovel.com/central-test-novel-capitulo-1/"
        assert links[2] == "https://centralnovel.com/central-test-novel-capitulo-3/"

    def test_get_chapter_content(self, mock_cloudscraper, centralnovel_chap_html):
        mock_scraper, mock_response = mock_cloudscraper
        mock_response.text = centralnovel_chap_html
        
        book = MyCentralNovelBook("https://centralnovel.com/central-test-novel/", 10, 1)
        data = book.get_chapter_content("https://dummy.url")
        
        assert data.title == "Chapter 1: Central Origin"
        assert "Central content paragraph" in data.content
        assert "Inteligência Artificial" not in data.content
