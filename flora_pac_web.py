#!/usr/bin/env python3
"""
Flora PAC Web Interface Entry Point

Launch Gradio web interface for Flora PAC generator.
"""

import argparse
import sys
import os

# Add current directory to path for development
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flora_pac_lib.web_ui import create_web_ui


def main():
    """Main entry point for web interface"""
    parser = argparse.ArgumentParser(
        description="Flora PAC Web Interface - Generate PAC files through web UI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                              # Launch on default port 7860
  %(prog)s --port 8080                  # Launch on custom port
  %(prog)s --host 0.0.0.0 --port 7860   # Allow external access
  %(prog)s --share                      # Create public Gradio link
        """
    )
    
    parser.add_argument(
        '--host', '--server-name',
        default='127.0.0.1',
        help='Host/IP to bind server to (default: 127.0.0.1)'
    )
    
    parser.add_argument(
        '--port', '--server-port',
        type=int,
        default=7860,
        help='Port to run server on (default: 7860)'
    )
    
    parser.add_argument(
        '--share',
        action='store_true',
        help='Create public Gradio share link'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='Flora PAC Web UI 1.0.0'
    )
    
    args = parser.parse_args()
    
    print("🌺 Flora PAC Web Interface")
    print("=" * 40)
    
    try:
        # Create and launch web UI
        ui = create_web_ui()
        
        print(f"Starting web server on {args.host}:{args.port}")
        if args.share:
            print("Creating public share link...")
        
        # Launch interface
        interface = ui.launch(
            server_name=args.host,
            server_port=args.port,
            share=args.share,
            debug=args.debug,
            inbrowser=True,  # Auto-open browser
            show_error=True,
            quiet=False
        )
        
        print("\n✅ Web interface launched successfully!")
        print(f"🌐 Local URL: http://{args.host}:{args.port}")
        
        if args.share and hasattr(interface, 'share_url'):
            print(f"🔗 Public URL: {interface.share_url}")
        
        print("\nPress Ctrl+C to stop the server")
        
        # Keep server running
        try:
            interface.block()
        except KeyboardInterrupt:
            print("\n\n🛑 Shutting down web server...")
            ui.cleanup()
            print("✅ Cleanup completed")
            
    except Exception as e:
        print(f"❌ Error starting web interface: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()