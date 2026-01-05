import io
import time
import random
import requests
import concurrent.futures
from abc import ABC, abstractmethod
from ebooklib import epub

class MyBook(ABC):
    def __init__(self, main_url: str, chapters_quantity: int, start_chapter: int):
        self._main_url = main_url
        self._chapters_quantity = chapters_quantity
        self._start_chapter = start_chapter
        
        self._session = requests.Session()
        self._session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        })
        
        self.book_title = "Unknown Title"

    @abstractmethod
    def get_book_metadata(self) -> dict: pass

    @abstractmethod
    def get_chapters_link(self) -> list: pass

    @abstractmethod
    def get_chapter_content(self, url: str) -> dict: pass

    def _fetch_with_retry(self, url: str, max_retries: int = 3):
        for i in range(max_retries):
            try:
                data = self.get_chapter_content(url)
                if not data or not data.get('main_content'):
                    raise ValueError("Content not found")
                return data
            except Exception as e:
                if i < max_retries - 1:
                    time.sleep((2 ** i) * 5 + random.uniform(1, 2))
                    continue
                raise e

    def create_epub_buffer(self) -> io.BytesIO:
        # 1. Fetch and clean metadata
        metadata = self.get_book_metadata()
        
        def to_str(value):
            if value is None: return ""
            return value.get_text(strip=True) if hasattr(value, 'get_text') else str(value)

        self.book_title = to_str(metadata.get('book_title', 'Unknown'))
        book_author = to_str(metadata.get('book_author', 'Unknown Author'))
        book_description = to_str(metadata.get('book_description', 'No description available.'))
        cover_url = to_str(metadata.get('book_cover_link'))
        
        chapter_urls = self.get_chapters_link()
        
        book = epub.EpubBook()
        book.set_identifier(f"id_{int(time.time())}")
        book.set_title(self.book_title)
        book.set_language('en')
        book.add_author(book_author)
        book.add_metadata('DC', 'description', book_description)

        # 2. Cover logic
        if cover_url and cover_url.startswith('http'):
            try:
                cover_res = self._session.get(cover_url, timeout=10)
                cover_res.raise_for_status()
                book.set_cover("cover.jpg", cover_res.content)
            except Exception as e:
                print(f"⚠️ Cover failed: {e}")

        # 3. Essential Info Pages
        # 3.1 Description Page
        desc_page = epub.EpubHtml(title='Synopsis', file_name='synopsis.xhtml', lang='en')
        desc_page.set_content(f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Synopsis</title></head>
<body>
    <section>
        <h1>Synopsis</h1>
        <p>{book_description}</p>
    </section>
</body>
</html>""".encode('utf-8'))
        book.add_item(desc_page)

        # 3.2 Disclaimer Page
        disclaimer_page = epub.EpubHtml(title='About this Project', file_name='disclaimer.xhtml', lang='en')
        disclaimer_page.set_content(f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>About this Project</title></head>
<body>
    <section>
        <h1>About this Project</h1>
        <p>This EPUB was generated as a <strong>personal project</strong> for educational and archival purposes.</p>
        <p><em>Disclaimer:</em> This book only utilizes data that is publicly available on the internet. All rights belong to the original authors and publishers.</p>
    </section>
</body>
</html>""".encode('utf-8'))
        book.add_item(disclaimer_page)

        # 4. Parallel Chapter Download
        chapters_data_results = [None] * len(chapter_urls)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_to_index = {
                executor.submit(self._fetch_with_retry, url): i 
                for i, url in enumerate(chapter_urls)
            }
            for future in concurrent.futures.as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    chapters_data_results[index] = future.result()
                    print(f"✅ [{index + 1}/{len(chapter_urls)}] Downloaded.")
                except Exception as e:
                    chapters_data_results[index] = {'chapter_title': f'Error {index+1}', 'main_content': 'N/A'}

        # 5. Assemble Chapters
        epub_chapters = []
        for i, data in enumerate(chapters_data_results):
            if not data: continue
            title = to_str(data.get('chapter_title', f'Chapter {i + 1}'))
            content_node = data.get('main_content')
            raw_html = content_node.decode_contents() if hasattr(content_node, 'decode_contents') else str(content_node)

            chapter = epub.EpubHtml(title=title, file_name=f'chap_{i + 1}.xhtml', lang='en')
            xhtml_body = f"""<!DOCTYPE html>
                            <html xmlns="http://www.w3.org/1999/xhtml">
                            <head><title>{title}</title></head>
                            <body>
                                <section>
                                    <h1>{title}</h1>
                                    <div>{raw_html}</div>
                                </section>
                            </body>
                            </html>"""
            
            chapter.set_content(xhtml_body.encode('utf-8'))
            book.add_item(chapter)
            epub_chapters.append(chapter)

        # 6. Finalize Multi-level Structure
        if not epub_chapters:
            raise ValueError("No chapters found")

        # Nested TOC structure
        book.toc = (
            (epub.Section('Essential Information'), (desc_page, disclaimer_page)),
            (epub.Section('Table of Contents'), tuple(epub_chapters)),
        )

        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        
        # Reading order
        book.spine = ['nav', desc_page, disclaimer_page] + epub_chapters

        buffer = io.BytesIO()
        epub.write_epub(buffer, book, {})
        buffer.seek(0)
        return buffer