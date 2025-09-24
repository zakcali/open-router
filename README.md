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

# 👁️ Multimodal Image & Text Analyzer (via OpenRouter)

A simple Gradio web app that lets you:
- Ask questions with plain text (chat)
- Upload an image and ask questions about it (vision)
- Select among multiple vision-capable models from a dropdown
- Get answers via the OpenRouter API using the official `openai` Python SDK (pointed at OpenRouter)
- Download the text response as a Markdown file
- Temporary files are automatically cleaned up on exit

Repository: [zakcali/open-router](https://github.com/zakcali/open-router)  
Entry point: `openrouter-image-analysis.py`

---

## Features

- Text-only or image+text prompts
- Model selection dropdown (pick a vision model per request)
  - Default: `x-ai/grok-4-fast:free`
  - Also includes: `qwen/qwen2.5-vl-72b-instruct:free`, `meta-llama/llama-3.2-90b-vision-instruct`, `google/gemini-2.0-flash-exp:free`, `meta-llama/llama-4-maverick:free`
- Automatic base64 encoding of uploaded images
- Runs locally via Gradio UI
- Status area shows which model handled your request
- Uses `max_tokens=32768` by default

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

1. Choose a vision model from the “Choose a Vision Model” dropdown.  
   - The default is `x-ai/grok-4-fast:free`.
2. Optional: Upload an image (PNG/JPG).  
3. Optional: Enter a prompt or question.  
   - If you don’t provide a prompt but upload an image, the app uses: “Describe this image in detail.”
4. Click “Analyze.”  
5. Read the model’s text response in the right-hand panel.  
6. Use “🗑️ Clear I/O” to reset inputs and output.

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

- Core function `get_vision_response(prompt, source_image, model_choice)`:
  - Validates `OPENROUTER_API_KEY`.
  - Falls back to “Describe this image in detail.” if no prompt is provided but an image is uploaded.
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
  - Calls OpenRouter with the selected model:
    ```python
    completion = client.chat.completions.create(
      model=model_choice,
      messages=api_messages,
      max_tokens=32768,
    )
    ```
  - Returns the first choice’s text content and a status message like:
    ```
    ✅ Analysis complete with <model_choice>.
    ```

- UI (Gradio `Blocks`):
  - Model selection dropdown with vision-capable models
  - Image uploader (PIL)
  - Prompt textbox
  - “Analyze” button
  - “🗑️ Clear I/O” button
  - Read-only textbox for the model’s response
  - Status area for success/error messages

---

## Changing or adding models

- Use the dropdown in the UI to switch models at runtime—no code changes needed.
- To change the default or add/remove options, edit the dropdown in `openrouter-image-analysis.py`:
  ```python
  model_choice = gr.Dropdown(
      label="Choose a Vision Model",
      choices=[
          "x-ai/grok-4-fast:free",
          "qwen/qwen2.5-vl-72b-instruct:free",
          "meta-llama/llama-3.2-90b-vision-instruct",
          "google/gemini-2.0-flash-exp:free",
          "meta-llama/llama-4-maverick:free",
      ],
      value="x-ai/grok-4-fast:free"
  )
  ```
- Find available models and pricing on [OpenRouter Models](https://openrouter.ai/models). Some models require additional provider setup or may not support images.

---

## Troubleshooting

- “CRITICAL: OPENROUTER_API_KEY environment variable not found.”  
  Set your key and restart the app. Confirm the variable is in the same shell session used to run Python.

- 401 Unauthorized or similar auth errors  
  Ensure the key is valid, has not expired, and is prefixed correctly (e.g., `sk-or-...`).

- Large image issues or timeouts  
  Very large uploads may slow down encoding or exceed limits. Try smaller images, or compress before uploading.

- Blank or partial responses  
  Free tiers or certain models may throttle or return empty/short content under load. Try again, switch models, or reduce prompt size. Note that responses can still be limited by provider-side caps even with `max_tokens=32768`.

- UI shows an unexpected error  
  The status area will show errors like:
  ```
  ❌ An unexpected error occurred: <details>
  ```
  Check your network, model availability on OpenRouter, and logs in the terminal.

---

## Security Notes

- Never commit API keys to source control.
- Prefer environment variables or a secret manager for production use.
- The app converts images to JPEG for transmission; transparency will be lost, and color profiles may change.
- Large images increase memory usage and latency due to base64 encoding.

---

## Extending the app

Ideas:
- Add more models to the dropdown or group them by provider.
- Persist last-used model selection.
- Support streaming responses.
- Temperature/Top-p controls.
- Drag-and-drop multiple images.
- Preserve original image format (PNG/WebP) when possible.
- Add logging and richer error messages in the UI.
- Export results (e.g., JSON with detected entities/tags).

---

## License and Acknowledgments

- Uses the `openai` Python SDK, pointing at the OpenRouter API.
- UI built with [Gradio](https://gradio.app).
- Models provided via [OpenRouter](https://openrouter.ai).

See the repository’s license file for details.

# 👁️🛠️ Multimodal Image Analyzer & Generator (via OpenRouter)

A simple Gradio web app that now lets you:
- Ask questions with plain text (chat)
- Upload an image and ask questions about it (vision analysis)
- Generate new images from a text prompt (when supported by the selected model)
- Modify or transform an uploaded image based on your prompt (when supported)
- Select among multiple vision-capable models from a dropdown
- Get answers and outputs via the OpenRouter API using the official `openai` Python SDK (pointed at OpenRouter)
- Download the text response as a Markdown file
- Temporary files are automatically cleaned up on exit

Repository: [zakcali/open-router](https://github.com/zakcali/open-router)  
Entry point: `openrouter-image-analysis.py`

---

## What’s new

- Image generation and editing support with capable models (e.g., `google/gemini-2.5-flash-image-preview`)
- Output panel can display text, images, or both—depending on what the model returns
- Keeps the simple “one-click” flow: the same button handles analysis, generation, and edits based on your prompt and the selected model’s capabilities

---

## Features

- Text-only or image+text prompts
- Image generation from text prompts (model-dependent)
- Image modification of an uploaded image (model-dependent)
- Model selection dropdown (pick a vision/generative model per request)
  - Default: `x-ai/grok-4-fast:free`
  - Also includes: `qwen/qwen2.5-vl-72b-instruct:free`, `meta-llama/llama-3.2-90b-vision-instruct`, `google/gemini-2.0-flash-exp:free`, `meta-llama/llama-4-maverick:free`, `google/gemini-2.5-flash-image-preview`
- Automatic base64 encoding of uploaded images (for input to models)
- Renders image outputs (when the model returns images) alongside text responses
- Runs locally via Gradio UI
- Status area shows which model handled your request
- Uses `max_tokens=32768` by default

Note: Not all listed models can generate or edit images. For image generation/editing, choose a capable model such as `google/gemini-2.5-flash-image-preview`.

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

There’s one unified flow. What happens depends on your prompt and the selected model’s capabilities.

- For analysis (describe, answer questions, OCR, etc.):
  1. Choose a vision model from the “Choose a Vision Model” dropdown.
     - The default is `x-ai/grok-4-fast:free`.
  2. Optional: Upload an image (PNG/JPG).
  3. Enter a prompt or question.
     - If you don’t provide a prompt but upload an image, the app uses: “Describe this image in detail.”
  4. Click “Analyze.”
  5. Read the model’s text response in the right-hand panel.

- For image generation:
  1. Select a model that can return images (e.g., `google/gemini-2.5-flash-image-preview`).
  2. Do not upload a source image; just enter a generative prompt (e.g., “A watercolor painting of a fox in a misty forest at sunrise”).
  3. Click “Analyze.”
  4. If the model returns images, they’ll render in the output panel (with any accompanying text).

- For image modification:
  1. Select a model that can return/modify images (e.g., `google/gemini-2.5-flash-image-preview`).
  2. Upload a source image.
  3. Enter instructions for the edit (e.g., “Make it look like nighttime with neon lights,” or “Convert to a pencil sketch”).
  4. Click “Analyze.”
  5. The output panel will show edited images if the model supports and returns them.

Use “🗑️ Clear I/O” to reset inputs and outputs at any time.

---

## How it works (Code Overview)

File: `openrouter-image-analysis.py`

- Libraries:
  - `openai` (the official OpenAI Python SDK) configured to point at OpenRouter
  - `gradio` for UI
  - `PIL` (Pillow) for basic image handling
  - `base64`/`BytesIO` for encoding uploaded images into data URLs

- API Client:
  ```python
  from openai import OpenAI
  client = OpenAI(
      base_url="https://openrouter.ai/api/v1",
      api_key=os.environ.get("OPENROUTER_API_KEY"),
  )
  ```

- Core function (conceptual) for building requests:
  - Validates `OPENROUTER_API_KEY`.
  - Falls back to “Describe this image in detail.” if no prompt is provided but an image is uploaded.
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
  - Calls OpenRouter with the selected model:
    ```python
    completion = client.chat.completions.create(
      model=model_choice,
      messages=api_messages,
      max_tokens=32768,
    )
    ```
  - The app displays:
    - Text responses in a read-only textbox.
    - Image responses (if the model returns images) in an image output area or gallery.

Notes:
- Image generation and editing rely on the model returning image content in its response format (e.g., image URLs or base64-encoded data). Not all models support this.
- Some providers/models may only return text descriptions even when asked to generate or edit an image.

---

## Changing or adding models

- Use the dropdown in the UI to switch models at runtime—no code changes needed.
- To change the default or add/remove options, edit the dropdown in `openrouter-image-analysis.py`:
  ```python
  model_choice = gr.Dropdown(
      label="Choose a Vision Model",
      choices=[
          "x-ai/grok-4-fast:free",
          "qwen/qwen2.5-vl-72b-instruct:free",
          "meta-llama/llama-3.2-90b-vision-instruct",
          "google/gemini-2.0-flash-exp:free",
          "meta-llama/llama-4-maverick:free",
          "google/gemini-2.5-flash-image-preview",
      ],
      value="x-ai/grok-4-fast:free"
  )
  ```
- Find available models and pricing on [OpenRouter Models](https://openrouter.ai/models). Some models require additional provider setup, may be in preview, or may not return images.

---

## Troubleshooting

- “CRITICAL: OPENROUTER_API_KEY environment variable not found.”
  Set your key and restart the app. Confirm the variable is in the same shell session used to run Python.

- 401 Unauthorized or similar auth errors
  Ensure the key is valid, has not expired, and is prefixed correctly (e.g., `sk-or-...`).

- Not seeing images in the output
  - Make sure you selected a model that can return images (e.g., `google/gemini-2.5-flash-image-preview`).
  - Some models only support analysis; they won’t generate images even with generative prompts.
  - Try a simpler prompt or a different model.

- Large image issues or timeouts
  Very large uploads may slow down encoding or exceed limits. Try smaller images, or compress before uploading.

- Blank or partial responses
  Free tiers or certain models may throttle or return empty/short content under load. Try again, switch models, or reduce prompt size. Note that responses can still be limited by provider-side caps even with `max_tokens=32768`.

- UI shows an unexpected error
  The status area will show errors like:
  ```
  ❌ An unexpected error occurred: <details>
  ```
  Check your network, model availability on OpenRouter, and logs in the terminal.

---

## Security Notes

- Never commit API keys to source control.
- Prefer environment variables or a secret manager for production use.
- The app converts uploaded images to JPEG for transmission; transparency will be lost, and color profiles may change.
- Generated images may be large; decoding base64 image data increases memory use.
- Respect model/provider content policies and the licensing/usage terms for generated outputs.

---

## Extending the app

Ideas:
- Add more models to the dropdown or group them by provider.
- Persist last-used model selection.
- Support streaming responses.
- Temperature/Top-p controls.
- Drag-and-drop multiple images and show a gallery.
- Optional masking/inpainting UI for more precise edits.
- Preserve original input image format (PNG/WebP) when possible.
- Add logging and richer error messages in the UI.
- Export results (e.g., JSON with detected entities/tags).
- Toggle between “Analyze” and “Generate/Edit” modes in the UI to guide users.

---

## License and Acknowledgments

- Uses the `openai` Python SDK, pointing at the OpenRouter API.
- UI built with [Gradio](https://gradio.app).
- Models provided via [OpenRouter](https://openrouter.ai).

See the repository’s license file for details.
