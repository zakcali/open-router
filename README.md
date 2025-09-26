# OpenRouter Text-to-Text Chatbot

A lightweight Gradio app to chat with multiple models on [OpenRouter](https://openrouter.ai/) using the OpenAI Python SDK. It supports streaming responses, optional reasoning traces, message downloads, and automatic cleanup of temporary files.

The chatbot is now configurable via external files, allowing you to easily customize the model list and system prompt without editing the Python code.

- File: `openrouter-text2text.py`
- Repo: [zakcali/open-router](https://github.com/zakcali/open-router)

## Features

- Simple, fast chat UI built with Gradio.
- **External Configuration:** Manage the model list and default system prompt via `models.txt` and `system-prompt.txt`.
- Streaming token-by-token responses.
- Model picker with a customizable list of models from OpenRouter.
- Reasoning controls:
  - For OpenAI models (gpt-oss/gpt-5): uses `reasoning: { effort: low|medium|high }`.
  - For Grok-4-fast: enables reasoning when effort is medium or high.
  - Other models ignore this setting gracefully.
- Adjustable temperature and max tokens.
- Download the last assistant response as a Markdown file.
- Temporary files are automatically cleaned up on exit.

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

1.  **Get an OpenRouter API Key**: Visit https://openrouter.ai/ to get your key.
2.  **Set the Environment Variable**:

    -   macOS/Linux:
        ```bash
        export OPENROUTER_API_KEY="your-api-key"
        ```
    -   Windows (PowerShell):
        ```powershell
        setx OPENROUTER_API_KEY "your-api-key"
        ```

3.  **(Required) Create `models.txt`**: In the same directory as the script, create a file named `models.txt`. Add the OpenRouter model identifiers you want to use, one per line. For example:
    ```text
    x-ai/grok-4-fast:free
    meta-llama/llama-3.1-405b-instruct:free
    google/gemini-2.0-flash-exp:free
    openai/gpt-oss-120b:free
    qwen/qwen3-coder:free
    ```
    The first model in this file will be the default selection in the UI.

4.  **(Optional) Create `system-prompt.txt`**: In the same directory, you can create a file named `system-prompt.txt` to set the default system instructions. For example:
    ```text
    You are an expert programmer. Your answers should be concise, accurate, and provide code examples where possible.
    ```
    If this file is not found, a generic "You are a helpful assistant" prompt will be used.

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
python openrouter-text2text.py
```

Then open the local URL Gradio prints (e.g., http://127.0.0.1:7860). Press Ctrl+C to stop. All tracked temporary download files are deleted on exit.

## Using the App

-   **Chat area**:
    -   Enter a message and click Send (or press Enter).
    -   Streaming tokens update the assistant message live.
    -   **Stop** cancels in-flight requests.
    -   **Clear Chat** resets the conversation and hides the download button.

-   **Right panel controls**:
    -   **Model dropdown**: Choose any model from your `models.txt` file.
    -   **System Instructions**: Set the assistant’s behavior. The initial value is loaded from `system-prompt.txt`.
    -   **Reasoning Control**:
        -   OpenAI models (`openai/gpt-oss-*`, `openai/gpt-5-*`): sets `reasoning.effort` to `low|medium|high`.
        -   Grok-4-fast: when `medium` or `high`, enables `reasoning.enabled=true`.
        -   Other models ignore this control, and you may see “This model does not expose reasoning traces.”
    -   **Temperature**: 0.0–2.0
    -   **Max Tokens**: 100–65535 (upper bound depends on model/support)

-   **Download Last Response**:
    -   Becomes visible after an assistant reply completes.
    -   Saves a `.md` file to your OS temp directory and provides a direct download.
    -   Files are tracked and removed automatically on app exit.

## Models

The model dropdown is now populated from your `models.txt` file. You can find a list of available models, including free ones, on the [OpenRouter Models page](https://openrouter.ai/models).

Notes:
- This is a text-to-text app. If you select a vision-capable model, it will be used in text mode.
- Not all models provide reasoning streams; when absent, the “Model Thoughts” panel will indicate that no trace is available.

## How Streaming and Reasoning Work

The core function `chat_with_openai`:
- Builds the message list from your chat history and system instructions.
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

- **Missing API key**:
  - Symptom: HTTP 401/403 or “You must provide an API key.”
  - Fix: Ensure `OPENROUTER_API_KEY` is set in your environment and your shell session is refreshed.

- **`models.txt` not found**:
  - Symptom: The app starts with a default, limited list of models.
  - Fix: Create `models.txt` in the same directory as the script and populate it with your desired model identifiers.

- **Rate limits or model unavailability**:
  - Symptom: Server error or stalls.
  - Fix: Try a different model from your list or reduce request frequency.

- **Large `max_tokens`**:
  - Symptom: Errors if the selected model doesn’t support the requested context/length.
  - Fix: Lower `max_tokens` or temperature; consider shorter prompts.

- **No reasoning content**:
  - Many models don’t emit a separate reasoning stream. This is expected behavior.

## Extending the Script

- **Add or remove a model**: Simply edit the `models.txt` file and restart the app.
- **Change the default system prompt**: Edit the `system-prompt.txt` file.
- **Map new reasoning semantics**:
  ```python
  elif "provider/model-name" in model_choice:
      request_params["extra_body"] = {
          "reasoning": { "some_param": "value" }
      }
  ```
- **Tweak the streaming flush interval**: Adjust the `flush_interval_s` variable in the script.
- **Make the app public**: Launch it with `demo.launch(share=True)`.

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
- Select from a list of vision-capable models populated from an external file (`models-image.txt`)
- Customize the system prompt via a UI textbox, with the initial prompt loaded from `system-prompt-image.txt`
- Control the `max_tokens` for the response with a UI slider
- Get answers via the OpenRouter API using the official `openai` Python SDK
- Download the text response as a Markdown file
- Automatically clean up temporary files on exit

Repository: [zakcali/open-router](https://github.com/zakcali/open-router)
Entry point: `openrouter-image-analysis.py`

---

## Features

- Text-only or image+text prompts
- **External Model List**: Model selection dropdown is populated from `models-image.txt`, making it easy to customize.
- **Configurable System Prompt**: Edit the system instructions directly in the UI. The default prompt is loaded from `system-prompt-image.txt`.
- **Adjustable Max Tokens**: Control the maximum length of the model's response using a slider.
- Automatic base64 encoding of uploaded images
- Runs locally via Gradio UI
- Status area shows which model handled your request
- Downloadable responses

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

### 4) Create Configuration Files
The app requires two text files to run. Create them in the same directory as the script.

**a. Create `models-image.txt`:**
This file lists the models that will appear in the dropdown. Add one model name per line. The first model in the file will be the default.

*macOS/Linux:*
```bash
touch models-image.txt
```
*Windows:*
```cmd
echo. > models-image.txt
```
**Example `models-image.txt` content:**
```
x-ai/grok-4-fast:free
qwen/qwen2.5-vl-72b-instruct:free
google/gemini-2.0-flash-exp:free
meta-llama/llama-4-maverick:free
meta-llama/llama-4-scout:free```

**b. Create `system-prompt-image.txt`:**
This file contains the default system instructions for the model.

*macOS/Linux:*
```bash
touch system-prompt-image.txt
```
*Windows:*
```cmd
echo. > system-prompt-image.txt
```
**Example `system-prompt-image.txt` content:**
```
You are an expert at analyzing images.
```

### 5) Run the app
```bash
python openrouter-image-analysis.py
```

Gradio will print a local URL (and optionally a public share URL) to your terminal. Open it in your browser.

---

## Usage

1.  Choose a vision model from the “Choose a Vision Model” dropdown.
2.  Optional: Modify the system prompt in the "System Instructions" textbox.
3.  Optional: Adjust the "Max Tokens" slider to limit the response length.
4.  Optional: Upload an image (PNG/JPG).
5.  Optional: Enter a text prompt or question.
    -   If you don’t provide a prompt but upload an image, the app uses: “Describe this image in detail.”
6.  Click “Analyze.”
7.  Read the model’s text response.
8.  Use “🗑️ Clear I/O” to reset inputs and output.

---

## How it works (Code Overview)

File: `openrouter-image-analysis.py`

- **Libraries**: `openai`, `gradio`, `PIL`, `base64`, `BytesIO`.
- **Configuration**: The app starts by calling `load_models()` and `load_system_prompt()` to read from `models-image.txt` and `system-prompt-image.txt`.
- **Core function `get_vision_response(prompt, source_image, model_choice, instructions, max_tokens)`**:
    - If an image is provided, it's converted to a `data:image/jpeg;base64,...` data URL.
    - Builds the `messages` payload, including a `system` message if provided:
      ```json
      [
        {"role": "system", "content": "your instructions"},
        {"role": "user", "content": [
          {"type": "text", "text": "your prompt"},
          {"type": "image_url", "image_url": {"url": "data:..."}}
        ]}
      ]
      ```
    - Calls OpenRouter with the user's selected model and parameters:
      ```python
      completion = client.chat.completions.create(
        model=model_choice,
        messages=api_messages,
        max_tokens=int(max_tokens),
      )
      ```
    - Returns the text content and updates the UI.
- **UI (Gradio `Blocks`)**: The UI is laid out in two columns, with inputs on the left and outputs/settings on the right.

---

## Changing or adding models

To change the models available in the dropdown, simply **edit the `models-image.txt` file**.

1.  Open `models-image.txt` in a text editor.
2.  Add, remove, or reorder the model names (one per line).
3.  The model on the very first line will be the default selection when the app starts.
4.  Save the file and restart the `openrouter-image-analysis.py` script to see your changes.

Find available models and pricing on [OpenRouter Models](https://openrouter.ai/models).

---

## Troubleshooting

- **“CRITICAL: OPENROUTER_API_KEY environment variable not found.”**
  Set your key and restart the app. Confirm the variable is in the same shell session used to run Python.

- **`FileNotFoundError` on startup.**
  Make sure you have created `models-image.txt` and `system-prompt-image.txt` in the same directory as the script.

- **Blank or partial responses.**
  This can happen if the value of "Max Tokens" is too low. Try increasing the slider. Free models may also throttle or return empty content under heavy load.

- **UI shows an unexpected error.**
  The status area will show errors like `❌ An unexpected error occurred: <details>`. Check your network, model availability on OpenRouter, and logs in the terminal.

---

## Security Notes

- Never commit API keys to source control.
- Prefer environment variables or a secret manager for production use.
- The app converts images to JPEG for transmission; transparency will be lost.
- Large images increase memory usage and latency due to base64 encoding.

Of course. I've updated the `README.md` file to reflect the latest script's capabilities, including the new UI elements for system prompts and max tokens, and the external configuration for the model list.

The file has been updated to use the new script name (`openrouter-image-analysis-and-generator.py`) and provides clear instructions on how to create and use the new `models-image.txt` and `system-prompt-image.txt` files.

Here is the revised `README.md`:

---

# 👁️ Multimodal AI Studio (via OpenRouter)

A simple Gradio web app that now lets you:
- Ask questions with plain text (chat)
- Upload an image and ask questions about it (vision analysis)
- Generate new images from a text prompt (when supported by the selected model)
- Modify or transform an uploaded image based on your prompt (when supported)
- **Select from a list of models loaded from an external file (`models-image.txt`)**
- **Customize the system prompt in the UI, with the initial prompt loaded from `system-prompt-image.txt`**
- **Control the `max_tokens` for the response with a UI slider**
- Get answers and outputs via the OpenRouter API using the official `openai` Python SDK
- Download the text response as a Markdown file
- Temporary files are automatically cleaned up on exit

Repository: [zakcali/open-router](https://github.com/zakcali/open-router)
Entry point: `openrouter-image-analysis-and-generator.py`

---

## What’s new

- **Image generation and editing support** with capable models (e.g., `google/gemini-2.5-flash-image-preview`)
- The output panel can display **text, images, or both**—depending on what the model returns
- **External configuration** for the model list and initial system prompt, making customization easy.
- **UI controls for `max_tokens` and system instructions** for more fine-grained control over model behavior.

---

## Features

- Text-only or image+text prompts
- Image generation from text prompts (model-dependent)
- Image modification of an uploaded image (model-dependent)
- **External Model List**: Model selection dropdown is populated from `models-image.txt`.
- **Configurable System Prompt**: Edit the system instructions directly in the UI. The default is loaded from `system-prompt-image.txt`.
- **Adjustable Max Tokens**: Control the maximum length of the model's response using a slider.
- Automatic base64 encoding of uploaded images
- Renders image outputs alongside text responses
- Runs locally via Gradio UI
- Status area shows which model handled your request

Note: Not all models can generate or edit images. For image generation/editing, choose a capable model such as `google/gemini-2.5-flash-image-preview`.

---

## Quickstart

### Prerequisites
- Python 3.9+ (recommended)
- An OpenRouter API key: create one at [OpenRouter](https://openrouter.ai)

### 1) Clone and enter the repo```bash
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

- Windows (PowerShell):```powershell
$env:OPENROUTER_API_KEY="sk-or-xxxxxxxxxxxxxxxx"
```

- Windows (Command Prompt):
```cmd
set OPENROUTER_API_KEY=sk-or-xxxxxxxxxxxxxxxx
```

### 4) Create Configuration Files
The app requires two text files to run. Create them in the same directory as the script.

**a. Create `models-image.txt`:**
This file lists the models for the dropdown. Add one model name per line. The first model is the default.
**Example content:**
```
x-ai/grok-4-fast:free
google/gemini-2.5-flash-image-preview
qwen/qwen2.5-vl-72b-instruct:free
meta-llama/llama-4-maverick:free
```

**b. Create `system-prompt-image.txt`:**
This file contains the default system instructions for the model.
**Example content:**
```
You are a helpful multimodal AI assistant. You can analyze images and generate them.
```

### 5) Run the app
```bash
python openrouter-image-analysis-and-generator.py
```

Gradio will print a local URL. Open it in your browser.

---

## Usage

- **For analysis (describe, OCR, etc.):**
  1. Choose a vision model from the dropdown.
  2. Optional: Modify the **System Instructions** or adjust the **Max Tokens** slider on the right.
  3. Upload an image and enter a prompt (e.g., "What brand is this?").
  4. Click “Run Model.”

- **For image generation:**
  1. Select a model that can return images (e.g., `google/gemini-2.5-flash-image-preview`).
  2. Optional: Modify the system prompt and `max_tokens`.
  3. Do **not** upload an image. Enter a generative prompt (e.g., “A watercolor painting of a fox in a misty forest”).
  4. Click “Run Model.”

- **For image modification:**
  1. Select a model that can modify images.
  2. Upload a source image.
  3. Enter instructions for the edit (e.g., “Make this look like a pencil sketch”).
  4. Click “Run Model.”

Use “🗑️ Clear I/O” to reset inputs and outputs at any time.

---

## How it works (Code Overview)

File: `openrouter-image-analysis-and-generator.py`

- **Configuration**: The app starts by calling `load_models()` and `load_system_prompt()` to read from the `.txt` files.
- **Core function `get_multimodal_response(...)`**:
    - Takes `prompt`, `source_image`, `model_choice`, `instructions`, and `max_tokens` from the UI.
    - Builds the `messages` payload, including a `system` message from the instructions box.
      ```json
      [
        {"role": "system", "content": "your instructions"},
        {"role": "user", "content": "your prompt"}
      ]
      ```
    - If no image is uploaded, it adds `{"modalities": ["image", "text"]}` to the request to signal to the model that we want an image in return.
    - Calls OpenRouter with the selected model and parameters:
      ```python
      completion = client.chat.completions.create(
        model=model_choice,
        messages=api_messages,
        max_tokens=int(max_tokens),
        **extra_params
      )
      ```
    - The app displays text responses and decodes any base64 image data returned by the model for display.

---

## Changing, Adding, or Reordering Models

To change the models available in the dropdown, simply **edit the `models-image.txt` file**.

1.  Open `models-image.txt` in a text editor.
2.  Add, remove, or reorder the model names (one per line).
3.  The model on the very **first line** will be the default selection when the app starts.
4.  Save the file and restart the Python script to see your changes.

Find available models and pricing on [OpenRouter Models](https://openrouter.ai/models).

---

## Troubleshooting

- **`FileNotFoundError` on startup.**
  Make sure you have created `models-image.txt` and `system-prompt-image.txt` in the same directory as the script.

- **Not seeing images in the output.**
  - Make sure you selected a model that can return images (e.g., `google/gemini-2.5-flash-image-preview`). Many models only support analysis.
  - Try a simpler prompt or a different generative model.

- **Blank or partial responses.**
  - This can happen if the value of **"Max Tokens"** is too low. Try increasing the slider.
  - Free models may throttle or return empty content under heavy load.

- **UI shows an unexpected error.**
  The status area will show errors like: `❌ An unexpected error occurred: <details>`. Check your network, model availability on OpenRouter, and logs in the terminal.
