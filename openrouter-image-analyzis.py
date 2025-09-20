# --- START OF FILE gradio-openrouter-grok.py ---

import os
import gradio as gr
from openai import OpenAI # <-- 1. Switched to the OpenAI library
from PIL import Image
from io import BytesIO
import base64 # <-- 2. Added for image encoding

# --- Configuration ---
# 3. Changed to use OPENROUTER_API_KEY
api_key = os.environ.get("OPENROUTER_API_KEY")
if not api_key:
    print("CRITICAL: OPENROUTER_API_KEY environment variable not found.")

# --- Initialize the OpenAI client to connect to OpenRouter ---
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

# --- Core Logic (modified for OpenRouter and Grok) ---
def get_grok_response(prompt, source_image):
    if not api_key:
        raise gr.Error("OPENROUTER_API_KEY not set.")
    if not prompt or not prompt.strip():
        # 4. If an image is provided, a prompt isn't strictly necessary
        if source_image is None:
            raise gr.Error("Please enter a prompt (or upload an image).")
        else:
            prompt = "Describe this image in detail." # Default prompt

    # --- 5. Construct the API message payload ---
    api_messages = []
    if source_image is None:
        # Text-to-text functionality
        api_messages.append({"role": "user", "content": prompt})
    else:
        # Image-to-text functionality
        # Convert PIL Image to base64 data URL
        buffered = BytesIO()
        source_image.save(buffered, format="JPEG") # Save image to a memory buffer
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        image_url = f"data:image/jpeg;base64,{img_str}"

        # Build the message structure for vision models
        api_messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_url}},
            ],
        })

    try:
        # --- 6. Make the API call to OpenRouter ---
        completion = client.chat.completions.create(
            model="x-ai/grok-4-fast:free",
            messages=api_messages,
            max_tokens=4096, # Optional: set a limit for the response
        )
        
        # --- 7. Process the text-only response ---
        text_response = completion.choices[0].message.content
        return (text_response, "✅ Analysis complete.")

    except Exception as e:
        # Catch any other unexpected errors
        print(f"An unexpected error occurred: {e}")
        error_message = f"❌ An unexpected error occurred: {e}"
        return ("", error_message)

# --- 8. Simplified Gradio User Interface ---
with gr.Blocks(theme=gr.themes.Soft(), title="👁️ Grok Image & Text Analyzer") as demo:
    gr.Markdown("# 👁️ Grok Image & Text Analyzer (via OpenRouter)")
    gr.Markdown("Provide a text prompt, OR upload an image and ask a question about it.")
    with gr.Row():
        with gr.Column(scale=1):
            input_image = gr.Image(type="pil", label="Upload an Image (Optional)", height=400)
            prompt_box = gr.Textbox(
                label="Your Prompt",
                placeholder="What is in this image? or Ask anything...",
                lines=5
            )
            with gr.Row():
                clear_btn = gr.Button(value="🗑️ Clear Inputs", scale=1)
                generate_btn = gr.Button("Analyze", variant="primary", scale=2)
            status_box = gr.Markdown("")
        with gr.Column(scale=1):
            # The UI is now focused on text output
            text_output_box = gr.Textbox(
                label="Model's Text Response",
                visible=True, # Now always visible
                lines=20,
                interactive=False
            )

    # Update the click function and its inputs/outputs
    generate_btn.click(
        fn=get_grok_response,
        inputs=[prompt_box, input_image],
        outputs=[text_output_box, status_box]
    )
    # Clear function now clears all inputs
    clear_btn.click(
        fn=lambda: (None, "", "Inputs cleared."),
        inputs=None,
        outputs=[input_image, prompt_box, status_box],
        queue=False
    )

if __name__ == "__main__":
    print("Launching Gradio interface... Press Ctrl+C to exit.")
    demo.launch()