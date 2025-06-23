"""
Integration tests for the modular Flora PAC system
"""
import pytest
import tempfile
import os
import subprocess
import sys
from unittest.mock import patch
import responses

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flora_pac_lib import generate_pac


class TestModularIntegration:
    """Integration tests for the modular system"""
    
    def test_flora_pac_lib_imports(self):
        """Test that all modular imports work correctly"""
        from flora_pac_lib import (
            fetch_ip_data, merge_nets, merge_all,
            fregment_net, fregment_nets, hash_address, hash_nets,
            generate_balanced_proxy, generate_no_proxy, generate_pac
        )
        
        # Verify all functions are callable
        assert callable(fetch_ip_data)
        assert callable(merge_nets)
        assert callable(merge_all)
        assert callable(fregment_net)
        assert callable(fregment_nets)
        assert callable(hash_address)
        assert callable(hash_nets)
        assert callable(generate_balanced_proxy)
        assert callable(generate_no_proxy)
        assert callable(generate_pac)
    
    def test_flora_pac_lib_metadata(self):
        """Test that package metadata is accessible"""
        import flora_pac_lib
        
        assert hasattr(flora_pac_lib, '__version__')
        assert hasattr(flora_pac_lib, '__author__')
        assert hasattr(flora_pac_lib, '__all__')
        
        # Check version format
        version_parts = flora_pac_lib.__version__.split('.')
        assert len(version_parts) >= 2
        
        # Check __all__ contains expected exports
        expected_exports = [
            'fetch_ip_data', 'merge_nets', 'merge_all',
            'fregment_net', 'fregment_nets', 'hash_address', 'hash_nets',
            'generate_balanced_proxy', 'generate_no_proxy', 'generate_pac'
        ]
        
        for export in expected_exports:
            assert export in flora_pac_lib.__all__
    
    @responses.activate
    def test_end_to_end_pac_generation(self):
        """Test complete end-to-end PAC generation with mocked data"""
        # Mock APNIC response
        mock_data = """2|apnic|20230101|46214|19830101|20230101|+1000
apnic|CN|ipv4|1.0.1.0|256|20110414|allocated
apnic|CN|ipv4|1.0.2.0|512|20110414|allocated
apnic|CN|ipv4|203.208.32.0|512|20110414|allocated"""
        
        responses.add(
            responses.GET,
            'http://ftp.apnic.net/apnic/stats/apnic/delegated-apnic-latest',
            body=mock_data,
            status=200
        )
        
        # Use temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pac', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Generate PAC file
            proxies = ['SOCKS5 127.0.0.1:1984']
            balance = 'no'
            no_proxy = ['192.168.0.0/24']
            
            with patch('builtins.print') as mock_print:
                generate_pac(proxies, balance, no_proxy, 
                           hash_base=101, mask_step=2, output_file=tmp_path)
            
            # Verify file was created
            assert os.path.exists(tmp_path)
            
            with open(tmp_path, 'r') as f:
                content = f.read()
            
            # Verify PAC file structure
            assert 'function FindProxyForURL(url, host)' in content
            assert 'HASH_BASE = 101' in content
            assert 'MASK_STEP = 2' in content
            assert "return 'SOCKS5 127.0.0.1:1984'" in content
            assert "isInNet(ip, '192.168.0.0', '255.255.255.0')" in content
            
            # Check that networks from mock data are included
            # The hash tables should contain data
            assert 'hashed_nets = [' in content
            
            # Verify statistics were printed
            assert mock_print.call_count > 0
            
        finally:
            # Clean up
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_main_script_functionality(self):
        """Test that the main flora_pac script works correctly"""
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'flora_pac')
        
        # Test help functionality
        result = subprocess.run([
            sys.executable, script_path, '--help'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert 'Generate proxy auto-config rules' in result.stdout
        assert '--proxy' in result.stdout
        assert '--balance' in result.stdout
        assert '--output' in result.stdout
        assert 'Examples:' in result.stdout
    
    def test_version_information(self):
        """Test that version information is available"""
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'flora_pac')
        
        # Test version functionality
        result = subprocess.run([
            sys.executable, script_path, '--version'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert 'Flora PAC' in result.stdout
        assert 'Modular' in result.stdout
    
    @responses.activate 
    def test_command_line_integration(self):
        """Test command line integration with mocked network data"""
        # Mock APNIC response
        mock_data = """apnic|CN|ipv4|192.168.0.0|256|20110414|allocated"""
        
        responses.add(
            responses.GET,
            'http://ftp.apnic.net/apnic/stats/apnic/delegated-apnic-latest',
            body=mock_data,
            status=200
        )
        
        # Test parameters
        proxies = ['SOCKS5 127.0.0.1:1984']
        balance = 'no'
        no_proxy = ['10.0.0.0/8']
        hash_base = 101
        mask_step = 2
        
        # Generate PAC files with modular approach
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pac', delete=False) as tmp1:
            tmp1_path = tmp1.name
            
        try:
            with patch('builtins.print'):
                generate_pac(proxies, balance, no_proxy, 
                           hash_base, mask_step, tmp1_path)
                
            with open(tmp1_path, 'r') as f:
                content = f.read()
            
            # Verify key components are present
            assert 'function FindProxyForURL(url, host)' in content
            assert f'HASH_BASE = {hash_base}' in content
            assert f'MASK_STEP = {mask_step}' in content
            assert "return 'SOCKS5 127.0.0.1:1984'" in content
            
        finally:
            if os.path.exists(tmp1_path):
                os.unlink(tmp1_path)
    
    def test_error_handling_integration(self):
        """Test error handling in the integrated system"""
        # Test with invalid proxy format
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pac', delete=False) as tmp:
            tmp_path = tmp.name
            
        try:
            # This should work even with unusual proxy formats
            with patch('builtins.print'):
                generate_pac(['INVALID_PROXY_FORMAT'], 'no', [], 
                           hash_base=11, mask_step=2, output_file=tmp_path)
            
            # File should still be created
            assert os.path.exists(tmp_path)
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)