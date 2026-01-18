#!/usr/bin/env python3
"""
The "Alive" URL Health Checker

A high-speed, concurrent tool to ruthlessly determine the reachability
and status of your critical URLs. Fast, fierce, and final.
"""

import argparse
import json
import sys
import time
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# UPDATED DEPENDENCY: Using 'ddgs'
try:
    from ddgs import DDGS
except ImportError:
    print("Error: ddgs library not found. Please install it (e.g., pip install ddgs).", file=sys.stderr)
    sys.exit(1)


# Utility function for clean string truncation
def safe_truncate(text, max_len=60, suffix='...'):
    """Truncates a string safely for clean terminal display."""
    if len(text) > max_len:
        return text[:max_len - len(suffix)] + suffix
    return text

# ---------- core checker ------------------------------------------------------
def is_valid_url(url: str) -> bool:
    try:
        # Check if scheme and netloc are present
        return all(urlparse(url)[0:2])
    except Exception:
        return False


def check_url(url: str, timeout: int = 10, retries: int = 3):
    """
    Performs a check using HEAD (for efficiency) and falls back to GET if HEAD fails.
    
    Returns: (success:bool, status_code:int|None, message:str, elapsed_ms:int|None)
    """
    if not is_valid_url(url):
        return False, None, "Invalid URL format", None

    # Default to https if no scheme is provided for a more robust check
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    retry = Retry(
        total=retries,
        backoff_factor=1,
        # 429: Too Many Requests; 5xx: Server errors
        status_forcelist=[429, 500, 502, 503, 504],
        # Allow both HEAD and GET for fallback logic
        allowed_methods=["HEAD", "GET"], 
    )
    sess = requests.Session()
    # Add a common User-Agent to avoid blocks from strict CDNs/WAFs
    sess.headers.update({
        'User-Agent': 'Mozilla/5.0 (compatible; Alive-Checker/1.0; +https://github.com/your-project/alive)'
    })
    
    sess.mount("http://", HTTPAdapter(max_retries=retry))
    sess.mount("https://", HTTPAdapter(max_retries=retry))

    try:
        t0 = time.perf_counter()
        
        # 1. Try HEAD first for efficiency (no body content downloaded)
        resp = sess.request("HEAD", url, timeout=timeout, allow_redirects=True)
        
        # 2. Fallback to GET if HEAD method is not allowed (HTTP 405)
        if resp.status_code == 405:
            # We must use GET now, and the Retries will apply to this GET request
            resp = sess.request("GET", url, timeout=timeout, allow_redirects=True)

        elapsed = int((time.perf_counter() - t0) * 1000)

        # Handle successful range
        if 200 <= resp.status_code < 300:
            return True, resp.status_code, "OK", elapsed
        # Handle redirects
        if 300 <= resp.status_code < 400:
            return True, resp.status_code, f"Redirected to {resp.url}", elapsed
        
        # Handle client/server errors
        return False, resp.status_code, f"HTTP {resp.status_code}", elapsed

    except requests.exceptions.Timeout:
        return False, None, "Request timed out", None
    except requests.exceptions.ConnectionError:
        # This catches DNS failures, refused connections, etc.
        return False, None, "Connection failed", None
    except requests.exceptions.TooManyRedirects:
        return False, None, "Too many redirects", None
    except requests.exceptions.RequestException as e:
        # General requests error (e.g., SSL error)
        return False, None, f"Request error: {e}", None
    except Exception as e:
        # Catch any unexpected Python errors
        return False, None, f"Unexpected error: {e}", None


def search_for_404_alter(url: str) -> list[dict]:
    """
    Performs two specific DuckDuckGo searches to find alternatives for a 404 URL.
    Returns a list of up to 3 combined, unique best results: 
    [{"title": "...", "url": "..."}, ...]
    """
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    # Get non-empty path segments (e.g., ['en-us', 'azure', 'sentinel', 'playbooks'])
    path_segments = [p for p in parsed_url.path.split('/') if p] 

    if len(path_segments) < 1:
        # Not enough info for a path-based search (e.g., only a domain: https://example.com)
        return []

    # --- Query 1: site: Search (Prioritize Domain/Path) ---
    path_and_keyword_terms = ' '.join(path_segments).replace('-', ' ').replace('_', ' ')
    query1 = f"site:{domain} {path_and_keyword_terms}"
    
    # --- Query 2: Plain Text Search (Broader Context) ---
    all_path_keywords = ' '.join(p.replace('-', ' ').replace('_', ' ') for p in path_segments)
    query2 = f"{domain} {all_path_keywords}"

    results = []
    seen_urls = set()

    try:
        ddgs = DDGS()

        # Run Query 1
        for r in ddgs.text(query1, max_results=3, safesearch='moderate'):
            if r.get('href') and r['href'] not in seen_urls:
                results.append({"title": r.get('title', 'No Title'), "url": r['href']})
                seen_urls.add(r['href'])
        
        # Run Query 2 (only if we don't have 3 results already)
        if len(results) < 3:
             for r in ddgs.text(query2, max_results=3, safesearch='moderate'):
                if r.get('href') and r['href'] not in seen_urls and len(results) < 3:
                    results.append({"title": r.get('title', 'No Title'), "url": r['href']})
                    seen_urls.add(r['href'])

    except Exception as e:
        # Catch any search related exceptions
        if sys.stderr.isatty():
             print(f"\n[!] Search Error for {url}: {e}", file=sys.stderr)
        return []
        
    return results


# ---------- output formatters -------------------------------------------------
def term_format(url, success, status_code, message, elapsed_ms, verbose, use_color, alternatives=None):
    """
    Formats a single check result for terminal or file output with improved style.
    """
    
    # Define colors and symbols for better terminal output
    GREEN = "\033[92m"
    RED = "\033[91m"
    GRAY = "\033[90m"
    BOLD = "\033[1m"
    RESET = "\033[0m"
    
    # Use Unicode symbols for clarity
    status_sym = "✅" if success else "❌"
    
    # Determine primary color based on success
    status_col = GREEN if success else RED
    
    # --- Primary Line ---
    # Status Symbol + URL + Message
    line_parts = []
    
    # Apply color/bold to the status symbol only
    if use_color:
        line_parts.append(f"{status_col}{BOLD}{status_sym}{RESET}")
    else:
        line_parts.append(status_sym)
        
    line_parts.append(f" {url} - {message}")
    
    final_line = "".join(line_parts)
    
    # --- Verbose Line (Appears right after the primary line, indented) ---
    if verbose:
        verbose_parts = []
        if status_code is not None:
            verbose_parts.append(f"STATUS: {status_code}")
        if elapsed_ms is not None:
            # Use GRAY for verbose details
            verbose_parts.append(f"TIME: {elapsed_ms}ms")
            
        if verbose_parts:
            # Indent the verbose line
            final_line += "\n" + (GRAY if use_color else "") + "    " + " | ".join(verbose_parts) + (RESET if use_color else "")
    
    # --- Alternatives Section (Only for 404 errors with suggestions) ---
    alt_lines = []
    if status_code == 404 and alternatives:
        alt_lines.append("\n" + (BOLD if use_color else "") + "    🔍 Alternatives Found:" + (RESET if use_color else ""))
        for i, alt in enumerate(alternatives):
            # Safe truncation for titles and URLs
            title = safe_truncate(alt['title'], max_len=75)
            url_short = safe_truncate(alt['url'], max_len=75)
            
            # Indent the list items
            # Use GRAY for the URL part for visual separation
            alt_url_color = GRAY if use_color else ""
            alt_reset_color = RESET if use_color else ""

            alt_lines.append(f"        {i+1}. {title} ({alt_url_color}{url_short}{alt_reset_color})")

    # Append alternatives lines 
    if alt_lines:
        final_line += "\n" + "\n".join(alt_lines)
        
    return final_line


# ---------- main --------------------------------------------------------------
def main():
    banner = """
 ▗▄▖ ▗▖   ▗▄▄▄▖▗▖  ▗▖▗▄▄▄▖
▐▌ ▐▌▐▌     █  ▐▌  ▐▌▐▌   
▐▛▀▜▌▐▌     █  ▐▌  ▐▌▐▛▀▀▘
▐▌ ▐▌▐▙▄▄▖▗▄█▄▖ ▝▚▞▘ ▐▙▄▄▖
        
        ~CODE 200  
         ~AZAZI~                                                                                                                              
"""
    # --- ARGPARSE SETUP ---
    parser = argparse.ArgumentParser(
        prog="alive",
        description="ALIVE: The URL health checker.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    
    # The crucial positional argument line
    parser.add_argument("urls", nargs="*") 
    parser.add_argument("-f", "--file", help="Text file with one URL per line.")
    parser.add_argument("-j", "--json", action="store_true", help="Expect JSON input (list of strings). Output is ONLY JSON to stdout.")
    parser.add_argument("-o", "--output", help="Write final results (plain text) to this file.")
    parser.add_argument("-t", "--timeout", type=int, default=10, help="Timeout in seconds for each request (default: 10).")
    parser.add_argument("-r", "--retries", type=int, default=3, help="Number of automatic retries on server errors (429, 5xx) (default: 3).")
    parser.add_argument("-w", "--max-workers", type=int, default=20, help="Maximum number of concurrent checks (default: 20).")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show response status code and time for each check.")
    # NEW ARGUMENT: -s / --suggest
    parser.add_argument("-s", "--suggest", action="store_true", help="Search for alternative URLs using DDGS on 404 errors.")
    args = parser.parse_args()

    # --- ASCII ART BANNER ---
    is_terminal = sys.stdout.isatty()
    # Only print banner if not asking for help and not in JSON mode
    if not (args.json or '-h' in sys.argv or '--help' in sys.argv):
        print(banner)
    # --------------------------

    # collect URLs
    urls = []
    if args.urls:
        urls.extend(args.urls)
    if args.file:
        try:
            with open(args.file) as fh:
                urls.extend(line.strip() for line in fh if line.strip())
        except FileNotFoundError:
            print(f"File not found: {args.file}", file=sys.stderr)
            sys.exit(1)
            
    if args.json:
        json_data = None
        if not args.urls and not args.file and not sys.stdin.isatty():
             try:
                json_data = json.load(sys.stdin)
             except json.JSONDecodeError as e:
                print(f"JSON input error from stdin: {e}", file=sys.stderr)
                sys.exit(1)
        elif args.urls and len(args.urls) == 1 and not args.file:
            try:
                with open(args.urls[0]) as fh:
                    json_data = json.load(fh)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"JSON input file error: {e}", file=sys.stderr)
                sys.exit(1)
            args.urls = []
        else:
            if args.json:
                 print("ERROR: In JSON mode (-j), use a single positional file path argument or pipe JSON data via stdin.", file=sys.stderr)
                 sys.exit(1)
            
        if json_data:
            if isinstance(json_data, list):
                urls.extend(json_data)
            else:
                print("JSON input must be a list of URLs.", file=sys.stderr)
                sys.exit(1)


    if not urls:
        parser.print_help(sys.stderr)
        sys.exit(1)
        
    # --- CONCURRENT CHECK EXECUTION ---
    
    # Do not print live action if in JSON mode but stdout is being piped
    show_live_status = not args.json and is_terminal
    
    if show_live_status:
        print(f"Checking {len(urls)} URLs with {args.max_workers} concurrent workers.")
        print("--- LIVE RESULTS ---")
    
    ordered_results = [None] * len(urls)
    
    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        future_to_index = {
            executor.submit(check_url, u, args.timeout, args.retries): i
            for i, u in enumerate(urls)
        }
        
        completed_count = 0 # New counter for live progress

        # Process results as they are completed
        for future in as_completed(future_to_index):
            index = future_to_index[future]
            url = urls[index]
            
            completed_count += 1
            
            # JSON Live Action: Progress counter printed to STDERR
            if args.json and sys.stderr.isatty(): # Only show progress if stderr is a console
                total = len(future_to_index)
                print(f"\rProgress: {completed_count}/{total} checked...", end="", file=sys.stderr, flush=True)


            try:
                ok, code, msg, ms = future.result()
                
                alternatives = []
                # UPDATED LOGIC: Trigger search only on 404 AND if --suggest (-s) is enabled
                if args.suggest and not ok and code == 404:
                    alternatives = search_for_404_alter(url)
                        
                # The result dictionary now includes the 'alternatives' key
                result = {"url": url, "success": ok, "status_code": code, "message": msg, "response_time_ms": ms, "alternatives": alternatives}
                
                # LIVE ACTION: Print result immediately to terminal 
                if show_live_status:
                    # Pass alternatives to term_format
                    print(term_format(url, ok, code, msg, ms, args.verbose, use_color=True, alternatives=alternatives))
                
                ordered_results[index] = result
                
            except Exception as exc:
                result = {"url": url, "success": False, "status_code": None, "message": f"Execution error: {exc}", "response_time_ms": None, "alternatives": []}
                
                if show_live_status:
                    # Pass alternatives=None for the error case
                    print(term_format(url, False, None, f"Execution error: {exc}", None, args.verbose, use_color=True, alternatives=None))

                ordered_results[index] = result

    # Clear the progress line from STDERR after loop finishes
    if args.json and completed_count > 0 and sys.stderr.isatty():
        print("\rProgress: Complete. Formatting JSON...  ", file=sys.stderr) # Spaces to clear the previous line
    
    # Flatten the list of results (now in original order)
    results = [r for r in ordered_results if r is not None]
    
    # --- OUTPUT ---
    
    if args.json:
        # JSON mode -> ONLY json to stdout (the 'alternatives' key is already in results)
        print(json.dumps(results, indent=2))
    else:
        # TERMINAL Summary Output (only if we printed the live results)
        ok_cnt = sum(r["success"] for r in results)
        
        if is_terminal:
            print("\n" + "=" * 50)
            print("--- FINAL SUMMARY ---")
            print(f"Total checked: {len(results)}")
            print(f"Working URLs:  {ok_cnt}")
            print(f"Failed URLs:   {len(results) - ok_cnt}")
        
        # Output to file if -o is specified (uses no_color for file)
        if args.output:
            try:
                with open(args.output, 'w') as out_fh:
                    out_fh.write("--- Alive URL Checker Report ---\n")
                    out_fh.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    out_fh.write(f"Summary: {ok_cnt}/{len(results)} URLs are working\n")
                    out_fh.write("-" * 35 + "\n")
                    
                    for r in results:
                        # Explicitly use use_color=False for file output and pass alternatives
                        line = term_format(
                            r["url"], r["success"], r["status_code"], r["message"], 
                            r["response_time_ms"], args.verbose, use_color=False,
                            alternatives=r.get("alternatives")
                        )
                        out_fh.write(line + "\n")
                if is_terminal:
                    print(f"Results successfully written to: {args.output}")
            except Exception as e:
                print(f"Error writing to output file {args.output}: {e}", file=sys.stderr)
                
    sys.exit(0 if all(r["success"] for r in results) else 1)


if __name__ == "__main__":
    try:
        print(r"""
                                                                                
 ░▒▓██████▓▒░░▒▓█▓▒░      ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓████████▓▒░ 
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░        
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒▒▓█▓▒░░▒▓█▓▒░        
░▒▓████████▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒▒▓█▓▒░░▒▓██████▓▒░   
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░ ░▒▓█▓▓█▓▒░ ░▒▓█▓▒░        
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░ ░▒▓█▓▓█▓▒░ ░▒▓█▓▒░        
░▒▓█▓▒░░▒▓█▓▒░▒▓████████▓▒░▒▓█▓▒░  ░▒▓██▓▒░  ░▒▓████████▓▒░ 
                                                                                                       
           __          ___               _ 
          / /  __ __  / _ |___ ___ ____ (_)
         / _ \/ // / / __ /_ // _ `/_ // / 
        /_.__/\_, / /_/ |_/__/\_,_//__/_/  
             /___/                         

    """)
        main()
    except KeyboardInterrupt:
        sys.exit(130)
