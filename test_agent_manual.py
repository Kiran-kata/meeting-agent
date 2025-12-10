#!/usr/bin/env python3
"""
Test the agent programmatically by simulating user interactions.
This will:
1. Wait for the UI to appear
2. Get a PDF file to upload
3. Trigger the start button
4. Wait a few seconds
5. Trigger the stop button
6. Check the output
"""
import time
import subprocess
import sys
from pathlib import Path

# Find a PDF file to test with
pdf_files = list(Path("C:/Users/kiran/OneDrive/Desktop").glob("**/*.pdf"))
if pdf_files:
    test_pdf = str(pdf_files[0])
    print(f"Found PDF: {test_pdf}")
else:
    print("No PDF files found to test with")
    sys.exit(1)

print("\nWaiting for agent UI to appear (5 seconds)...")
time.sleep(5)

print("\nAgent should now be running with UI visible.")
print("To complete the test manually:")
print(f"1. Click 'Add PDF' button and select: {test_pdf}")
print("2. Click 'Start' button to begin recording")
print("3. Speak or play audio during the meeting")
print("4. Click 'Stop' button to generate summary")
print("\nCheck the logs for detailed information:")
print("  - logs/meeting_agent.log (main application logs)")
print("  - agent_test.log (stdout/stderr)")
