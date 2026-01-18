# 🚀 AliveV2: The Concurrent Recon & Research Validator

**AliveV2** is a high-speed, OSINT-enhanced URL health checker built for security professionals and academic researchers. It streamlines the process of validating large sets of assets while providing intelligent alternatives for broken resources through DuckDuckGo integration.

---

## 🛡️ Cybersecurity & Pentesting Use Cases
Developed as part of my **Master’s in Cybersecurity**, this tool is designed to bridge the gap between initial reconnaissance and vulnerability discovery:

* **Attack Surface Mapping**: Rapidly filter live web targets after subdomain enumeration or **Nmap** scans.
* **Broken Link Hijacking (BLH)**: Identify `404 Not Found` pages on target domains that are vulnerable to social media or resource hijacking.
* **C2 & Malware Analysis**: Safely check the status of suspected Command and Control (C2) infrastructure or malicious URLs identified in threat feeds.
* **OSINT Discovery**: Use the `--suggest` flag to find moved assets or legacy portals via DuckDuckGo integration.
* **WAF & CDN Detection**: Configured with custom User-Agents and retry logic to handle rate-limiting and Web Application Firewalls.

---

## 🎓 Academic Research & Integrity
Beyond security, I utilize AliveV2 as a "Reference Auditor" to maintain the quality and academic rigor of technical reports and my Master's thesis:

* **Combatting Link Rot**: Automatically verifies that every citation in a research paper is still live and accessible.
* **Reference Audit**: Batch-checks bibliography URLs to ensure professional reporting standards.
* **Automated Verification**: Replaces the manual task of clicking through dozens of references, ensuring 100% data integrity in technical documentation.

---

## ✨ Key Features
- **High Concurrency**: Uses `ThreadPoolExecutor` for rapid multi-threaded scanning of large URL lists.
- **Intelligent Fallback**: Attempts `HEAD` requests for speed, falling back to `GET` for strict server configurations.
- **OSINT Suggestions**: Automatic DuckDuckGo search for `404` errors to find alternative content or archived locations.
- **DeepRead Ready**: Generates structured JSON support for integration with other forensics and automation scripts.
- **Fierce Error Handling**: Built-in exponential backoff to handle HTTP 429 (Rate Limiting) and server instability.

---

## 🚀 Quick Start

### 1. Installation
```bash
# Clone the repository
git clone [https://github.com/YourUsername/AliveV2.git](https://github.com/YourUsername/AliveV2.git)
cd AliveV2

# Install dependencies
pip install -r requirements.txt

```

### 2. Basic Usage

Check a few URLs directly with verbose output:

```bash
python aliveV2.py [https://example.com](https://example.com) [https://google.com](https://google.com) -v

```

### 3. Research & Security Auditing

Check a file of URLs (e.g., a bibliography or a list of subdomains) with OSINT suggestions:

```bash
python aliveV2.py -f targets.txt --suggest --output report.txt

```

### 4. JSON Pipeline

Pipe input from other tools and output clean JSON for further analysis:

```bash
cat targets.json | python aliveV2.py -j > results.json

```

---

## 🛠️ Requirements

* Python 3.7+
* `requests`
* `urllib3`
* `ddgs` (DuckDuckGo Search)

---

## ⚖️ License

This project is licensed under the MIT License - see the LICENSE file for details.

**Author**: Azazi

**Focus**: Cyber Threat Intelligence | Master's Student in Cybersecurity

```
