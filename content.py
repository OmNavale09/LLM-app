import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

import gradio as gr

load_dotenv()
api = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api)


def understand_content(content):
    system_prompt = "Understand the given content and describe it in details to help me post it on social media"

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.3,
            max_output_tokens=2000
        ),
        contents=content
    )
    return response.text

def social_media(content):
    system_prompt = "Generate description for LinkdIn, Twitter and Reddit"

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.3,
            max_output_tokens=2000
        ),
        contents=content
    )
    return response.text

def main(prompt):
    description = understand_content(prompt)
    response = social_media(description)
    return response



demo = gr.Interface(
    fn=main,
    inputs=[
        gr.Textbox(lines=8, placeholder="Enter a sentence to convert...", label="Input Sentence")
    ],
    outputs=gr.Textbox(lines=10, label="Social Media Output"),
    title="Content Repurposer"
)

demo.launch(debug=True)