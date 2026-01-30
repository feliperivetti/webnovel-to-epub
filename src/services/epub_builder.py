import io
import time
from ebooklib import epub
from src.schemas.novel_schema import Novel
from src.utils.constants import EPUB_HTML_TEMPLATE, EPUB_STRINGS
from src.utils.logger import logger

class EpubBuilder:
    """
    Service responsible for converting a Novel object into an EPUB file.
    Follows Single Responsibility Principle (SRP).
    """

    @staticmethod
    def create_epub(novel: Novel) -> io.BytesIO:
        """
        Generates an EPUB file in-memory from the provided Novel data.
        """
        start_time = time.time()
        logger.info(f"[EpubBuilder] Starting generation for: {novel.metadata.book_title}")

        # 1. Initialize EPUB object
        book = epub.EpubBook()
        book.set_identifier(f"id_{int(time.time())}")
        book.set_title(novel.metadata.book_title)
        book.set_language('en')
        book.add_author(novel.metadata.book_author)
        book.add_metadata('DC', 'description', novel.metadata.book_description)

        # 2. Handle Cover Image
        if novel.cover_image_bytes:
            try:
                book.set_cover("cover.jpg", novel.cover_image_bytes)
            except Exception as e:
                logger.warning(f"[EpubBuilder] Failed to set cover image: {e}")

        # 3. Create Essential Pages
        desc_page = epub.EpubHtml(title=EPUB_STRINGS["synopsis_title"], file_name='synopsis.xhtml', lang='en')
        desc_page.set_content(EPUB_HTML_TEMPLATE.format(
            title=EPUB_STRINGS["synopsis_title"],
            content=f"<p>{novel.metadata.book_description.replace(chr(10), '<br/>')}</p>"
        ).encode('utf-8'))
        book.add_item(desc_page)

        disclaimer_page = epub.EpubHtml(title=EPUB_STRINGS["disclaimer_title"], file_name='disclaimer.xhtml', lang='en')
        disclaimer_page.set_content(EPUB_HTML_TEMPLATE.format(
            title=EPUB_STRINGS["disclaimer_title"],
            content=EPUB_STRINGS["disclaimer_content"]
        ).encode('utf-8'))
        book.add_item(disclaimer_page)

        # 4. Add Chapters
        epub_chapters = []
        for chapter_data in novel.chapters:
            file_name = f'chap_{chapter_data.index}.xhtml'
            chapter = epub.EpubHtml(title=chapter_data.title, file_name=file_name, lang='en')
            
            # Ensure content is string
            content_str = chapter_data.content
            
            chapter.set_content(EPUB_HTML_TEMPLATE.format(
                title=chapter_data.title,
                content=content_str
            ).encode('utf-8'))
            
            book.add_item(chapter)
            epub_chapters.append(chapter)

        # 5. Structure TOC and Spine
        book.toc = (
            (epub.Section('Essential Information'), (desc_page, disclaimer_page)),
            (epub.Section('Table of Contents'), tuple(epub_chapters)),
        )
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        book.spine = ['nav', desc_page, disclaimer_page] + epub_chapters

        # 6. Save to Buffer
        buffer = io.BytesIO()
        epub.write_epub(buffer, book, {})
        buffer.seek(0)
        
        total_time = time.time() - start_time
        logger.info(f"[EpubBuilder] DONE: generated in {total_time:.2f}s")
        
        return buffer
