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

# --- Core Logic (Unified approach) ---
def get_multimodal_response(prompt, source_image, model_choice):
    if not api_key:
        raise gr.Error("OPENROUTER_API_KEY not set.")
    if not prompt and not source_image:
        raise gr.Error("Please enter a prompt or upload an image.")
    
    # If no prompt is provided with an image, use a default one.
    if source_image and not prompt:
        prompt = "Describe this image in detail."

    api_messages = []
    extra_params = {}

    try:
        # --- Construct the payload based on user input ---
        if source_image:
            # If an image is provided, ALWAYS format it as a vision request.
            # The API will return an error if the model doesn't support image inputs.
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
            max_tokens=8192,
            **extra_params
        )

        # --- Process the response ---
        message = completion.choices[0].message
        text_response = message.content or ""
        image_output = None

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

        return (text_response, image_output, status_message)

    except Exception as e:
        print(f"An API error occurred: {e}")
        # Display the raw API error to the user
        error_message = f"❌ An API error occurred: {e}"
        return ("", None, error_message)

# --- Gradio User Interface ---
with gr.Blocks(theme=gr.themes.Soft(), title="👁️ Multimodal AI Studio") as demo:
    gr.Markdown("# 👁️ Multimodal AI Studio (via OpenRouter)")
    gr.Markdown("Provide a text prompt and/or an image to any model and see what happens.")
    with gr.Row():
        with gr.Column(scale=1):
            model_choice = gr.Dropdown(
               label="Choose a Model",
               choices=[
                   "x-ai/grok-4-fast:free",
                   "qwen/qwen2.5-vl-72b-instruct:free",
                   "meta-llama/llama-3.2-90b-vision-instruct",
                   "google/gemini-2.0-flash-exp:free",
                   "meta-llama/llama-4-maverick:free",
                   "google/gemini-2.5-flash-image-preview"
               ],
               value="x-ai/grok-4-fast:free"
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
        with gr.Column(scale=1):
            text_output_box = gr.Textbox(label="Model's Text Response", lines=5, interactive=False)
            image_output_box = gr.Image(label="Image Output", interactive=False, height=400)

    run_btn.click(
        fn=get_multimodal_response,
        inputs=[prompt_box, input_image, model_choice],
        outputs=[text_output_box, image_output_box, status_box]
    )

    clear_btn.click(
        fn=lambda: (None, "", "", None, "Inputs and outputs cleared."),
        inputs=None,
        outputs=[input_image, prompt_box, text_output_box, image_output_box, status_box],
        queue=False
    )

if __name__ == "__main__":
    print("Launching Gradio interface... Press Ctrl+C to exit.")
    demo.launch()