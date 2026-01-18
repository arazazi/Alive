# 🚀 AliveV2: The Concurrent Recon & Research Validator

**AliveV2** is a high-speed, OSINT-enhanced URL health checker built for security professionals and academic researchers. It streamlines the process of validating large sets of assets while providing intelligent alternatives for broken resources.

## 🛡️ Cybersecurity & Pentesting Use Cases

As a Master’s student in Cybersecurity, I developed this tool to bridge the gap between initial reconnaissance and vulnerability discovery:

* **Attack Surface Mapping**: Rapidly filter live web targets after subdomain enumeration or **Nmap** scans.
* **Broken Link Hijacking (BLH)**: Identify `404 Not Found` pages on target domains that are vulnerable to social media or resource hijacking.
* **C2 & Malware Analysis**: Safely check the status of suspected Command and Control (C2) infrastructure or malicious URLs.
* **OSINT Discovery**: Use the `--suggest` flag to find moved assets or legacy portals via DuckDuckGo integration.
* **Bypassing WAFs**: Configured with custom User-Agents and retry logic to handle rate-limiting and Web Application Firewalls.

## 🎓 Academic Research & Integrity

I utilize AliveV2 as a "Reference Auditor" to maintain the quality of my technical reports and Master's thesis:

* **Combatting Link Rot**: Automatically verifies that every citation in a research paper is still live and accessible.
* **Reference Audit**: Batch-checks bibliography URLs to ensure professional reporting standards.
* **Automated Verification**: Replaces the manual task of clicking through dozens of references, ensuring 100% data integrity.

## ✨ Key Features

* **High Concurrency**: Uses `ThreadPoolExecutor` for rapid multi-threaded scanning.
* **Intelligent Fallback**: Attempts `HEAD` requests for speed, falling back to `GET` for strict servers.
* **OSINT Suggestions**: Automatic DuckDuckGo search for `404` errors to find alternative content.
* **Pipeline Ready**: Full JSON support for integration with tools like **Metasploit** or custom Python scripts.

## 🚀 Quick Start

1. **Clone & Install**:
```bash
git clone https://github.com/YourUsername/AliveV2.git
pip install -r requirements.txt

```


2. **Scan for Research/Security**:
```bash
# Check a file of URLs with OSINT suggestions
python aliveV2.py -f targets.txt --suggest --verbose

```
