import os
import gradio as gr
from openai import OpenAI
from PIL import Image
from io import BytesIO
import base64

# --- Configuration ---
api_key = os.environ.get("OPENROUTER_API_KEY")
if not api_key:
    print("CRITICAL: OPENROUTER_API_KEY environment variable not found.")

# --- Initialize the OpenAI client to connect to OpenRouter ---
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

# --- Core Logic (modified for model selection) ---
def get_vision_response(prompt, source_image, model_choice):
    if not api_key:
        raise gr.Error("OPENROUTER_API_KEY not set.")
    if not prompt or not prompt.strip():
        if source_image is None:
            raise gr.Error("Please enter a prompt (or upload an image).")
        else:
            prompt = "Describe this image in detail."

    # --- Construct the API message payload ---
    api_messages = []
    if source_image is None:
        api_messages.append({"role": "user", "content": prompt})
    else:
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

    try:
        # --- Make the API call to OpenRouter with the selected model ---
        completion = client.chat.completions.create(
            model=model_choice, # Use the selected model
            messages=api_messages,
            max_tokens=8192,
        )

        text_response = completion.choices[0].message.content
        return (text_response, f"✅ Analysis complete with {model_choice}.")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        error_message = f"❌ An unexpected error occurred: {e}"
        return ("", error_message)

# --- Gradio User Interface ---
with gr.Blocks(theme=gr.themes.Soft(), title="👁️ Multimodal Image & Text Analyzer") as demo:
    gr.Markdown("# 👁️ Multimodal Image & Text Analyzer (via OpenRouter)")
    gr.Markdown("Provide a text prompt and/or an image, and select a model to analyze it.")
    with gr.Row():
        with gr.Column(scale=1):
            # --- Model Selection Dropdown ---
            model_choice = gr.Dropdown(
                label="Choose a Vision Model",
                choices=[
                    "x-ai/grok-4-fast:free",
                    "qwen/qwen2.5-vl-72b-instruct:free",
                    "qwen/qwen2.5-vl-32b-instruct:free",
                    "google/gemini-2.0-flash-exp:free",
                    "meta-llama/llama-4-maverick:free",
                    "meta-llama/llama-4-scout:free",
                    "mistralai/mistral-small-3.2-24b-instruct:free",
                    "moonshotai/kimi-vl-a3b-thinking:free",
                    "google/gemma-3-27b-it:free",
                    "google/gemini-2.5-flash-image-preview",
                    "meta-llama/llama-3.2-90b-vision-instruct",
                ],
                value="x-ai/grok-4-fast:free"
            )
            input_image = gr.Image(type="pil", label="Upload an Image (Optional)", height=350)
            prompt_box = gr.Textbox(
                label="Your Prompt",
                placeholder="What is in this image? or Ask anything...",
                lines=5
            )
            with gr.Row():
                clear_btn = gr.Button(value="🗑️ Clear I/O", scale=1)
                generate_btn = gr.Button("Analyze", variant="primary", scale=2)
            status_box = gr.Markdown("")
        with gr.Column(scale=1):
            text_output_box = gr.Textbox(
                label="Model's Text Response",
                visible=True,
                lines=20,
                interactive=False
            )

    # Update the click function to include the new model_choice input
    generate_btn.click(
        fn=get_vision_response,
        inputs=[prompt_box, input_image, model_choice],
        outputs=[text_output_box, status_box]
    )

# Clear function now clears all inputs and the text output
    clear_btn.click(
        fn=lambda: (None, "", "", "Inputs and output cleared."),
        inputs=None,
        outputs=[input_image, prompt_box, text_output_box, status_box],
        queue=False
    )

if __name__ == "__main__":
    print("Launching Gradio interface... Press Ctrl+C to exit.")
    demo.launch()