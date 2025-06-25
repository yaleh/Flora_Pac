"""
Test suite for Flora PAC Web UI module
"""

import os
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock
from flora_pac_lib.web_ui import FloraPacWebUI, create_web_ui, launch_web_ui


class TestFloraPacWebUI:
    """Test cases for FloraPacWebUI class"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.ui = FloraPacWebUI()
    
    def teardown_method(self):
        """Cleanup after each test"""
        self.ui.cleanup()
    
    def test_init(self):
        """Test FloraPacWebUI initialization"""
        assert self.ui.temp_files == []
    
    @patch('flora_pac_lib.web_ui.fetch_ip_data')
    @patch('flora_pac_lib.web_ui.merge_nets')
    @patch('flora_pac_lib.web_ui.fregment_nets')
    @patch('flora_pac_lib.web_ui.hash_nets')
    @patch('flora_pac_lib.web_ui.generate_pac')
    def test_generate_pac_file_basic(
        self, 
        mock_generate_pac,
        mock_hash_nets,
        mock_fregment_nets,
        mock_merge_nets,
        mock_fetch_ip_data
    ):
        """Test basic PAC file generation"""
        # Setup mocks
        mock_fetch_ip_data.return_value = ['192.168.1.0/24']
        mock_merge_nets.return_value = ['192.168.1.0/24']
        mock_fregment_nets.return_value = ['192.168.1.0/24']
        mock_hash_nets.return_value = {'hash': 'table'}
        mock_generate_pac.return_value = 'function FindProxyForURL() { return "DIRECT"; }'
        
        # Test generation
        status, content, file_path = self.ui.generate_pac_file(
            proxy_strings="SOCKS5 127.0.0.1:1984"
        )
        
        # Verify results
        assert "Generated PAC file successfully!" in status
        assert "function FindProxyForURL" in content
        assert file_path.endswith('.pac')
        assert os.path.exists(file_path)
        
        # Verify mocks were called
        mock_fetch_ip_data.assert_called_once()
        mock_merge_nets.assert_called_once()
        mock_fregment_nets.assert_called_once()
        mock_hash_nets.assert_called_once()
        mock_generate_pac.assert_called_once()
    
    def test_generate_pac_file_empty_proxy(self):
        """Test PAC file generation with empty proxy strings"""
        status, content, file_path = self.ui.generate_pac_file(
            proxy_strings=""
        )
        
        assert "Error: At least one proxy must be specified" in status
        assert content == ""
        assert file_path == ""
    
    @patch('flora_pac_lib.web_ui.fetch_ip_data')
    def test_generate_pac_file_exception_handling(self, mock_fetch_ip_data):
        """Test exception handling in PAC file generation"""
        # Mock an exception
        mock_fetch_ip_data.side_effect = Exception("Network error")
        
        status, content, file_path = self.ui.generate_pac_file(
            proxy_strings="SOCKS5 127.0.0.1:1984"
        )
        
        assert "Error generating PAC file: Network error" in status
        assert content == ""
        assert file_path == ""
    
    @patch('flora_pac_lib.web_ui.fetch_ip_data')
    @patch('flora_pac_lib.web_ui.merge_nets')
    @patch('flora_pac_lib.web_ui.fregment_nets')
    @patch('flora_pac_lib.web_ui.hash_nets')
    @patch('flora_pac_lib.web_ui.generate_pac')
    def test_generate_pac_file_multiple_proxies(
        self,
        mock_generate_pac,
        mock_hash_nets,
        mock_fregment_nets, 
        mock_merge_nets,
        mock_fetch_ip_data
    ):
        """Test PAC file generation with multiple proxies"""
        # Setup mocks
        mock_fetch_ip_data.return_value = ['192.168.1.0/24']
        mock_merge_nets.return_value = ['192.168.1.0/24']
        mock_fregment_nets.return_value = ['192.168.1.0/24']
        mock_hash_nets.return_value = {'hash': 'table'}
        mock_generate_pac.return_value = 'function FindProxyForURL() { return "PROXY"; }'
        
        # Test with multiple proxies and balance mode
        status, content, file_path = self.ui.generate_pac_file(
            proxy_strings="SOCKS5 127.0.0.1:1984\nSOCKS5 127.0.0.1:1989",
            balance_mode="local_ip"
        )
        
        assert "Generated PAC file successfully!" in status
        assert "Proxy mode: local_ip" in status
    
    @patch('flora_pac_lib.web_ui.fetch_ip_data')
    @patch('flora_pac_lib.web_ui.merge_nets')
    @patch('flora_pac_lib.web_ui.fregment_nets')
    @patch('flora_pac_lib.web_ui.hash_nets')
    @patch('flora_pac_lib.web_ui.generate_pac')
    def test_generate_pac_file_with_no_proxy_networks(
        self,
        mock_generate_pac,
        mock_hash_nets,
        mock_fregment_nets,
        mock_merge_nets,
        mock_fetch_ip_data
    ):
        """Test PAC file generation with no-proxy networks"""
        # Setup mocks
        mock_fetch_ip_data.return_value = ['192.168.1.0/24']
        mock_merge_nets.return_value = ['192.168.1.0/24']
        mock_fregment_nets.return_value = ['192.168.1.0/24']
        mock_hash_nets.return_value = {'hash': 'table'}
        mock_generate_pac.return_value = 'function FindProxyForURL() { return "PROXY"; }'
        
        # Test with no-proxy networks
        status, content, file_path = self.ui.generate_pac_file(
            proxy_strings="SOCKS5 127.0.0.1:1984",
            no_proxy_networks="192.168.0.0/24\n10.0.0.0/8"
        )
        
        assert "Generated PAC file successfully!" in status
    
    def test_temp_file_cleanup(self):
        """Test temporary file cleanup functionality"""
        # Create some temp files manually
        for i in range(7):  # More than the limit of 5
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            temp_file.close()
            self.ui.temp_files.append(temp_file.name)
        
        # Verify initial state
        assert len(self.ui.temp_files) == 7
        
        # Trigger cleanup by simulating file generation
        with patch('flora_pac_lib.web_ui.fetch_ip_data') as mock_fetch:
            mock_fetch.side_effect = Exception("Test cleanup")
            self.ui.generate_pac_file("SOCKS5 127.0.0.1:1984")
        
        # Should still have all files since generation failed
        assert len(self.ui.temp_files) == 7
        
        # Test explicit cleanup
        self.ui.cleanup()
        assert len(self.ui.temp_files) == 0
    
    @patch('gradio.Blocks')
    def test_create_interface(self, mock_blocks):
        """Test Gradio interface creation"""
        # Mock the Blocks context manager
        mock_interface = Mock()
        mock_blocks.return_value.__enter__.return_value = mock_interface
        
        result = self.ui.create_interface()
        
        # Verify Blocks was called with expected parameters
        mock_blocks.assert_called_once()
        call_kwargs = mock_blocks.call_args[1]
        assert call_kwargs['title'] == "Flora PAC Generator"
        assert 'theme' in call_kwargs
        assert 'css' in call_kwargs
    
    @patch.object(FloraPacWebUI, 'create_interface')
    def test_launch(self, mock_create_interface):
        """Test web UI launch functionality"""
        # Mock interface
        mock_interface = Mock()
        mock_create_interface.return_value = mock_interface
        
        # Test launch
        result = self.ui.launch(
            server_name="0.0.0.0",
            server_port=8080,
            share=True
        )
        
        # Verify interface creation and launch
        mock_create_interface.assert_called_once()
        mock_interface.launch.assert_called_once_with(
            server_name="0.0.0.0",
            server_port=8080,
            share=True
        )


class TestFactoryFunctions:
    """Test factory functions and utilities"""
    
    def test_create_web_ui(self):
        """Test create_web_ui factory function"""
        ui = create_web_ui()
        assert isinstance(ui, FloraPacWebUI)
        assert ui.temp_files == []
        ui.cleanup()
    
    @patch.object(FloraPacWebUI, 'launch')
    def test_launch_web_ui(self, mock_launch):
        """Test launch_web_ui convenience function"""
        # Mock the launch method
        mock_launch.return_value = Mock()
        
        # Test launch
        result = launch_web_ui(
            server_name="localhost",
            server_port=7777,
            share=False
        )
        
        # Verify launch was called with correct parameters
        mock_launch.assert_called_once_with(
            server_name="localhost",
            server_port=7777,
            share=False
        )


class TestWebUIIntegration:
    """Integration tests for Web UI components"""
    
    @patch('flora_pac_lib.web_ui.fetch_ip_data')
    @patch('flora_pac_lib.web_ui.merge_nets')
    @patch('flora_pac_lib.web_ui.fregment_nets')
    @patch('flora_pac_lib.web_ui.hash_nets')
    @patch('flora_pac_lib.web_ui.generate_balanced_proxy')
    @patch('flora_pac_lib.web_ui.generate_no_proxy')
    @patch('flora_pac_lib.web_ui.generate_pac')
    def test_full_generation_pipeline(
        self,
        mock_generate_pac,
        mock_generate_no_proxy,
        mock_generate_balanced_proxy,
        mock_hash_nets,
        mock_fregment_nets,
        mock_merge_nets,
        mock_fetch_ip_data
    ):
        """Test full PAC generation pipeline with all components"""
        # Setup mocks to simulate real workflow
        mock_fetch_ip_data.return_value = [
            '1.2.3.0/24',
            '1.2.4.0/24'
        ]
        mock_merge_nets.return_value = [
            '1.2.3.0/23'  # Merged network
        ]
        mock_fregment_nets.return_value = [
            '1.2.3.0/24',
            '1.2.4.0/24'
        ]
        mock_hash_nets.return_value = {
            'hash_table': [0, 1, 0, 1],
            'masks': [24, 24]
        }
        mock_generate_balanced_proxy.return_value = "SOCKS5 127.0.0.1:1984"
        mock_generate_no_proxy.return_value = "192.168.0.0/16"
        mock_generate_pac.return_value = '''
function FindProxyForURL(url, host) {
    // Generated PAC content
    return "SOCKS5 127.0.0.1:1984";
}
'''
        
        ui = FloraPacWebUI()
        try:
            # Test full generation
            status, content, file_path = ui.generate_pac_file(
                proxy_strings="SOCKS5 127.0.0.1:1984\nSOCKS5 127.0.0.1:1989",
                balance_mode="host",
                no_proxy_networks="192.168.0.0/16\n10.0.0.0/8",
                hash_base=5003,
                mask_step=1
            )
            
            # Verify success
            assert "Generated PAC file successfully!" in status
            assert "China networks: 2" in status
            assert "Merged networks: 1" in status
            assert "Fragmented networks: 2" in status
            assert "Hash base: 5003" in status
            assert "Proxy mode: host" in status
            
            assert "function FindProxyForURL" in content
            assert file_path.endswith('.pac')
            assert os.path.exists(file_path)
            
            # Verify all components were called correctly
            mock_fetch_ip_data.assert_called_once()
            mock_merge_nets.assert_called_once_with(['1.2.3.0/24', '1.2.4.0/24'])
            mock_fregment_nets.assert_called_once_with(['1.2.3.0/23'], 1)
            mock_hash_nets.assert_called_once()
            mock_generate_balanced_proxy.assert_called_once()
            mock_generate_no_proxy.assert_called_once()
            mock_generate_pac.assert_called_once()
            
        finally:
            ui.cleanup()


if __name__ == '__main__':
    pytest.main([__file__])