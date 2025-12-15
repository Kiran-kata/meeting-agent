"""
Run Parakeet-Style Interview Assistant
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from frontend.main_parakeet import main

if __name__ == "__main__":
    main()
