# --- API General Configurations ---
API_CONFIG = {
    "MAX_CHAPTERS_LIMIT": 1000,
    "DEFAULT_TIMEOUT": 15,
    "MAX_WORKERS": 2,  # Recommended between 2 and 5 to avoid IP bans    
}

# --- HTML Templates for EPUB pages ---
EPUB_HTML_TEMPLATE = """<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>{title}</title></head>
<body>
    <section>
        <h1>{title}</h1>
        <div>{content}</div>
    </section>
</body>
</html>"""

# --- Content Strings ---
EPUB_STRINGS = {
    "synopsis_title": "Synopsis",
    "disclaimer_title": "About this Project",
    "disclaimer_content": """
        <p>This EPUB was generated automatically as a <strong>personal project</strong>.</p>
        <p><em>Disclaimer:</em> This book only utilizes data that is publicly available on the internet. All rights belong to the original authors and publishers.</p>
    """,
    "default_no_description": "No description available.",
    "error_content": "Content could not be downloaded."
}