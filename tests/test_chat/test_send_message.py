import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone
from app.main import app

client = TestClient(app)

# Mock functions (assuming you want to avoid real external interactions)
@pytest.fixture
def mock_schedule_whatsapp_message(mocker):
    return mocker.patch("app.services.whatsapp.schedule_whatsapp_message")

# Test cases
def test_send_message_scheduled(mock_schedule_whatsapp_message):
    """
    Test scheduling a message for a future time.
    """
    future_time = "2030-12-15T12:00:00.000000Z"#(datetime.now(timezone.utc) + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    
    request_data = {
        "title": "Test Title",
        "message": "This is a test message.",
        "numbers": ["1234567890", "0987654321"],
        "image": "",
        "userId": "677ec7c63a019368ed48a8fb",
        "date": future_time,
        "messageId": "677edd278bc7fdfba4afbc8e",
        "doc": ""
    }

    response = client.post("/chat/send", json=request_data)
    
    assert response.status_code == 200
    assert response.json()["status"] == "scheduled"
    assert "Message scheduled for" in response.json()["message"]


def test_send_message_immediate(mock_schedule_whatsapp_message):
    """
    Test sending a message immediately.
    """
    past_time = "2024-12-15T12:00:00.000000Z"#(datetime.now(timezone.utc) - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    
    request_data = {
        "title": "Test Title",
        "message": "This is a test message.",
        "numbers": ["1234567890", "0987654321"],
        "image": "",
        "userId": "677ec7c63a019368ed48a8fb",
        "date": past_time,
        "messageId": "677edd278bc7fdfba4afbc8e",
        "doc": ""
    }

    response = client.post("/chat/send", json=request_data)

    assert response.status_code == 200
    assert response.json()["status"] == "sent"
    assert "Message sent" in response.json()["message"]


def test_invalid_date_format():
    """
    Test invalid date format in the request.
    """
    request_data = {
        "title": "Test Title",
        "message": "This is a test message.",
        "numbers": ["1234567890", "0987654321"],
        "image": "",
        "userId": "677ec7c63a019368ed48a8fb",
        "date": "invalid_date_format",
        "messageId": "677edd278bc7fdfba4afbc8e",
        "doc": ""
    }

    response = client.post("/chat/send", json=request_data)

    assert response.status_code == 200
    assert "Invalid date format" in response.json()["error"]


