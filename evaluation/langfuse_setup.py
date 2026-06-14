# evaluation/langfuse_setup.py
import os
from dotenv import load_dotenv

# Load .env dari root project
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

def get_lf_client():
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    host       = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    if not public_key or not secret_key:
        raise ValueError(f"Keys not found! public={public_key}, secret={secret_key}")

    from langfuse import Langfuse
    client = Langfuse(
        public_key=public_key,
        secret_key=secret_key,
        host=host,
    )
    return client


def verify_connection():
    try:
        client = get_lf_client()
        client.auth_check()
        print("✅ Langfuse connected!")
        return True
    except Exception as e:
        print(f"❌ {e}")
        return False


if __name__ == "__main__":
    verify_connection()