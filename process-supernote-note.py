#!/usr/bin/env python3

import os
import sys
import json
import base64
import subprocess
from datetime import datetime
from dotenv import load_dotenv
import requests
import shutil

# Load environment variables from the .env file
load_dotenv()

# Script to convert Supernote .note files to PDF and use Gemini 2.5 Pro API for handwriting recognition
# Before first use, store gemini api key in ~/.api_keys/gemini_key

# Set up variables
SUPERNOTE_TOOL_PATH = os.getenv("SUPERNOTE_TOOL_PATH")
os.environ["PATH"] = f"{SUPERNOTE_TOOL_PATH}:{os.environ['PATH']}" # Add supernote-tool to PATH
GOOGLE_API_KEY = open(os.path.expanduser("~/.api_keys/gemini_key")).read().strip()
GEMINI_MODEL = "gemini-2.5-pro-exp-03-25"
GEMINI_ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GOOGLE_API_KEY}"
OBSIDIAN_DIR = os.getenv("OBSIDIAN_DIR") # daily notes directory

# Add supernote-tool to PATH
os.environ["PATH"] = f"{SUPERNOTE_TOOL_PATH}:{os.environ['PATH']}"

# Check if API key is set
if not GOOGLE_API_KEY:
    print("Error: GOOGLE_API_KEY environment variable is not set.")
    sys.exit(1)

# Check if input file was provided
if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} <path_to_note_file>")
    sys.exit(1)

INPUT_FILE = sys.argv[1]
NOTE_DIR = os.path.dirname(INPUT_FILE)
PROCESSED_DIR = os.path.join(NOTE_DIR, "processed_notes")

# Check if input file exists and has .note extension
if not os.path.isfile(INPUT_FILE):
    print(f"Error: Input file '{INPUT_FILE}' does not exist.")
    sys.exit(1)

if not INPUT_FILE.endswith('.note'):
    print("Error: Input file must have .note extension.")
    sys.exit(1)

# Extract base filename and check if it starts with 8 digits
FILENAME = os.path.basename(INPUT_FILE)[:-5]
if not FILENAME[:8].isdigit():
    print("Error: File name must start with 8 digits in YYYYMMDD format")
    sys.exit(1)

# Extract date components
DATE_PART = FILENAME[:8]
date_obj = datetime.strptime(DATE_PART, "%Y%m%d")

# Get date components
YEAR = date_obj.strftime("%Y")
MONTH = date_obj.strftime("%m")
DAY = date_obj.strftime("%d")
MONTH_NAME = date_obj.strftime("%b")
DAY_OF_WEEK = date_obj.strftime("%a")

# Create processed_notes directory if it doesn't exist
os.makedirs(PROCESSED_DIR, exist_ok=True)

# Construct Obsidian paths
OBSIDIAN_SUBDIR = os.path.join(OBSIDIAN_DIR, YEAR, f"{MONTH}-{MONTH_NAME}")
OBSIDIAN_FILE = os.path.join(OBSIDIAN_SUBDIR, f"{YEAR}-{MONTH}-{DAY} {DAY_OF_WEEK}.md")

# Create attachments directory if it doesn't exist
ATTACHMENTS_DIR = os.path.join(OBSIDIAN_SUBDIR, "attachments")
os.makedirs(ATTACHMENTS_DIR, exist_ok=True)

# Define PDF filename and path
PDF_FILENAME = f"{YEAR}-{MONTH}-{DAY}_supernote.pdf"
PDF_PATH = os.path.join(ATTACHMENTS_DIR, PDF_FILENAME)

print(f"Date detected: {YEAR}-{MONTH}-{DAY} ({DAY_OF_WEEK})")
print(f"Target Obsidian file: {OBSIDIAN_FILE}")
print(f"Converting {INPUT_FILE} to PDF...")

# Use supernote-tool to convert .note to PDF
try:
    subprocess.run(["supernote-tool", "convert", "-t", "pdf", "-a", INPUT_FILE, PDF_PATH], check=True)
except subprocess.CalledProcessError:
    print("Error: Failed to convert .note file to PDF.")
    sys.exit(1)

print("Sending PDF to Gemini API for handwriting recognition...")

# Create JSON request
with open(PDF_PATH, "rb") as pdf_file:
    pdf_base64 = base64.b64encode(pdf_file.read()).decode('utf-8')

json_request = {
    "contents": [{
        "parts": [
            {
                "text": "- Recognize the handwriting and other content in this image\
                - Convert it to organized markdown format, which should not be enclosed in backtick symbols\
                - Preserve headings, lists, list indentation, horizontal rules, tables, blockquotes, and other structures\
                - Underlined text on its own line should be a H3 header in markdown, prefixed with: ### \
                - For text written in ALL CAPS, convert to traditional capitalization\
                - A task is text in the image that has AI in a circle to the left of it. Include it in markdown preceded exactly by the characters between asterisks here: *- [ ] * (that is: hyphen, space, left-bracket, space, right bracket, space). For example: - [ ] action item text\
                - For any text that is highlighted in the image, add == before and after the highlighted text, with no space between the == and the highlighted text on either end. For example: ==highlighted text==\
                - Text with one asterisk before and after it should be maintained as markdown italic. For example: *italic text here*\
                - Text with two asterisks before and after it should be maintained as markdown bold.  For example: **bold text here**\
                - text with three asterisks before and after it should be maintained as markdown bold italics. For example ***very important text***\
                - Blockquotes in the image will have a > symbol to the left and should be maintained as markdown blockquote. For example: > blockquote text\
                "
            },
            {
                "inline_data": {
                    "mime_type": "application/pdf",
                    "data": pdf_base64
                }
            }
        ]
    }]
}

# Send request to Gemini API
response = requests.post(GEMINI_ENDPOINT, json=json_request)
response_json = response.json()

# Extract the text content from the response
MARKDOWN_CONTENT = response_json['candidates'][0]['content']['parts'][0]['text']

if MARKDOWN_CONTENT:
    print("✓ Text extracted successfully")
    
    # Create Obsidian directory structure if it doesn't exist
    os.makedirs(OBSIDIAN_SUBDIR, exist_ok=True)
    
    # Create Obsidian file if it doesn't exist
    if not os.path.isfile(OBSIDIAN_FILE):
        with open(OBSIDIAN_FILE, 'w') as f:
            f.write("\n")
        print("✓ Created new Obsidian file")
    else:
        print("✓ Using existing Obsidian file")
    
    # Check if the file already has a Supernote section
    with open(OBSIDIAN_FILE, 'r+') as f:
        content = f.read()
        if "## ✨ Supernote" not in content:
            f.write("\n## ✨ Supernote\n")
            print("✓ Added Supernote section")
        else:
            print("✓ Found existing Supernote section")
        
        # Find the Supernote section and add new content
        lines = content.split('\n')
        new_lines = []
        supernote_found = False
        for line in lines:
            new_lines.append(line)
            if line == "## ✨ Supernote":
                supernote_found = True
                new_lines.extend([
                    "",
                    MARKDOWN_CONTENT,
                    "",
                    f"![[attachments/{PDF_FILENAME}]]"
                ])
        
        if not supernote_found:
            new_lines.extend([
                "",
                "## ✨ Supernote",
                "",
                MARKDOWN_CONTENT,
                "",
                f"![[attachments/{PDF_FILENAME}]]"
            ])
        
        # Write the updated content back to the file
        f.seek(0)
        f.write('\n'.join(new_lines))
        f.truncate()

    # Move the original .note file to the processed directory
    try:
        shutil.move(INPUT_FILE, PROCESSED_DIR)
        print(f"✓ Moved original file to: {os.path.join(PROCESSED_DIR, os.path.basename(FILENAME))}")
        print("✅ Processing complete!")
        sys.exit(0)  # Explicit successful exit
    except Exception as e:
        print(f"❌ Error moving file to processed directory: {os.path.basename(FILENAME)}")
        print(f"Error details: {str(e)}")
        sys.exit(1)

else:
    print("Error: Failed to extract markdown content from API response.")
    print(f"API Response: {response_json}")
    sys.exit(1)
