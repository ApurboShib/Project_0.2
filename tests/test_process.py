import os
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_process_document():
    """Test the document processing endpoint with a real file."""
    sample_file_path = "samples/sample_notice.txt"
    
    # Create sample file if it doesn't exist
    if not os.path.exists(sample_file_path):
        os.makedirs("samples", exist_ok=True)
        with open(sample_file_path, "w") as f:
            f.write("This is a test notice. The deadline is 2026-05-20.")

    with open(sample_file_path, "rb") as f:
        files = {"file": (os.path.basename(sample_file_path), f, "text/plain")}
        data = {
            "draft_type": "notice_summary",
            "custom_instructions": "Test instructions"
        }
        response = client.post("/process", data=data, files=files)
        
    # If it's a 500, this will show the error details if we print the response
    if response.status_code == 500:
        print(f"\nERROR 500: {response.text}")
    
    assert response.status_code == 200
    assert "Generated Document" in response.text
