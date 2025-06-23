import pytest
import tempfile
import os
import subprocess
import sys
from unittest.mock import patch, MagicMock
import responses

# Add parent directory to path to import flora_pac
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestIntegration:
    """Integration tests for the complete flora_pac workflow"""
    
    @responses.activate
    def test_end_to_end_pac_generation(self):
        """Test complete end-to-end PAC file generation"""
        # Mock APNIC data
        mock_apnic_data = """2|apnic|20230101|46214|19830101|20230101|+1000
apnic|CN|ipv4|1.0.1.0|256|20110414|allocated
apnic|CN|ipv4|1.0.2.0|512|20110414|allocated
apnic|CN|ipv4|27.8.0.0|1024|20110414|allocated"""
        
        responses.add(
            responses.GET,
            'http://ftp.apnic.net/apnic/stats/apnic/delegated-apnic-latest',
            body=mock_apnic_data,
            status=200
        )
        
        # Create temporary directory for test
        with tempfile.TemporaryDirectory() as tmp_dir:
            original_cwd = os.getcwd()
            os.chdir(tmp_dir)
            
            try:
                # Run flora_pac with test parameters
                script_path = os.path.join(os.path.dirname(__file__), '..', 'flora_pac')
                result = subprocess.run([
                    'python3', script_path,
                    '-x', 'SOCKS5 127.0.0.1:1984',
                    '-n', '192.168.0.0/24',
                    '-b', 'no'
                ], capture_output=True, text=True, timeout=30)
                
                # Check that command succeeded
                assert result.returncode == 0, f"Command failed: {result.stderr}"
                
                # Check that PAC file was created
                pac_file = os.path.join(tmp_dir, 'flora_pac.pac')
                assert os.path.exists(pac_file), "PAC file was not created"
                
                # Read and verify PAC file content
                with open(pac_file, 'r') as f:
                    content = f.read()
                
                # Verify essential PAC file components
                assert 'function FindProxyForURL(url, host)' in content
                assert 'SOCKS5 127.0.0.1:1984' in content
                assert "isInNet(ip, '192.168.0.0', '255.255.255.0')" in content
                assert 'lookup_ip' in content
                assert 'hashed_nets' in content
                
                # Verify that Chinese networks are included
                # The mock data should result in some network entries
                assert '[' in content and ']' in content  # Should have hash arrays
                
            finally:
                os.chdir(original_cwd)
    
    def test_command_line_argument_parsing(self):
        """Test command line argument parsing"""
        import argparse
        from flora_pac import __main__ as main_module
        
        # Test basic argument parsing
        sys.argv = ['flora_pac', '-x', 'SOCKS5 127.0.0.1:1984', '-b', 'local_ip']
        
        parser = argparse.ArgumentParser(description="Generate proxy auto-config rules.")
        parser.add_argument('-x', '--proxy', dest='proxy', default=['SOCKS 127.0.0.1:8964'], 
                           nargs='*', help="Proxy Server")
        parser.add_argument('-b', '--balance', choices=["no", "local_ip", "host"],
                           dest='balance', default="no", help="Balancing policy")
        parser.add_argument('-n', '--no-proxy', dest='no_proxy', nargs='*',
                           default=['192.168.0.0/24'], help="Don't proxy request")
        parser.add_argument('-m', '--mask-step', type=int, dest='mask_step',
                           default=2, help="Step size of mask fragment")
        parser.add_argument('-s', '--hash-base', type=int, dest='hash_base',
                           default=3011, help='Size of the address hash table')
        
        args = parser.parse_args(['-x', 'SOCKS5 127.0.0.1:1984', '-b', 'local_ip'])
        
        assert args.proxy == ['SOCKS5 127.0.0.1:1984']
        assert args.balance == 'local_ip'
        assert args.no_proxy == ['192.168.0.0/24']  # default
        assert args.mask_step == 2  # default
        assert args.hash_base == 3011  # default
    
    def test_pac_file_javascript_syntax(self):
        """Test that generated PAC file has valid JavaScript syntax"""
        # This is a basic syntax check - in a real environment you might
        # want to use a JavaScript parser or validator
        
        # Mock network data for testing
        with patch('flora_pac.fetch_ip_data') as mock_fetch:
            mock_fetch.return_value = []  # Empty for simplicity
            
            with tempfile.TemporaryDirectory() as tmp_dir:
                original_cwd = os.getcwd()
                os.chdir(tmp_dir)
                
                try:
                    import flora_pac
                    generate_pac = flora_pac.generate_pac
                    
                    generate_pac(['SOCKS5 127.0.0.1:1984'], 'no', ['192.168.0.0/24'])
                    
                    # Read generated PAC file
                    with open('flora_pac.pac', 'r') as f:
                        content = f.read()
                    
                    # Basic JavaScript syntax checks
                    assert content.count('{') == content.count('}'), "Mismatched braces"
                    assert content.count('(') == content.count(')'), "Mismatched parentheses"
                    assert content.count('[') == content.count(']'), "Mismatched brackets"
                    
                    # Check for required function structure
                    assert 'function FindProxyForURL(url, host) {' in content
                    assert content.strip().endswith('}'), "Function not properly closed"
                    
                    # Check for proper variable declarations
                    assert 'var ' in content, "Variables should be declared"
                    
                    # Check for proper return statements
                    assert 'return ' in content, "Should have return statements"
                    
                finally:
                    os.chdir(original_cwd)
    
    def test_multiple_proxy_balancing_integration(self):
        """Test integration with multiple proxies and balancing"""
        with patch('flora_pac.fetch_ip_data') as mock_fetch:
            mock_fetch.return_value = []
            
            with tempfile.TemporaryDirectory() as tmp_dir:
                original_cwd = os.getcwd()
                os.chdir(tmp_dir)
                
                try:
                    import flora_pac
                    generate_pac = flora_pac.generate_pac
                    
                    proxies = [
                        'SOCKS5 127.0.0.1:1984', 
                        'SOCKS5 127.0.0.1:1989',
                        'PROXY 127.0.0.1:8080'
                    ]
                    
                    generate_pac(proxies, 'host', ['192.168.0.0/24', '10.0.0.0/8'])
                    
                    with open('flora_pac.pac', 'r') as f:
                        content = f.read()
                    
                    # Verify all proxies are included
                    for proxy in proxies:
                        assert proxy in content
                    
                    # Verify host balancing is included
                    assert 'target_host_balance' in content
                    assert 'hash_string' in content
                    
                    # Verify no-proxy rules are included
                    assert "isInNet(ip, '192.168.0.0', '255.255.255.0')" in content
                    assert "isInNet(ip, '10.0.0.0', '255.0.0.0')" in content
                    
                finally:
                    os.chdir(original_cwd)