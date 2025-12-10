#!/usr/bin/env python3
"""
Quick test of Gemini API to verify it's working
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

try:
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content("What is the capital of France?")
    print(f"✓ API Working!")
    print(f"Response: {response.text}")
    print(f"Model: gemini-2.5-flash")
except Exception as e:
    print(f"✗ API Error: {e}")
