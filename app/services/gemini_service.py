from typing import Optional
import os
import google.generativeai as genai
from ..config import settings


class GeminiService:
    def __init__(self):
        api_key = settings.gemini_api_key or os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
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
            
            Objective: Improve clarity, conciseness, and impact while maintaining a professional yet student-friendly tone.
            
            Rules:
            - Eliminate marketing fluff, excessive exclamation marks, and emojis.
            - Ensure strict grammatical accuracy.
            - Keep the tone serious, calm, and trustworthy.
            - DO NOT alter or remove specific details (dates, times, prices, locations, links, or names).
            - Return ONLY the refined body text without any titles or commentary.
            
            Original Text: "{text}"
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip() if response.text else text
            
        except Exception as e:
            print(f"Gemini refinement failed: {e}")
            return text
    
    async def generate_post_title(self, content: str, post_type: str) -> str:
        if not self.enabled:
            # Fallback: use first 50 chars
            return content[:50].strip() + "..."
        
        try:
            prompt = f"""
            Generate a concise, compelling title for a {post_type} post with this content.
            Make it engaging but professional, suitable for a university audience.
            Max 60 characters.
            
            Content: "{content[:500]}"
            
            Title:
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip() if response.text else content[:50].strip() + "..."
            
        except Exception as e:
            print(f"Gemini title generation failed: {e}")
            return content[:50].strip() + "..."