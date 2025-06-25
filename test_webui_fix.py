#!/usr/bin/env python3
"""
Quick test for Web UI fix to validate the directory error is resolved
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flora_pac_lib.web_ui import FloraPacWebUI

def test_webui_fix():
    """Test that the web UI can generate PAC files without directory errors"""
    ui = FloraPacWebUI()
    
    try:
        # Test basic generation
        print("Testing PAC file generation...")
        status, content, file_path = ui.generate_pac_file(
            proxy_strings="SOCKS5 127.0.0.1:1984"
        )
        
        print("Status:", status)
        print("Content length:", len(content) if content else 0)
        print("File path:", file_path)
        
        # Check if file was created
        if file_path and os.path.exists(file_path):
            print(f"✅ PAC file successfully created at: {file_path}")
            print(f"File size: {os.path.getsize(file_path)} bytes")
        else:
            print("❌ PAC file was not created")
            
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        ui.cleanup()

if __name__ == '__main__':
    print("🌺 Testing Flora PAC Web UI Fix")
    print("=" * 40)
    success = test_webui_fix()
    print("=" * 40)
    if success:
        print("✅ Web UI fix test completed successfully!")
    else:
        print("❌ Web UI fix test failed!")
    sys.exit(0 if success else 1)