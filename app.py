#!/usr/bin/env python3
"""
AI Chatbot Assistant - Main Entry Point
"""

import sys
import os

# Thêm thư mục src vào Python path để import intents
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.main_chatbot import main

if __name__ == "__main__":
    main()
