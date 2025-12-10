#!/usr/bin/env python3
"""
List available Gemini models
"""
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("ERROR: GEMINI_API_KEY not set in .env")
    exit(1)

import google.generativeai as genai

genai.configure(api_key=api_key)

print("Available models:")
for model in genai.list_models():
    print(f"  - {model.name}")
