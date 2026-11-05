
import re

from langchain_text_splitters import RecursiveCharacterTextSplitter


class MarkdownChunker:

    def __init__(self, chunk_size: int, chunk_overlap: int):

        self.size_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

    def chunk(self, texts: list[str]) -> list[str]:

        chunk_list = []

        for text in texts:

            # Track the current Markdown hierarchy.
            h1 = ""
            h2 = ""
            current_group = None

            grouped_sections = {}

            for line in text.splitlines():

                line = line.strip()

                # Update H1 context.
                if re.match(r"^# ", line):
                    h1 = line[2:].strip()
                    h2 = ""
                    current_group = None
                    continue

                # Update H2 context and create a new group.
                if re.match(r"^## ", line):
                    h2 = line[3:].strip()

                    group_key = (h1, h2)

                    if group_key not in grouped_sections:
                        grouped_sections[group_key] = {
                            "context": f"# {h1}\n## {h2}",
                            "content": []
                        }

                    current_group = grouped_sections[group_key]
                    continue

                # Preserve H3 headings, even when they have no description.
                if re.match(r"^### ", line):
                    if current_group is not None:
                        current_group["content"].append(line)
                    continue

                # Keep content before the first H2 under the H1 section.
                if line and current_group is None and h1:
                    group_key = (h1, "")
                    if group_key not in grouped_sections:
                        grouped_sections[group_key] = {
                              "context": f"# {h1}",
                              "content": []
                            }
                    
                    current_group = grouped_sections[group_key]

                # Add normal content to the current group.
                if line and current_group is not None:
                    current_group["content"].append(line)

            # Split each group into appropriately sized chunks.
            for group in grouped_sections.values():

                content = "\n".join(group["content"]).strip()

                if not content:
                    continue

                chunks = self.size_splitter.split_text(content)

                for chunk in chunks:

                    contextual_chunk = (
                        f'{group["context"]}\n\n{chunk}'
                    )

                    chunk_list.append(contextual_chunk.strip())

        return chunk_list
