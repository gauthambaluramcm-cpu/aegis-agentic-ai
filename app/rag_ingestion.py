from pathlib import Path
import re
import shutil

from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

POLICY_DIR = BASE_DIR / "data" / "knowledge_base" / "policies"
REGULATION_DIR = BASE_DIR / "data" / "knowledge_base" / "regulations"
CHROMA_DIR = BASE_DIR / "data" / "chroma_db"


# =========================================================
# TEXT SPLITTERS
# =========================================================

policy_splitter = RecursiveCharacterTextSplitter(
    chunk_size=900,
    chunk_overlap=120,
    separators=[
        "\n\n",
        "\n",
        ". ",
        " ",
        ""
    ]
)

regulation_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1800,
    chunk_overlap=200,
    separators=[
        "\n\n",
        "\n",
        ". ",
        " ",
        ""
    ]
)


# =========================================================
# LOAD INTERNAL POLICIES
# =========================================================

def load_policy_documents():

    documents = []

    print("\n--- INTERNAL POLICIES ---")

    for file_path in sorted(POLICY_DIR.glob("*.txt")):

        print(f"\nProcessing: {file_path.name}")

        # -------------------------------------------------
        # Read policy file directly
        # -------------------------------------------------

        text = None

        encodings_to_try = [
            "utf-8",
            "utf-8-sig",
            "cp1252",
            "latin-1"
        ]

        for encoding in encodings_to_try:

            try:

                text = file_path.read_text(
                    encoding=encoding
                )

                if text.strip():
                    break

            except UnicodeDecodeError:
                continue

        # -------------------------------------------------
        # Check file content
        # -------------------------------------------------

        if text is None or not text.strip():

            print(
                f"WARNING: {file_path.name} contains no readable text."
            )

            continue

        text = text.strip()

        # -------------------------------------------------
        # Split policy into chunks
        # -------------------------------------------------

        chunks = policy_splitter.split_text(text)

        valid_chunks = 0

        for index, chunk_text in enumerate(
            chunks,
            start=1
        ):

            chunk_text = chunk_text.strip()

            if not chunk_text:
                continue

            chunk = Document(
                page_content=chunk_text,
                metadata={
                    "source_file": file_path.name,
                    "document_type": "internal_policy",
                    "section_number": None,
                    "section_title": file_path.stem.replace(
                        "_",
                        " "
                    ).title(),
                    "start_page": None,
                    "chunk_id": index
                }
            )

            documents.append(chunk)

            valid_chunks += 1

        print(
            f"Created {valid_chunks} chunks "
            f"from {file_path.name}"
        )

    return documents


# =========================================================
# CLEAN PDF TEXT
# =========================================================

def clean_pdf_text(text):

    lines = []

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        # Remove common Gazette headers
        upper_line = line.upper()

        if "THE GAZETTE OF INDIA" in upper_line:
            continue

        # Remove standalone page numbers
        if re.fullmatch(r"\d+", line):
            continue

        lines.append(line)

    return "\n".join(lines)


# =========================================================
# DETECT ACT SECTION HEADINGS
# =========================================================

def detect_act_section(line):

    """
    Detects actual numbered sections in the DPDP Act.

    Examples:

    1. Short title and commencement.
    2. Definitions.
    3. Application of Act.

    We deliberately avoid lines such as:

    2. Definitions...
    inside subsection content when they are clearly
    part of another provision.
    """

    pattern = r"^(\d{1,2})\.\s+(.+)$"

    match = re.match(pattern, line)

    if not match:
        return None

    number = match.group(1)
    title = match.group(2).strip()

    # Section headings normally have a reasonably
    # descriptive title.
    if len(title) < 5:
        return None

    # Ignore subsection-like content
    if title.startswith("("):
        return None

    return number, title


# =========================================================
# DETECT DPDP RULE HEADINGS
# =========================================================

def detect_rule_heading(line):

    """
    Detects Rules such as:

    1. Short title and commencement.
    2. Definitions.
    3. Notice given by Data Fiduciary.
    """

    pattern = r"^(\d{1,2})\.\s+(.+)$"

    match = re.match(pattern, line)

    if not match:
        return None

    number = match.group(1)
    title = match.group(2).strip()

    if len(title) < 5:
        return None

    # Avoid subsection content
    if title.startswith("("):
        return None

    # Avoid obvious sentence fragments
    if len(title) > 180:
        return None

    return number, title


# =========================================================
# EXTRACT STRUCTURED SECTIONS FROM PDF
# =========================================================

def extract_structured_sections(pdf_path, document_type):

    loader = PyPDFLoader(str(pdf_path))

    pages = loader.load()

    sections = []

    current_number = None
    current_title = None
    current_text = []
    current_start_page = None

    for page_index, page in enumerate(pages):

        page_number = page_index + 1

        text = clean_pdf_text(page.page_content)

        if not text:
            continue

        lines = text.splitlines()

        for line in lines:

            if document_type == "act":
                section_info = detect_act_section(line)

            else:
                section_info = detect_rule_heading(line)

            # ---------------------------------------------
            # New section/rule detected
            # ---------------------------------------------

            if section_info:

                # Save previous section
                if current_text:

                    section_text = "\n".join(current_text).strip()

                    if section_text:

                        sections.append(
                            Document(
                                page_content=section_text,
                                metadata={
                                    "source_file": pdf_path.name,
                                    "document_type": "regulation",
                                    "regulation_type": document_type,
                                    "section_number": current_number,
                                    "section_title": current_title,
                                    "start_page": current_start_page
                                }
                            )
                        )

                # Start new section
                current_number = section_info[0]
                current_title = section_info[1]

                current_start_page = page_number

                current_text = [line]

            else:

                if current_text:
                    current_text.append(line)

                else:
                    # Content before the first detected section
                    current_text.append(line)

                    if current_start_page is None:
                        current_start_page = page_number

    # -----------------------------------------------------
    # SAVE FINAL SECTION
    # -----------------------------------------------------

    if current_text:

        section_text = "\n".join(current_text).strip()

        if section_text:

            sections.append(
                Document(
                    page_content=section_text,
                    metadata={
                        "source_file": pdf_path.name,
                        "document_type": "regulation",
                        "regulation_type": document_type,
                        "section_number": current_number,
                        "section_title": current_title,
                        "start_page": current_start_page
                    }
                )
            )

    return sections


# =========================================================
# LOAD REGULATIONS
# =========================================================

def load_regulation_documents():

    documents = []

    print("\n--- REGULATIONS ---")

    for pdf_path in sorted(REGULATION_DIR.glob("*.pdf")):

        print(f"\nProcessing: {pdf_path.name}")

        # Determine whether this is Act or Rules
        if "Act" in pdf_path.name:
            document_type = "act"

        elif "Rules" in pdf_path.name:
            document_type = "rules"

        else:
            document_type = "regulation"

        sections = extract_structured_sections(
            pdf_path,
            document_type
        )

        print(
            f"Detected {len(sections)} "
            f"structured provisions"
        )

        pdf_chunk_count = 0

        # -------------------------------------------------
        # Split large legal provisions
        # -------------------------------------------------

        for section in sections:

            section_number = section.metadata.get(
                "section_number"
            )

            section_title = section.metadata.get(
                "section_title"
            )

            regulation_type = section.metadata.get(
                "regulation_type"
            )

            start_page = section.metadata.get(
                "start_page"
            )

            # Create human-readable heading
            if regulation_type == "rules":

                heading = (
                    f"DPDP Rule {section_number}: "
                    f"{section_title}"
                )

            else:

                heading = (
                    f"DPDP Act Section {section_number}: "
                    f"{section_title}"
                )

            # Split only if the provision is large
            split_chunks = regulation_splitter.split_text(
                section.page_content
            )

            for chunk_index, chunk_text in enumerate(
                split_chunks,
                start=1
            ):

                chunk_text = chunk_text.strip()

                if not chunk_text:
                    continue

                # Add heading to every chunk
                final_text = (
                    f"{heading}\n\n"
                    f"{chunk_text}"
                )

                chunk = Document(
                    page_content=final_text,
                    metadata={
                        "source_file": pdf_path.name,
                        "document_type": "regulation",
                        "regulation_type": regulation_type,
                        "section_number": section_number,
                        "section_title": section_title,
                        "start_page": start_page,
                        "chunk_id": chunk_index
                    }
                )

                documents.append(chunk)

                pdf_chunk_count += 1

        print(
            f"Created {pdf_chunk_count} chunks "
            f"from {pdf_path.name}"
        )

    return documents


# =========================================================
# DISPLAY SAMPLE CHUNKS
# =========================================================

def display_sample_chunks(documents):

    print("\n--- SAMPLE CHUNKS ---")

    for index, doc in enumerate(documents[:5], start=1):

        print(f"\nChunk {index}")

        print(
            f"Source: "
            f"{doc.metadata.get('source_file')}"
        )

        print(
            f"Type: "
            f"{doc.metadata.get('document_type')}"
        )

        print(
            f"Section: "
            f"{doc.metadata.get('section_number')}"
        )

        print(
            f"Title: "
            f"{doc.metadata.get('section_title')}"
        )

        print(
            f"Page: "
            f"{doc.metadata.get('start_page')}"
        )

        preview = doc.page_content[:300]

        print(
            f"Preview:\n{preview}..."
        )


# =========================================================
# MAIN
# =========================================================

def main():

    print("\n")
    print("=" * 60)
    print("AEGIS RAG INGESTION")
    print("=" * 60)

    # -----------------------------------------------------
    # Load policies
    # -----------------------------------------------------

    policy_documents = load_policy_documents()

    # -----------------------------------------------------
    # Load regulations
    # -----------------------------------------------------

    regulation_documents = load_regulation_documents()

    # -----------------------------------------------------
    # Combine
    # -----------------------------------------------------

    all_documents = (
        policy_documents +
        regulation_documents
    )

    print("\n" + "=" * 60)

    print(
        f"Policy chunks      : "
        f"{len(policy_documents)}"
    )

    print(
        f"Regulation chunks  : "
        f"{len(regulation_documents)}"
    )

    print(
        f"TOTAL chunks       : "
        f"{len(all_documents)}"
    )

    # -----------------------------------------------------
    # Safety check
    # -----------------------------------------------------

    if len(policy_documents) == 0:

        raise RuntimeError(
            "No policy chunks were created. "
            "Check the files inside data/knowledge_base/policies."
        )

    if len(regulation_documents) == 0:

        raise RuntimeError(
            "No regulation chunks were created. "
            "Check the files inside data/knowledge_base/regulations."
        )

    # -----------------------------------------------------
    # Display samples
    # -----------------------------------------------------

    display_sample_chunks(all_documents)

    # -----------------------------------------------------
    # Delete old Chroma database
    # -----------------------------------------------------

    if CHROMA_DIR.exists():

        print("\nDeleting old Chroma database...")

        shutil.rmtree(CHROMA_DIR)

    # -----------------------------------------------------
    # Load embedding model
    # -----------------------------------------------------

    print("\nLoading embedding model...")

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={
            "device": "cpu"
        },
        encode_kwargs={
            "normalize_embeddings": True
        }
    )

    # -----------------------------------------------------
    # Create Chroma database
    # -----------------------------------------------------

    print("\nCreating Chroma vector database...")

    Chroma.from_documents(
        documents=all_documents,
        embedding=embeddings,
        collection_name="aegis_knowledge_base",
        persist_directory=str(CHROMA_DIR)
    )

    # -----------------------------------------------------
    # Completed
    # -----------------------------------------------------

    print("\n" + "=" * 60)
    print("RAG INGESTION COMPLETED SUCCESSFULLY")
    print("=" * 60)

    print(
        f"\nVector database:\n"
        f"{CHROMA_DIR}"
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()