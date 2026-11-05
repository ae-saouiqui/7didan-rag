import json

from pathlib import Path
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig



# OUTPUT_DIR = Path(os.getenv("RAW_DATA_PATH"))

def load_pages(config_path:str)->list[dict[str, str]]:
    """Load and validate URLs and filenames from the JSON configuration."""

    if not config_path:
        raise ValueError("CRAWLER_URLS is not defined in .env")

    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as file:
        config = json.load(file)

    pages = config.get("pages", [])

    # Remove empty URLs and duplicates
    unique_pages = []
    seen_urls = set()

    for page in pages:
        url = page.get("url", "").strip()
        filename = page.get("file", "").strip()

        if not url or not filename:
            continue

        if url in seen_urls:
            print(f"[SKIPPED] Duplicate URL: {url}")
            continue

        if Path(filename).name != filename:
            print(f"[SKIPPED] Invalid filename: {filename}")
            continue

        seen_urls.add(url)
        unique_pages.append({
            "url": url,
            "file": filename
        })

    return unique_pages


async def crawl_web(output_dir:str,config_path:str):

    pages = load_pages(config_path)
    OUTPUT_DIR = Path(output_dir)
    if not pages:
        print("No URLs to crawl.")
        return

    urls = [page["url"] for page in pages]

    # Make a dictionnary mapping each url with its file
    url_to_file = {
        page["url"]: page["file"]
        for page in pages
    }

    crawl_config = CrawlerRunConfig(
        stream=True,
        excluded_tags=[
            "header",
            "footer"
        ]
    )

    successful = 0
    failed = 0

    async with AsyncWebCrawler() as crawler:
        # scrapping site in parallel
        # results is an async generator thus you have to use async keyword
        results = await crawler.arun_many(
            urls,
            config=crawl_config
        )

        async for result in results:
            filename = url_to_file.get(result.url)

            if not result.success:
                failed += 1
                print(f"[FAILED] {result.url}")
                print(f"Reason: {result.error_message}")
                continue

            if not filename:
                failed += 1
                print(f"[WARNING] No filename mapping for: {result.url}")
                continue

            markdown = result.markdown

            output_path = OUTPUT_DIR / filename

            try:
                output_path.write_text(
                    markdown,
                    encoding="utf-8"
                )
                successful += 1
                print(f"[SAVED] {filename}")

            except Exception as ex:
                failed += 1
                print(f"[ERROR] Saving {filename}: {ex}")


    print(f"Total URLs: {len(pages)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")