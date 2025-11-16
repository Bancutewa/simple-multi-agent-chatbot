#!/usr/bin/env python3
"""
Test script để kiểm tra API key loading
"""

import os
import sys
sys.path.insert(0, 'src')

def test_api_key_loading():
    """Test xem API key có được load đúng từ env không"""
    print("🧪 Testing API key loading...")

    # Test without API key
    if 'GEMINI_API_KEY' in os.environ:
        del os.environ['GEMINI_API_KEY']

    try:
        from main_chatbot import MainChatbot
        print("❌ Should have failed without API key")
        return False
    except SystemExit:
        print("✅ Correctly stopped when no API key")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

    # Test with API key
    os.environ['GEMINI_API_KEY'] = 'test_key_123'

    try:
        chatbot = MainChatbot()
        if chatbot.api_key == 'test_key_123':
            print("✅ API key loaded correctly from environment")
            return True
        else:
            print(f"❌ API key not loaded correctly: {chatbot.api_key}")
            return False
    except Exception as e:
        print(f"❌ Error initializing chatbot: {e}")
        return False

if __name__ == "__main__":
    success = test_api_key_loading()
    print(f"\n{'✅ All tests passed!' if success else '❌ Some tests failed!'}")
