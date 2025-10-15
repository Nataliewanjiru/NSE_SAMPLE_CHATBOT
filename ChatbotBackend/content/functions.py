from django.utils.timezone import now
from .utils import get_drive_service,list_pdf_files,download_pdf
from .models import PDFDocument
import os
from llama_parse import LlamaParse
import asyncio
from langchain_google_genai import GoogleGenerativeAIEmbeddings

parser = LlamaParse(api_key="llx-M9JOYUoYuqBVWpBMm3zYghA6xc4ZL30FJjb0JH6otgYzyhE2")
SERVICE_ACCOUNT_PATH = "content/credentials/service_account.json"


embedding_function = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001", 
    google_api_key=os.getenv("GOOGLE_API_KEY")
)


def safe_llama_parse(parser, path):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return parser.load_data(path)
    finally:
        loop.close()

def store_pdf_metadata_bulk(file_list):
    existing_ids = set(
        PDFDocument.objects.filter(drive_file_id__in=[f['id'] for f in file_list])
        .values_list('drive_file_id', flat=True)
    )

    new_docs = [
        PDFDocument(
            name=f['name'],
            drive_file_id=f['id'],
            uploaded_at=now(),
            is_downloaded=False,  # new files are not downloaded yet
            local_path=""         # will be filled after downloading
        )
        for f in file_list if f['id'] not in existing_ids
    ]

    if new_docs:
        PDFDocument.objects.bulk_create(new_docs)
        print(f"✅ Stored {len(new_docs)} new documents.")
    else:
        print("⏩ No new files to store.")

    


def embed_and_store_chunks(pdf_obj, parsed_docs):
    from langchain.text_splitter import CharacterTextSplitter
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    from langchain_chroma import Chroma
    from langchain.schema import Document

    embedding_function = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )

    splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    
    all_chunks = []
    for parsed in parsed_docs:
        chunks = splitter.split_text(parsed.text)
        all_chunks.extend([
            Document(
                page_content=chunk,
                metadata={
                    "pdf_id": pdf_obj.id,
                    "file_name": pdf_obj.name,
                    "drive_file_id": pdf_obj.drive_file_id
                }
            ) for chunk in chunks
        ])

    vectorstore = Chroma(
        collection_name="gemini_pdf_chunks",
        embedding_function=embedding_function,
        persist_directory="./chroma_index"
    )
    vectorstore.add_documents(all_chunks)
    print(f"✅ Stored {len(all_chunks)} chunks for {pdf_obj.name}")


def run_drive_sync():
    try:
        print("📡 [drive_sync] Starting...")
        service = get_drive_service(SERVICE_ACCOUNT_PATH)
        files = list_pdf_files(service)

        # Save metadata to DB
        store_pdf_metadata_bulk(files)

        # Ensure download folder exists
        os.makedirs("./pdfs", exist_ok=True)

        # Download and process new PDFs
        new_docs = PDFDocument.objects.filter(is_downloaded=False)
        for doc in new_docs:
            local_path = f"./pdfs/{doc.drive_file_id}.pdf"
            print(f"⬇️ Downloading {doc.name}...")
            try:
                download_pdf(service, doc.drive_file_id, local_path)
                doc.local_path = local_path
                doc.is_downloaded = True
                doc.save()
            except Exception as e:
                print(f"❌ Failed to download {doc.name}: {e}")
                continue

            try:
                print(f"🧾 Parsing {doc.name}...")
                documents = safe_llama_parse(parser, local_path)
                if not documents:
                    print(f"⚠️ Empty parse result for {doc.name}, skipping.")
                    continue

                print(documents[0].text[:500])  # Preview parsed result

                # ⬇️ Embed and store the chunks
                embed_and_store_chunks(doc, documents)

            except Exception as e:
                print(f"❌ Failed to parse or embed {doc.name}: {e}")
                continue

        print("✅ [drive_sync] Done syncing.")

    except Exception as e:
        print(f"❌ Error: {e}")

