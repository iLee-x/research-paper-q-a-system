#!/usr/bin/env python3
"""Quick test script to verify the Q&A system is working."""

import requests
import time
import sys

BASE_URL = "http://localhost:8000"


def test_health():
    """Test health check endpoint."""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        print("✓ Health check passed")
        return True
    else:
        print("✗ Health check failed")
        return False


def test_status():
    """Test status endpoint."""
    print("\nChecking system status...")
    response = requests.get(f"{BASE_URL}/status")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Status check passed")
        print(f"  - Documents indexed: {data['documents_indexed']}")
        print(f"  - Embedding model: {data['embedding_model']}")
        print(f"  - LLM model: {data['llm_model']}")
        return data['documents_indexed'] > 0
    else:
        print("✗ Status check failed")
        return False


def test_index():
    """Test indexing the paper."""
    print("\nIndexing the paper (this may take 30-60 seconds)...")
    try:
        response = requests.post(f"{BASE_URL}/index", timeout=120)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Indexing successful")
            print(f"  - Chunks created: {data['chunks_created']}")
            print(f"  - Documents indexed: {data['documents_indexed']}")
            return True
        else:
            print(f"✗ Indexing failed: {response.text}")
            return False
    except requests.exceptions.Timeout:
        print("✗ Indexing timed out")
        return False


def test_question(question: str):
    """Test asking a question."""
    print(f"\nAsking question: '{question}'")
    try:
        response = requests.post(
            f"{BASE_URL}/ask",
            json={"question": question},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Question answered successfully")
            print(f"  - Answer length: {len(data['answer'])} characters")
            print(f"  - Context chunks used: {data['context_chunks_used']}")
            print(f"  - Input tokens: {data['usage']['input_tokens']}")
            print(f"  - Output tokens: {data['usage']['output_tokens']}")
            print(f"\n  Answer preview:")
            print(f"  {data['answer'][:200]}...")
            return True
        else:
            print(f"✗ Question failed: {response.text}")
            return False
    except requests.exceptions.Timeout:
        print("✗ Question timed out")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Q&A System Test Suite")
    print("=" * 60)

    # Test health
    if not test_health():
        print("\n❌ System is not healthy. Make sure the server is running.")
        sys.exit(1)

    # Test status and check if indexed
    has_documents = test_status()

    # Index if needed
    if not has_documents:
        print("\n⚠️  Vector store is empty. Indexing paper...")
        if not test_index():
            print("\n❌ Failed to index paper.")
            sys.exit(1)
    else:
        print("\n✓ Vector store already has documents, skipping indexing")

    # Test questions
    test_questions = [
        "What is the Transformer architecture?",
        "How does multi-head attention work?",
        "What is the role of positional encoding?"
    ]

    print("\n" + "=" * 60)
    print("Testing Q&A Functionality")
    print("=" * 60)

    success_count = 0
    for question in test_questions:
        if test_question(question):
            success_count += 1
        time.sleep(1)  # Brief pause between questions

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Questions asked: {len(test_questions)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {len(test_questions) - success_count}")

    if success_count == len(test_questions):
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed.")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to server. Make sure it's running on port 8000.")
        sys.exit(1)
