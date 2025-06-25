"""
Flora PAC Web UI Module

Provides Gradio-based web interface for generating PAC files with
visual configuration and real-time preview.
"""

import tempfile
import os
from typing import List, Tuple, Optional
import gradio as gr
from .ip_data import fetch_ip_data, merge_all
from .network_ops import fregment_nets, hash_nets
from .pac_generator import generate_balanced_proxy, generate_no_proxy, _generate_pac_content


class FloraPacWebUI:
    """Web UI controller for Flora PAC generator"""
    
    def __init__(self):
        self.temp_files = []
    
    def generate_pac_file(
        self,
        proxy_strings: str,
        balance_mode: str = "no",
        no_proxy_networks: str = "",
        hash_base: int = 3011,
        mask_step: int = 2
    ) -> Tuple[str, str, str]:
        """
        Generate PAC file with given parameters
        
        Returns:
            Tuple of (status_message, pac_content, file_path)
        """
        try:
            # Parse proxy strings
            proxies = [p.strip() for p in proxy_strings.split('\n') if p.strip()]
            if not proxies:
                return "Error: At least one proxy must be specified", "", ""
            
            # Parse no-proxy networks
            no_proxy_list = []
            if no_proxy_networks.strip():
                no_proxy_list = [n.strip() for n in no_proxy_networks.split('\n') if n.strip()]
            
            # Fetch and process IP data
            status_msg = "Fetching China IP ranges..."
            china_nets = fetch_ip_data()
            merged_nets = merge_all(china_nets)
            
            # Fragment networks
            fragmented_nets = fregment_nets(merged_nets, mask_step)
            
            # Generate hash tables  
            hash_tables = hash_nets(fragmented_nets, hash_base)
            
            # Calculate prefix range for PAC generation
            from .network_ops import calculate_prefix_range
            min_prefixlen, max_prefixlen = calculate_prefix_range(merged_nets)
            
            # Generate final PAC content using the internal function
            pac_content = _generate_pac_content(
                hash_tables, 
                proxies,
                balance_mode,
                no_proxy_list,
                hash_base, 
                mask_step,
                min_prefixlen,
                max_prefixlen,
                merged_nets
            )
            
            # Save PAC file to current directory for easy access
            try:
                output_path = os.path.join(os.getcwd(), "flora_pac.pac")
                # Ensure the directory exists and is writable
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(pac_content)
            except Exception:
                # If we can't write to current directory, use temp file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.pac', delete=False, encoding='utf-8') as f:
                    f.write(pac_content)
                    output_path = f.name
                    self.temp_files.append(output_path)
            
            stats = f"Generated PAC file successfully!\n"
            stats += f"- China networks: {len(china_nets)}\n"
            stats += f"- Merged networks: {len(merged_nets)}\n"
            stats += f"- Fragmented networks: {len(fragmented_nets)}\n"
            stats += f"- Hash base: {hash_base}\n"
            stats += f"- Proxy mode: {balance_mode}\n"
            stats += f"- File size: {len(pac_content)} bytes\n"
            stats += f"- Saved to: {output_path}"
            
            return stats, pac_content, output_path
            
        except Exception as e:
            import traceback
            error_msg = f"Error generating PAC file: {str(e)}\n"
            error_msg += f"Error type: {type(e).__name__}\n"
            error_msg += f"Current directory: {os.getcwd()}\n"
            error_msg += f"Traceback:\n{traceback.format_exc()}"
            return error_msg, "", ""
    
    def create_interface(self) -> gr.Interface:
        """Create and configure Gradio interface"""
        
        with gr.Blocks(
            title="Flora PAC Generator",
            theme=gr.themes.Soft(),
            css="""
            .gradio-container {
                max-width: 1200px !important;
            }
            .pac-preview {
                font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                font-size: 12px;
            }
            """
        ) as interface:
            
            gr.Markdown("""
            # 🌺 Flora PAC Generator
            
            Generate optimized PAC (Proxy Auto-Config) files for China IP ranges.
            Configure your proxy settings below and generate a PAC file for your browser.
            """)
            
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### Proxy Configuration")
                    
                    proxy_input = gr.Textbox(
                        label="Proxy Servers (one per line)",
                        placeholder="SOCKS5 127.0.0.1:1984\nSOCKS5 127.0.0.1:1989",
                        lines=4,
                        info="Enter proxy servers, one per line. Example: SOCKS5 127.0.0.1:1984"
                    )
                    
                    balance_mode = gr.Dropdown(
                        label="Load Balance Mode",
                        choices=[
                            ("No balancing", "no"),
                            ("Local IP based", "local_ip"), 
                            ("Host based", "host")
                        ],
                        value="no",
                        info="Choose how to distribute load across multiple proxies"
                    )
                    
                    no_proxy_input = gr.Textbox(
                        label="No-Proxy Networks (optional)",
                        placeholder="192.168.0.0/24\n10.0.0.0/8",
                        lines=3,
                        info="Networks that should bypass proxy (CIDR notation)"
                    )
                    
                    gr.Markdown("### Performance Tuning")
                    
                    with gr.Row():
                        hash_base = gr.Slider(
                            label="Hash Base",
                            minimum=1009,
                            maximum=9973,  
                            step=2,
                            value=3011,
                            info="Hash table size (larger = faster matching, bigger file)"
                        )
                        
                        mask_step = gr.Slider(
                            label="Mask Step",
                            minimum=1,
                            maximum=4,
                            step=1,
                            value=2,
                            info="Network fragmentation step (smaller = more precise)"
                        )
                    
                    generate_btn = gr.Button(
                        "🚀 Generate PAC File",
                        variant="primary",
                        size="lg"
                    )
                
                with gr.Column(scale=1):
                    gr.Markdown("### Results")
                    
                    status_output = gr.Textbox(
                        label="Status",
                        lines=8,
                        interactive=False,
                        info="Generation status and statistics"
                    )
                    
                    gr.Markdown("""
                    **Download Instructions:**
                    - PAC file saved to project directory as `flora_pac.pac`
                    - Copy the PAC content below to create your own file
                    - Or use the saved file path shown in the status
                    """)
            
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### PAC File Preview")
                    pac_preview = gr.Code(
                        label="Generated PAC Content",
                        language="javascript",
                        lines=15,
                        elem_classes=["pac-preview"]
                    )
            
            # Wrapper function to handle the file path return value
            def generate_for_ui(*args):
                status, content, file_path = self.generate_pac_file(*args)
                return status, content
            
            # Event handlers
            generate_btn.click(
                fn=generate_for_ui,
                inputs=[
                    proxy_input,
                    balance_mode, 
                    no_proxy_input,
                    hash_base,
                    mask_step
                ],
                outputs=[status_output, pac_preview]
            )
            
            # Examples
            gr.Markdown("""
            ### 💡 Usage Examples
            
            **Basic SOCKS5 Proxy:**
            ```
            SOCKS5 127.0.0.1:1984
            ```
            
            **Multiple Proxies with Load Balancing:**
            ```
            SOCKS5 127.0.0.1:1984
            SOCKS5 127.0.0.1:1989
            ```
            Set balance mode to "Local IP based" or "Host based"
            
            **Browser Compatibility (SOCKS5 + SOCKS fallback):**
            ```
            SOCKS5 127.0.0.1:1984; SOCKS 127.0.0.1:1984
            ```
            
            **No-Proxy Networks:**
            ```
            192.168.0.0/24
            10.0.0.0/8
            172.16.0.0/12
            ```
            """)
        
        return interface
    
    def launch(
        self, 
        server_name: str = "127.0.0.1",
        server_port: int = 7860,
        share: bool = False,
        **kwargs
    ):
        """Launch the web interface"""
        interface = self.create_interface()
        return interface.launch(
            server_name=server_name,
            server_port=server_port,
            share=share,
            **kwargs
        )
    
    def cleanup(self):
        """Clean up temporary files"""
        for temp_file in self.temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass
        self.temp_files.clear()


def create_web_ui() -> FloraPacWebUI:
    """Factory function to create web UI instance"""
    return FloraPacWebUI()


# For backwards compatibility and direct import
def launch_web_ui(
    server_name: str = "127.0.0.1", 
    server_port: int = 7860,
    share: bool = False,
    **kwargs
):
    """Launch Flora PAC web interface"""
    ui = create_web_ui()
    return ui.launch(
        server_name=server_name,
        server_port=server_port, 
        share=share,
        **kwargs
    )