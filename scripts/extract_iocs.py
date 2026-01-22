"""
IOC (Indicator of Compromise) Extraction Script

Purpose:
    Extract security indicators from unstructured text:
    - IP addresses (IPv4)
    - Domain names
    - URLs
    - File hashes (MD5, SHA1, SHA256)
    
    Common in SOAR workflows when:
    - Processing email bodies
    - Parsing alert descriptions
    - Extracting indicators from threat intelligence feeds

Author: Clinton Howard
Date: January 2026
"""

import re
from typing import Dict, List, Set
from collections import defaultdict


class IOCExtractor:
    """
    Extract and validate Indicators of Compromise from text.
    
    Handles defanged indicators (hxxp://, domain[.]com) commonly used
    in security communications to prevent accidental clicks.
    """
    
    def __init__(self):
        """Initialize regex patterns for different IOC types."""
        
        # IP Address Pattern
        # Matches: 192.168.1.1, 10.0.0.5
        # Breakdown:
        #   \b          = word boundary (start of IP)
        #   \d{1,3}     = 1-3 digits
        #   \.          = literal dot
        #   (repeat 3 times for 4 octets)
        #   \b          = word boundary (end of IP)
        self.ip_pattern = re.compile(
            r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        )
        
        # Domain Pattern
        # Matches: example.com, sub.domain.co.uk, malicious-site.net
        # Also handles defanged: example[.]com, example\.com
        # Breakdown:
        #   \b                          = word boundary
        #   (?:[a-zA-Z0-9-]+            = subdomain/domain part (letters, numbers, hyphens)
        #   (?:\[?\.\]?|\\.)            = dot, bracket-dot, or escaped-dot
        #   )+                          = repeat for subdomains
        #   [a-zA-Z]{2,}                = TLD (at least 2 letters: .com, .co.uk)
        #   \b                          = word boundary
        self.domain_pattern = re.compile(
            r'\b(?:[a-zA-Z0-9-]+(?:\[?\.\]?|\\.)){1,}[a-zA-Z]{2,}\b'
        )
        
        # URL Pattern
        # Matches: http://example.com, hxxps://defanged[.]site
        # Breakdown:
        #   \b                          = word boundary
        #   h[tx]{2}ps?                 = http/https or hxxp/hxxps (defanged)
        #   ://                         = colon-slash-slash
        #   [^\s]+                      = any non-whitespace (rest of URL)
        self.url_pattern = re.compile(
            r'\bh[tx]{2}ps?://[^\s]+'
        )
        
        # MD5 Hash Pattern (32 hex characters)
        # Matches: d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2
        # Breakdown:
        #   \b          = word boundary
        #   [a-fA-F0-9] = hexadecimal characters
        #   {32}        = exactly 32 characters
        #   \b          = word boundary
        self.md5_pattern = re.compile(
            r'\b[a-fA-F0-9]{32}\b'
        )
        
        # SHA1 Hash Pattern (40 hex characters)
        self.sha1_pattern = re.compile(
            r'\b[a-fA-F0-9]{40}\b'
        )
        
        # SHA256 Hash Pattern (64 hex characters)
        self.sha256_pattern = re.compile(
            r'\b[a-fA-F0-9]{64}\b'
        )
    
    
    def refang(self, text: str) -> str:
        """
        Convert defanged indicators back to normal format.
        
        Defanging is used in security reports to prevent accidental clicks:
        - hxxp://site.com -> http://site.com
        - domain[.]com -> domain.com
        - domain\.com -> domain.com
        
        Args:
            text: Text potentially containing defanged indicators
        
        Returns:
            Text with indicators refanged (restored to normal)
        """
        # Replace hxxp/hxxps with http/https
        text = text.replace('hxxp://', 'http://')
        text = text.replace('hxxps://', 'https://')
        
        # Replace [.] with .
        text = text.replace('[.]', '.')
        
        # Replace \. with . (but keep actual regex escapes)
        # Only replace if not preceded by backslash (avoid breaking actual escapes)
        text = re.sub(r'(?<!\\)\\\.', '.', text)
        
        return text
    
    
    def is_valid_ip(self, ip: str) -> bool:
        """
        Validate if extracted IP address is actually valid.
        
        Filters out:
        - Version numbers (1.2.3.4 could be v1.2.3.4)
        - Invalid octets (999.999.999.999)
        - Dates that look like IPs (12.25.2024 = December 25, 2024)
        
        Args:
            ip: String that matched IP pattern
        
        Returns:
            True if valid IPv4 address
        """
        octets = ip.split('.')
        
        # Must have exactly 4 octets
        if len(octets) != 4:
            return False
        
        # Each octet must be 0-255
        try:
            for octet in octets:
                num = int(octet)
                if num < 0 or num > 255:
                    return False
        except ValueError:
            return False
        
        # Filter out common false positives
        # Version numbers often start with 1. or 2.
        if octets[0] in ['1', '2'] and all(int(o) < 10 for o in octets[1:]):
            return False
        
        return True
    
    
    def is_valid_domain(self, domain: str) -> bool:
        """
        Basic domain validation.
        
        Filters out:
        - Too short (single letter TLDs don't exist anymore)
        - No TLD (just "localhost" or "hostname")
        - Obvious non-domains (file.txt, image.jpg)
        
        Args:
            domain: String that matched domain pattern
        
        Returns:
            True if likely a real domain
        """
        # Must contain at least one dot
        if '.' not in domain:
            return False
        
        # Get TLD (last part after final dot)
        tld = domain.split('.')[-1].lower()
        
        # Filter out file extensions
        file_extensions = ['txt', 'log', 'jpg', 'png', 'pdf', 'doc', 'docx', 'xlsx', 'zip']
        if tld in file_extensions:
            return False
        
        # TLD must be at least 2 characters
        if len(tld) < 2:
            return False
        
        return True
    
    
    def extract_ips(self, text: str) -> List[str]:
        """
        Extract all valid IP addresses from text.
        
        Args:
            text: Input text to search
        
        Returns:
            List of unique valid IP addresses
        """
        # Find all potential IPs
        potential_ips = self.ip_pattern.findall(text)
        
        # Validate and deduplicate
        valid_ips = set()
        for ip in potential_ips:
            if self.is_valid_ip(ip):
                valid_ips.add(ip)
        
        return sorted(list(valid_ips))
    
    
    def extract_domains(self, text: str) -> List[str]:
        """
        Extract all valid domain names from text.
        
        Args:
            text: Input text to search
        
        Returns:
            List of unique valid domains
        """
        # Refang defanged indicators first
        text = self.refang(text)
        
        # Find all potential domains
        potential_domains = self.domain_pattern.findall(text)
        
        # Validate and deduplicate
        valid_domains = set()
        for domain in potential_domains:
            # Clean up any remaining defang artifacts
            domain = domain.replace('[.]', '.').replace('\\.', '.')
            
            if self.is_valid_domain(domain):
                valid_domains.add(domain.lower())
        
        return sorted(list(valid_domains))
    
    
    def extract_urls(self, text: str) -> List[str]:
        """
        Extract all URLs from text.
        
        Args:
            text: Input text to search
        
        Returns:
            List of unique URLs (refanged)
        """
        # Refang defanged URLs first
        text = self.refang(text)
        
        # Find all URLs
        urls = self.url_pattern.findall(text)
        
        # Deduplicate and return
        return sorted(list(set(urls)))
    
    
    def extract_hashes(self, text: str) -> Dict[str, List[str]]:
        """
        Extract file hashes (MD5, SHA1, SHA256) from text.
        
        Args:
            text: Input text to search
        
        Returns:
            Dictionary with hash types as keys, lists of hashes as values
        """
        hashes = {
            'md5': [],
            'sha1': [],
            'sha256': []
        }
        
        # Extract each hash type
        # Note: Check longer hashes first to avoid misidentifying SHA256 as two SHA1s
        hashes['sha256'] = sorted(list(set(self.sha256_pattern.findall(text))))
        hashes['sha1'] = sorted(list(set(self.sha1_pattern.findall(text))))
        hashes['md5'] = sorted(list(set(self.md5_pattern.findall(text))))
        
        return hashes
    
    
    def extract_all(self, text: str) -> Dict[str, any]:
        """
        Extract all IOC types from text in one pass.
        
        Args:
            text: Input text to search
        
        Returns:
            Dictionary containing all extracted IOCs by type
        """
        return {
            'ips': self.extract_ips(text),
            'domains': self.extract_domains(text),
            'urls': self.extract_urls(text),
            'hashes': self.extract_hashes(text)
        }


def main():
    """
    Example usage with test data.
    """
    
    # Example alert text with various IOCs (including defanged)
    alert_text = """
    Suspicious activity detected from multiple sources.
    
    User accessed hxxp://malicious-site[.]com from IP 192.168.1.50.
    Downloaded file with MD5 hash: d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2
    
    Additional connections observed:
    - 10.0.0.5 (internal network)
    - suspicious-domain.evil
    - 172.16.254.1
    
    Email originated from attacker@phishing-site[.]net
    
    File details:
    SHA256: a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2
    
    Related URLs:
    - hxxps://c2-server[.]xyz/payload
    - http://legitimate-site.com/page
    
    False positives to ignore:
    - Version 1.2.3.4 (not an IP)
    - File report.pdf (not a domain)
    """
    
    print("=" * 60)
    print("IOC EXTRACTION DEMO")
    print("=" * 60)
    
    print("\nINPUT TEXT:")
    print("-" * 60)
    print(alert_text)
    
    # Extract IOCs
    extractor = IOCExtractor()
    iocs = extractor.extract_all(alert_text)
    
    print("\n" + "=" * 60)
    print("EXTRACTED IOCs")
    print("=" * 60)
    
    print("\nIP ADDRESSES:")
    for ip in iocs['ips']:
        print(f"  - {ip}")
    
    print("\nDOMAINS:")
    for domain in iocs['domains']:
        print(f"  - {domain}")
    
    print("\nURLs:")
    for url in iocs['urls']:
        print(f"  - {url}")
    
    print("\nFILE HASHES:")
    for hash_type, hashes in iocs['hashes'].items():
        if hashes:
            print(f"  {hash_type.upper()}:")
            for hash_val in hashes:
                print(f"    - {hash_val}")
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total IPs found:      {len(iocs['ips'])}")
    print(f"Total Domains found:  {len(iocs['domains'])}")
    print(f"Total URLs found:     {len(iocs['urls'])}")
    total_hashes = sum(len(h) for h in iocs['hashes'].values())
    print(f"Total Hashes found:   {total_hashes}")
    
    print("\nKey features demonstrated:")
    print("  - Defanged indicator handling (hxxp, [.])")
    print("  - IP validation (filtered version numbers)")
    print("  - Domain validation (filtered file extensions)")
    print("  - Automatic deduplication")
    print("  - Hash type identification")


if __name__ == "__main__":
    main()