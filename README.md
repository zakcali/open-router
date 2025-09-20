# OpenRouter Gradio Text-to-Text Chatbot

A lightweight Gradio app to chat with multiple (free) models on [OpenRouter](https://openrouter.ai/) using the OpenAI Python SDK. It supports streaming responses, optional reasoning traces (when available), message downloads, and automatic cleanup of temporary files.

- File: `openrouter-gradio-text2text.py`
- Repo: [zakcali/open-router](https://github.com/zakcali/open-router)

## Features

- Simple, fast chat UI built with Gradio
- Streaming token-by-token responses
- System instructions (system prompt) per session
- Model picker with several free models on OpenRouter
- Reasoning controls:
  - For OpenAI models (gpt-oss/gpt-5): uses `reasoning: { effort: low|medium|high }`
  - For Grok-4-fast: enables reasoning when effort is medium or high
  - Other models ignore this setting gracefully
- Adjustable temperature and max tokens
- Download the last assistant response as a Markdown file
- Temporary files are automatically cleaned up on exit

## Demo (How it works)

The app maintains a conversation history and streams new tokens to the chat as they arrive. If a model supports a separate "reasoning" stream, it will appear in the "Model Thoughts" panel. The "Download Last Response" button lets you save the most recent assistant message to a temporary `.md` file; these files are tracked and cleaned up automatically when the app exits.

## Requirements

- Python 3.9+
- Packages:
  - `gradio`
  - `openai` (the new 1.x SDK that exposes `from openai import OpenAI`)

Install:

```bash
pip install -U gradio openai
```

## Setup

1. Get an OpenRouter API key: https://openrouter.ai/
2. Set the environment variable:

   - macOS/Linux:
     ```bash
     export OPENROUTER_API_KEY="your-api-key"
     ```
   - Windows (PowerShell):
     ```powershell
     setx OPENROUTER_API_KEY "your-api-key"
     ```

No other keys are needed. The script configures the OpenAI SDK to point to OpenRouter:

```python
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)
```

## Run

From the repository root:

```bash
python openrouter-gradio-text2text.py
```

Then open the local URL Gradio prints (e.g., http://127.0.0.1:7860). Press Ctrl+C to stop. All tracked temporary download files are deleted on exit.

## Using the App

- Chat area:
  - Enter a message and click Send (or press Enter).
  - Streaming tokens update the assistant message live.
  - Stop cancels in-flight requests.
  - Clear Chat resets the conversation and hides the download button.

- Right panel controls:
  - Model dropdown: choose any free model listed (default: `x-ai/grok-4-fast:free`).
  - System Instructions: set the assistant’s general behavior.
  - Reasoning Control:
    - OpenAI models (`openai/gpt-oss-*`, `openai/gpt-5-*`): sets `reasoning.effort` to `low|medium|high`.
    - Grok-4-fast: when `medium` or `high`, enables `reasoning.enabled=true`.
    - Other models ignore this control, and you may see “This model does not expose reasoning traces.”
  - Temperature: 0.0–2.0
  - Max Tokens: 100–65535 (upper bound depends on model/support)

- Download Last Response:
  - Becomes visible after an assistant reply completes.
  - Saves a `.md` file to your OS temp directory and provides a direct download.
  - Files are tracked and removed automatically on app exit.

## Models

The dropdown lists several free models, for example:

- OpenAI OSS:
  - `openai/gpt-oss-20b:free`
  - `openai/gpt-oss-120b:free`
- Grok:
  - `x-ai/grok-4-fast:free`
- Meta Llama, Qwen, DeepSeek, Google Gemma, Zhipu GLM, Moonshot, etc.

Notes:
- This is a text-to-text app. If you select a vision-capable model, it will be used in text mode.
- Not all models provide reasoning streams; when absent, the “Model Thoughts” panel will indicate that no trace is available.

## How Streaming and Reasoning Work

The core function `chat_with_openai`:
- Builds the message list from your chat history and optional system instructions.
- Prepares request parameters per selected model:
  - Always streams: `stream=True`.
  - For OpenAI models (gpt-oss/gpt-5), sets:
    ```python
    extra_body = { "reasoning": { "effort": effort } }
    ```
  - For Grok-4-fast, when effort is `medium` or `high`:
    ```python
    extra_body = { "reasoning": { "enabled": True } }
    ```
- Iterates over streaming chunks:
  - Appends `delta.content` to the chat.
  - Appends `delta.reasoning` to the “Model Thoughts” panel when present.
- Flushes UI updates roughly every 40 ms for smooth streaming.
- After completion, writes the assistant’s final text to a temporary `.md` file and reveals the download button.

Temporary files are tracked in a global list and removed by an `atexit` handler when the app shuts down.

## Common Issues and Troubleshooting

- Missing API key:
  - Symptom: HTTP 401/403 or “You must provide an API key.”
  - Fix: Ensure `OPENROUTER_API_KEY` is set in your environment and your shell session is refreshed.

- Rate limits or model unavailability:
  - Symptom: Server error or stalls.
  - Fix: Try a different listed free model or reduce request frequency.

- Large `max_tokens`:
  - Symptom: Errors if the selected model doesn’t support the requested context/length.
  - Fix: Lower `max_tokens` or temperature; consider shorter prompts.

- No reasoning content:
  - Many models don’t emit a separate reasoning stream. This is expected behavior.

## Extending the Script

- Add a new model to the dropdown.
- Map new reasoning semantics:
  ```python
  elif "provider/model-name" in model_choice:
      request_params["extra_body"] = {
          "reasoning": { "some_param": "value" }
      }
  ```
- Tweak the streaming flush interval by adjusting `flush_interval_s`.
- Make the app public by launching with `demo.launch(share=True)`.

## Security

- API keys are read from environment variables; the app does not log them.
- Responses are written to temporary files only for download convenience and are deleted automatically when the app exits.

## License

Choose and add a license (e.g., MIT) at the repo root if you plan to distribute or accept contributions.

## Acknowledgments

- [OpenRouter](https://openrouter.ai/) for unified access to many models
- [OpenAI Python SDK](https://github.com/openai/openai-python) for the client abstraction
- [Gradio](https://github.com/gradio-app/gradio) for the UI framework

# 👁️ Grok Image & Text Analyzer (via OpenRouter)

A simple Gradio web app that lets you:
- Ask questions with plain text (chat)
- Upload an image and ask questions about it (vision)
- Get answers from the Grok model served through OpenRouter

This project uses the official `openai` Python SDK pointing at the OpenRouter API.

Repository: [zakcali/open-router](https://github.com/zakcali/open-router)  
Entry point: `openrouter-image-analysis.py`

---

## Features

- Text-only or image+text prompts
- Automatic base64 encoding of uploaded images
- Runs locally via Gradio UI
- Uses OpenRouter with the `x-ai/grok-4-fast:free` model by default

---

## Quickstart

### Prerequisites
- Python 3.9+ (recommended)
- An OpenRouter API key: create one at [OpenRouter](https://openrouter.ai)

### 1) Clone and enter the repo
```bash
git clone https://github.com/zakcali/open-router.git
cd open-router
```

### 2) Create a virtual environment and install dependencies
```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

python -m pip install -U pip
pip install openai gradio pillow
```

### 3) Set your API key (OPENROUTER_API_KEY)

- macOS/Linux:
```bash
export OPENROUTER_API_KEY="sk-or-xxxxxxxxxxxxxxxx"
```

- Windows (PowerShell):
```powershell
$env:OPENROUTER_API_KEY="sk-or-xxxxxxxxxxxxxxxx"
```

- Windows (Command Prompt):
```cmd
set OPENROUTER_API_KEY=sk-or-xxxxxxxxxxxxxxxx
```

Tip: You can also use a `.env` loader if you prefer, but this script reads from the environment directly.

### 4) Run the app
```bash
python openrouter-image-analysis.py
```

Gradio will print a local URL (and optionally a public share URL) to your terminal. Open it in your browser.

---

## Usage

1. Optional: Upload an image (PNG/JPG).  
2. Optional: Enter a prompt or question.  
   - If you don’t provide a prompt but upload an image, the app uses: “Describe this image in detail.”
3. Click “Analyze.”  
4. Read the model’s text response in the right-hand panel.  
5. Use “Clear Inputs” to reset.

---

## How it works (Code Overview)

File: `openrouter-image-analysis.py`

- Libraries:
  - `openai` (the official OpenAI Python SDK) configured to point at OpenRouter
  - `gradio` for UI
  - `PIL` (Pillow) for basic image handling
  - `base64`/`BytesIO` for encoding images into data URLs

- API Client:
  ```python
  from openai import OpenAI
  client = OpenAI(
      base_url="https://openrouter.ai/api/v1",
      api_key=os.environ.get("OPENROUTER_API_KEY"),
  )
  ```

- The main function `get_grok_response(prompt, source_image)`:
  - Validates `OPENROUTER_API_KEY`.
  - If an image is provided, converts it to JPEG bytes and builds a `data:image/jpeg;base64,...` data URL.
  - Builds the `messages` payload for chat completions:
    - Text-only:
      ```json
      [{"role": "user", "content": "your prompt"}]
      ```
    - Image+text:
      ```json
      [{
        "role": "user",
        "content": [
          {"type": "text", "text": "your prompt"},
          {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
        ]
      }]
      ```
  - Calls:
    ```python
    client.chat.completions.create(
      model="x-ai/grok-4-fast:free",
      messages=api_messages,
      max_tokens=4096,
    )
    ```
  - Displays the first choice’s text content in the UI.

- UI:
  - Built with `gr.Blocks` and includes:
    - Image uploader (PIL)
    - Prompt textbox
    - Analyze & Clear buttons
    - Read-only textbox for the model’s response
    - Status area for success/error messages

---

## Changing the model

To use a different OpenRouter model, update the `model` field in the `chat.completions.create(...)` call:

```python
completion = client.chat.completions.create(
    model="x-ai/grok-4:latest",  # example
    messages=api_messages,
    max_tokens=2048,
)
```

Find available models and pricing on [OpenRouter Models](https://openrouter.ai/models). Some models require additional provider setup or may not support images.

---

## Troubleshooting

- “CRITICAL: OPENROUTER_API_KEY environment variable not found.”  
  Set your key and restart the app. Confirm the variable is in the same shell session used to run Python.

- 401 Unauthorized or similar auth errors  
  Ensure the key is valid, has not expired, and is prefixed correctly (e.g., `sk-or-...`).

- Large image issues or timeouts  
  Very large uploads may slow down encoding or exceed limits. Try smaller images, or compress before uploading.

- Blank responses  
  The free tier or selected model may throttle or return empty content under load. Try again or switch models.

---

## Security Notes

- Never commit API keys to source control.
- Prefer environment variables or a secret manager for production use.
- The app converts images to JPEG for transmission; transparency will be lost and color profiles may change.

---

## Extending the app

Ideas:
- Add a model dropdown in the UI
- Support streaming responses
- Temperature/Top-p controls
- Drag-and-drop multiple images
- Preserve original image format (PNG/WebP) when possible
- Add logging and better error messages in the UI

---

## License and Acknowledgments

- Uses the `openai` Python SDK, pointing at the OpenRouter API.
- UI built with [Gradio](https://gradio.app).
- Grok models provided via [OpenRouter](https://openrouter.ai).

See the repository’s license file for details.
