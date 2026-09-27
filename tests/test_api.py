import pytest
from fastapi.testclient import TestClient
from app.main import app
from scripts.generate_samples import create_synthetic_wav
from app.config import SAMPLES_DIR

client = TestClient(app)

def test_api_jobs_list():
    response = client.get("/api/jobs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_api_upload_and_pipeline_flow():
    # Create sample file to upload
    create_synthetic_wav("api_test.wav", duration_sec=3.0)
    sample_file = SAMPLES_DIR / "api_test.wav"

    with open(sample_file, "rb") as f:
        upload_resp = client.post("/api/upload", files={"file": ("api_test.wav", f, "audio/wav")})

    assert upload_resp.status_code == 200
    data = upload_resp.json()
    assert "job_id" in data
    job_id = data["job_id"]

    # Poll status until completed or timeout
    import time
    completed = False
    for _ in range(10):
        status_resp = client.get(f"/api/jobs/{job_id}")
        assert status_resp.status_code == 200
        st_data = status_resp.json()
        if st_data["status"] == "COMPLETED":
            completed = True
            break
        time.sleep(1)

    assert completed is True

    # Test result endpoint
    result_resp = client.get(f"/api/jobs/{job_id}/result")
    assert result_resp.status_code == 200
    res_data = result_resp.json()
    assert "summary" in res_data
    assert "statistics" in res_data
    assert "transcript" in res_data

    # Test export endpoints
    pdf_resp = client.get(f"/api/jobs/{job_id}/export/pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"

    docx_resp = client.get(f"/api/jobs/{job_id}/export/docx")
    assert docx_resp.status_code == 200

    json_resp = client.get(f"/api/jobs/{job_id}/export/json")
    assert json_resp.status_code == 200
