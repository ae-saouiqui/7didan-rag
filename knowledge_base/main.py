from dotenv import load_dotenv
import os
import asyncio
from src.ingestions.ingest import ingest
from src.preprocessing.structured_cleaning import Cleaner
from src.chunkers.markdown_chunker import MarkdownChunker
from src.embedders.qwen_embedder import QwenEmbedder
from src.indexers.pg_indexer import PGIndexer
from argparse import ArgumentParser
import json



load_dotenv()


arg_parser = ArgumentParser()

arg_parser.add_argument("-c","--crawl",action="store_true")
arg_parser.add_argument("-p","--parse",action="store_true")

async def main():

    args = arg_parser.parse_args()
    crawl_config = {
            "config_path" : os.getenv("CRAWLER_URLS"),
            "output_dir" : os.getenv("RAW_DATA_PATH")
            } if args.crawl else None
    if args.parse:
        with open(os.getenv("PARSER_CONFIG"), "r") as f :
            parser_config = json.load(f)
        parser_config.update({"source_dir":os.getenv("PDF_DATA_PATH")})
        parser_config.update({"output_dir":os.getenv("RAW_DATA_PATH")})
    else :
        parser_config = None


    await ingest(
        args.crawl,
        args.parse,
        crawl_config,
        parser_config
        )

    cleaner = Cleaner(int(os.getenv("NUM_WORKER")))
    cleaned_text = cleaner.clean_documents(os.getenv("RAW_DATA_PATH"))
    chunker = MarkdownChunker(
        int(os.getenv("CHUNK_SIZE")),
        int(os.getenv("CHUNK_OVERLAP"))
        )
    chunks = chunker.chunk(cleaned_text)
    with open(os.getenv("MODEL_CONFIG"),"r") as f:
        model_config = json.load(f)
    embedding = QwenEmbedder(
        os.getenv("MODEL_NAME"),
        model_config["encode_kwargs"],
        {},
        None
    )

    postgres_auth = {
        "POSTGRES_USER" : os.getenv("POSTGRES_USER"),
        "POSTGRES_PASSWORD" : os.getenv("POSTGRES_PASSWORD"),
        "POSTGRES_HOST" : os.getenv("POSTGRES_HOST"),
        "POSTGRES_PORT" : os.getenv("POSTGRES_PORT"),
        "POSTGRES_DB" : os.getenv("POSTGRES_DB"),
        "POSTGRES_TABLE" : os.getenv("POSTGRES_TABLE")
    }
    
    indexer = PGIndexer(
        postgres_auth,
        int(os.getenv("VECTOR_SIZE")),
        embedding
    )
    indexer.store_chunks(chunks)



if __name__ == "__main__":
    asyncio.run(main())


