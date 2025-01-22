import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Sample input and expected output for the endpoint
sample_request = {
    "title": "Sample Title",
    "message": "This is a test message."
}

mock_prompt_template = {
    "prompt": "The title is: __TEXT_TITLE__ and the message is: __TEXT_MESSAGE__.",
    "system_instruction": "Provide suggestions based on the input."
}

mock_output = {
    "suggestions": [
        "Consider rephrasing your title for better impact.",
        "Your message could use additional details for clarity."
    ]
}

# Mocking load_prompt_template and ChatGpt
@patch("app.routers.ai_suggestion.load_prompt_template")
@patch("app.routers.ai_suggestion.ChatGpt")
def test_chat_suggestion(mock_chat_gpt, mock_load_prompt_template):
    # Set up the mock for load_prompt_template
    mock_load_prompt_template.return_value = mock_prompt_template

    # Set up the mock for ChatGpt
    mock_chat_instance = MagicMock()
    mock_chat_instance.generate.return_value = mock_output
    mock_chat_gpt.return_value = mock_chat_instance

    # Perform the POST request
    response = client.post("/ai/suggestion", json=sample_request)

    # Assertions
    assert response.status_code == 200
    assert response.json() == mock_output

    # Verify mocks were called with the correct arguments
    mock_load_prompt_template.assert_called_once_with("message_suggestion")
    mock_chat_gpt.assert_called_once_with(
        "GPT-4O-mini",  # Assuming MODELS['GPT_4O_mini'] resolves to this
        mock_prompt_template["system_instruction"]
    )
    mock_chat_instance.generate.assert_called_once_with(
        prompt="The title is: Sample Title and the message is: This is a test message.",
        respose_format="AiSuggestion"  # Assuming this is the expected format
    )