import os
import gradio as gr
from openai import OpenAI
from PIL import Image
from io import BytesIO
import base64
import tempfile
import atexit

# --- Temporary File Management ---

# This list will hold the paths of all generated chat logs for this session.
temp_files_to_clean = []

def cleanup_temp_files():
    """Iterates through the global list and deletes the tracked files."""
    if not temp_files_to_clean:
        return
    print(f"\nCleaning up {len(temp_files_to_clean)} temporary files...")
    for file_path in temp_files_to_clean:
        try:
            os.remove(file_path)
        except FileNotFoundError:
            pass # File was already deleted or never existed
        except Exception as e:
            print(f"  - Error removing {file_path}: {e}")
    print("Cleanup complete.")

# Register the cleanup function to be called on script exit
atexit.register(cleanup_temp_files)

print("Temporary download files will be saved in the OS's default temp directory and cleaned on exit.")


# --- Function to read system prompt from a file ---
def load_system_prompt(filepath="system-prompt-image.txt"):
    """Loads the system prompt from a text file, with a fallback default."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Warning: '{filepath}' not found. Using a default system prompt.")
        return "You are a helpful multimodal AI assistant."

# --- Function to read the model list from a file ---
def load_models(filepath="models-image.txt"):
    """Loads the list of models from a text file, with a fallback default list."""
    default_models = [
        "x-ai/grok-4-fast:free",
        "qwen/qwen2.5-vl-72b-instruct:free",
        "google/gemini-2.0-flash-exp:free",
        "meta-llama/llama-4-maverick:free",
        "meta-llama/llama-4-scout:free",
        "mistralai/mistral-small-3.2-24b-instruct:free",
        "moonshotai/kimi-vl-a3b-thinking:free",
        "google/gemma-3-27b-it:free",
        "google/gemini-2.5-flash-image-preview",
        "meta-llama/llama-3.2-90b-vision-instruct",
    ]
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            models = [line.strip() for line in f if line.strip()]
            if not models:
                print(f"Warning: '{filepath}' was empty. Using default model list.")
                return default_models
            return models
    except FileNotFoundError:
        print(f"Warning: '{filepath}' not found. Using default model list.")
        return default_models

# --- Configuration ---
api_key = os.environ.get("OPENROUTER_API_KEY")
if not api_key:
    print("CRITICAL: OPENROUTER_API_KEY environment variable not found.")

# --- Initialize the OpenAI client to connect to OpenRouter ---
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

# --- Core Logic (Unified approach) ---
def get_multimodal_response(prompt, source_image, model_choice, instructions, max_tokens):
    initial_download_update = gr.update(visible=False)

    if not api_key:
        raise gr.Error("OPENROUTER_API_KEY not set.")
    if not prompt and not source_image:
        raise gr.Error("Please enter a prompt or upload an image.")
    
    # If no prompt is provided with an image, use a default one.
    if source_image and not prompt:
        prompt = "Describe this image in detail."

    api_messages = []
    extra_params = {}
    
    # Add system prompt if provided
    if instructions and instructions.strip():
        api_messages.append({"role": "system", "content": instructions})

    try:
        # --- Construct the payload based on user input ---
        if source_image:
            # If an image is provided, ALWAYS format it as a vision request.
            buffered = BytesIO()
            source_image.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            image_url = f"data:image/jpeg;base64,{img_str}"

            api_messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            })
        else:
            # If ONLY text is provided, format it as a standard prompt
            # but add the parameter to request an image in the response.
            api_messages.append({"role": "user", "content": prompt})
            extra_params["extra_body"] = {"modalities": ["image", "text"]}

        # --- Make the API call ---
        completion = client.chat.completions.create(
            model=model_choice,
            messages=api_messages,
            max_tokens=int(max_tokens),
            **extra_params
        )

        # --- Process the response ---
        message = completion.choices[0].message
        text_response = message.content or ""
        image_output = None
        
        # Default to the initial hidden state for the download button
        download_update = initial_download_update

        if text_response:
            # If there's text, create a temporary file for download
            with tempfile.NamedTemporaryFile(delete=False, suffix=".md", mode="w", encoding="utf-8") as temp_file:
                output_filepath = temp_file.name
                temp_file.write(text_response)
            
            # Track the file for cleanup and prepare the button update
            temp_files_to_clean.append(output_filepath)
            print(f"Created and tracking temp file: {output_filepath}")
            download_update = gr.update(visible=True, value=output_filepath)


        if hasattr(message, 'images') and message.images:
            image_url = message.images[0]["image_url"]["url"]
            base64_data = image_url.split(",")[1]
            image_data = base64.b64decode(base64_data)
            image_output = Image.open(BytesIO(image_data))
            if not text_response.strip():
                text_response = "Image generated successfully."
            status_message = f"✅ Success with {model_choice}."
        else:
             status_message = f"✅ Text response received from {model_choice}."

        return (text_response, image_output, status_message, download_update)

    except Exception as e:
        print(f"An API error occurred: {e}")
        # Display the raw API error to the user
        error_message = f"❌ An API error occurred: {e}"
        return ("", None, error_message, initial_download_update)

# --- Load external configuration before building UI ---
model_list = load_models()
initial_system_prompt = load_system_prompt()
default_model = model_list[0] if model_list else None

# --- Gradio User Interface ---
with gr.Blocks(theme=gr.themes.Soft(), title="👁️ Multimodal AI Studio") as demo:
    gr.Markdown("# 👁️ Multimodal AI Studio (via OpenRouter)")
    gr.Markdown("Provide a text prompt and/or an image to any model and see what happens.")
    with gr.Row():
        # --- LEFT COLUMN ---
        with gr.Column(scale=1):
            model_choice = gr.Dropdown(
               label="Choose a Model",
               choices=model_list,
               value=default_model
            )
            input_image = gr.Image(type="pil", label="Upload an Image (Optional)", height=350)
            prompt_box = gr.Textbox(
                label="Your Prompt",
                placeholder="Ask a question or describe an image to generate...",
                lines=5
            )
            with gr.Row():
                clear_btn = gr.Button(value="🗑️ Clear I/O", scale=1)
                run_btn = gr.Button("Run Model", variant="primary", scale=2)
            status_box = gr.Markdown("")
        
        # --- RIGHT COLUMN ---
        with gr.Column(scale=1):
            text_output_box = gr.Textbox(
                label="Model's Text Response",
                lines=5,
                interactive=False,
                show_copy_button=True
            )
            download_btn = gr.DownloadButton(
                "⬇️ Download Text Response",
                visible=False
            )
            image_output_box = gr.Image(label="Image Output", interactive=False, height=400)
            
            # --- ADDED UI ELEMENTS ---
            instructions = gr.Textbox(
                label="System Instructions", 
                value=initial_system_prompt, 
                lines=3
            )
            max_tokens = gr.Slider(
                8192, 
                65535, 
                value=32768, 
                step=256, 
                label="Max Tokens"
            )

    # Define inputs and outputs for the Gradio function
    inputs_list = [prompt_box, input_image, model_choice, instructions, max_tokens]
    outputs_list = [text_output_box, image_output_box, status_box, download_btn]

    run_btn.click(
        fn=get_multimodal_response,
        inputs=inputs_list,
        outputs=outputs_list
    )

    # Configure the clear button
    clear_btn.click(
        fn=lambda: (None, "", "", None, "Inputs and outputs cleared.", gr.update(visible=False)),
        inputs=None,
        outputs=[input_image, prompt_box, text_output_box, image_output_box, status_box, download_btn],
        queue=False
    )

if __name__ == "__main__":
    print("Launching Gradio interface... Press Ctrl+C to exit.")
    demo.launch()