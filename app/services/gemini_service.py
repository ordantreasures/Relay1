from typing import Optional
import os
import google.generativeai as genai
from ..config import settings


class GeminiService:
    def __init__(self):
        api_key = settings.gemini_api_key or os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("gemini-pro")
            self.enabled = True
        else:
            self.enabled = False

    async def refine_post_content(self, text: str, post_type: str) -> str:
        if not self.enabled:
            return text

        try:
            prompt = f"""
You are an elite campus editor for 'Relay', a minimalist university discovery app.
Refine the following text for a {post_type} post.

Rules:
- Improve clarity and conciseness
- Remove emojis and marketing fluff
- Preserve all factual details
- Return ONLY the refined text

Original Text:
"{text}"
            """

            response = self.model.generate_content(prompt)
            return response.text.strip() if response.text else text

        except Exception as e:
            print(f"Gemini refinement failed: {e}")
            return text

    async def generate_post_title(self, content: str, post_type: str) -> str:
        if not self.enabled:
            return content[:50].strip() + "..."

        try:
            prompt = f"""
Generate a concise, professional title for a {post_type} post.
Max 60 characters.

Content:
"{content[:500]}"

Title:
            """

            response = self.model.generate_content(prompt)
            return response.text.strip() if response.text else content[:50].strip() + "..."

        except Exception as e:
            print(f"Gemini title generation failed: {e}")
            return content[:50].strip() + "..."


# ✅ singleton instance
gemini_service = GeminiService()
