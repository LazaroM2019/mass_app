from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app
from app.main import AiSuggestion  # Adjust imports based on your app structure

client = TestClient(app)

# Mock output of the `generate` method
mock_output = {
    "output": {
        "message": "Test message response",
        "suggestions": ["Suggestion 1", "Suggestion 2"]
    },
    "refusal": False,
    "usage": {"tokens": 10}
}

@patch("app.main.ChatGpt.generate")
def test_chat_suggestion(mock_generate):
    # Configure the mock to return the desired output
    mock_generate.return_value = mock_output

    # Define the payload to send to the endpoint
    payload = {
        "title": "Test Title",
        "message": "Test message body"
    }

    # Make the POST request to the endpoint
    response = client.post("/ai/suggestion", json=payload)

    # Ensure the mocked method was called as expected
    mock_generate.assert_called_once()

    # Assertions
    assert response.status_code == 200
    assert response.json() == mock_output
