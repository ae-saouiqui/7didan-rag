from langchain_postgres import PGEngine, PGVectorStore
from langchain_core.embeddings import Embeddings


class PGIndexer:

    def __init__(
        self,
        postgres_auth: dict,
        vector_size: int,
        embedding: Embeddings
    ):
        self.connection_string = (
            f"postgresql+asyncpg://"
            f"{postgres_auth['POSTGRES_USER']}:"
            f"{postgres_auth['POSTGRES_PASSWORD']}@"
            f"{postgres_auth['POSTGRES_HOST']}:"
            f"{postgres_auth['POSTGRES_PORT']}/"
            f"{postgres_auth['POSTGRES_DB']}"
        )

        self.engine = PGEngine.from_connection_string(
            url=self.connection_string
        )

        table_name = postgres_auth["POSTGRES_TABLE"]

        # Create the table if not existing
        self.engine.init_vectorstore_table(
            table_name=table_name,
            vector_size=vector_size,
            overwrite_existing=False
        )

        # Initialize the vector store
        self.store = PGVectorStore.create_sync(
            engine=self.engine,
            table_name=table_name,
            embedding_service=embedding
        )

    def store_chunks(self,chunks:list[str])->list[str]:
        return self.store.add_texts(chunks)