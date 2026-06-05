## WAF Logic Asymmetry Exploitation Kit (v2.0)
- Author: QA210
- Date: June 06, 2026
- Version: 1.0 (Enhanced)
- Category: Protocol Security / Evasion Techniques

# Overview
This repository contains the advanced Proof of Concept (PoC) tools demonstrating Asymmetric Content-Encoding Deception (ACED) and Identity-Based Transparency Deception (IBTD).

Version 1.0 introduces significant improvements to evade basic fingerprinting and automate the validation of bypass attempts.

New Features in v1.0
Automated Scan Mode (Comparison Logic):
The tool now automatically sends a Baseline Request (standard traffic) followed by an Attack Request (ACED/IBTD vector).
It compares the Content-Length and Status Code of both responses to provide a heuristic analysis on whether the bypass was successful.
Random User-Agent Rotation:
To avoid WAF signatures that flag default script user-agents, the tool now selects a random, modern User-Agent from a predefined list for every request.
JSON Payload Support:
Added support for modern API endpoints that consume application/json.
Automatically wraps payloads in a JSON object structure.
Techniques

- ##  1. Asymmetric Content-Encoding Deception (ACED)
Exploits Fail-Open logic.

Header: Content-Encoding: gzip
Body: Raw plain-text data.
Logic: WAF fails to decompress -> Fails Open -> Backend reads raw data -> Payload executes.

- ## 2. Identity-Based Transparency Deception (IBTD)
Exploits performance optimization logic.

- Header: Content-Encoding: identity
- Body: Raw plain-text data.
- Logic: WAF marks as low-priority -> Skips Deep Inspection -> Payload executes transparently.

## Attack Workflow Diagrams

### 1. ACED Mechanism
![ACED Diagram](./diagram.svg)

### 2. IBTD Mechanism
![IBTD Diagram](./diagram%20(1).svg)



- Installation
- Ensure you have Python 3.x installed.
- Install dependencies:
  ` pip install requests
 `
 # Usage
Syntax:
`python3 poc.py -u [TARGET_URL] -m [MODE] -p [PAYLOAD] [OPTIONS]
`   
- # Arguments

| Argument         | Required | Description                                                  |
|------------------|----------|--------------------------------------------------------------|
| -u, --url        | Yes      | Target URL (e.g., https://target.com/api/login)              |
| -m, --mode       | Yes      | Attack mode: aced or ibtd                                    |
| -p, --payload    | No       | Payload to inject (Default: SQLi test string)                |
| --json           | No       | Send payload as JSON body (Content-Type: application/json)   |
| --json-key       | No       | Key name for JSON payload (Default: id)                      |
| --no-random-ua   | No       | Disable random User-Agent rotation                           |

 # Examples
 1. Basic Scan (Form-Data)
Tests ACED against a standard form endpoint.

`
python3 poc.py -u https://target.com/search -m aced -p "id=1' UNION SELECT 1,2,3--"
`

2. JSON API Scan (IBTD)
Tests IBTD against a JSON API endpoint. The script will automatically construct `{"username": "admin' OR 1=1--"}`.

`
python3 poc.py -u https://api.target.com/v1/auth -m ibtd -p "admin' OR 1=1--" --json --json-key "username"
`

Understanding the Output
The tool provides a comparison table:
```
============================================================
[ANALYSIS] Result for ACED
============================================================
Request Type         | Status    | Length (Bytes) 
------------------------------------------------------------
Baseline (Normal)   | 200       | 452            
Attack (Evasion)    | 200       | 452            
------------------------------------------------------------
[+] POTENTIAL BYPASS DETECTED!
    Reason: Response length matches baseline exactly.
```
- POTENTIAL BYPASS: The attack response length and status match the baseline. The WAF likely forwarded the request.
- LIKELY BLOCKED: The lengths differ significantly (often a 403 page is shorter than a 200 OK page).
# Mitigation & Defense
To protect against ACED and IBTD:

1.Fail-Closed Policy: Configure WAFs to block requests where the body content does not match the declared encoding header.

2.Strict DPI: Ensure identity encoding is not treated as a "skip inspection" trigger.

3.Backend Hardening: Disable implicit fallback on web servers (IIS, Tomcat) to reject malformed encoding attempts.
- Disclaimer
This tool is for educational purposes and authorized security testing only. Do not use it against systems you do not own or have explicit permission to test.

Security is a battle of logic, not just signatures.


