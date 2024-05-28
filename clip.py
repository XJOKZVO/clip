import argparse
import json
import os
import re
import sys
import requests
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# ASCII art
ascii_art = """
           ***                        
            ***      *                
             **     ***               
             **      *                
             **               ****    
   ****      **    ***       * ***  * 
  * ***  *   **     ***     *   ****  
 *   ****    **      **    **    **   
**           **      **    **    **   
**           **      **    **    **   
**           **      **    **    **   
**           **      **    **    **   
***     *    **      **    *******    
 *******     *** *   *** * ******     
  *****       ***     ***  **         
                           **         
                           **         
                            **        
"""

print(ascii_art)

# Global variables
headers = {}
visited_urls = set()

def parse_headers(raw_headers):
    if raw_headers:
        header_lines = raw_headers.split(";;")
        for line in header_lines:
            parts = line.split(":")
            if len(parts) == 2:
                header_key = parts[0].strip()
                header_value = parts[1].strip()
                if header_key.lower() == "user-agent":
                    headers["User-Agent"] = header_value
                else:
                    headers[header_key] = header_value

def extract_hostname(url):
    try:
        # Handle various URL formats including with or without protocol
        parsed_url = urlparse(url)
        if parsed_url.hostname:
            return parsed_url.hostname
        elif parsed_url.netloc:
            return parsed_url.netloc.split(":")[0]  # Handle cases with port numbers
        else:
            # Fallback to regular expression for handling more edge cases
            hostname = re.search(r"https?://(?:www\.)?([^/:]+)", url).group(1)
            return hostname
    except AttributeError:
        return None

def print_result(link, source_name, show_source, show_where, show_json, where_url):
    result = link
    if show_json:
        where = where_url if show_where else ""
        result = json.dumps({"Source": source_name, "URL": link, "Where": where})
    elif show_source:
        result = f"[{source_name}] {link}"
    if show_where and not show_json:
        result = f"[{where_url}] {result}"
    print(result)

def crawl_url(url, inside, depth, show_source, show_where, show_json):
    if not url or urlparse(url).scheme not in {'http', 'https'}:
        print(f"Ignoring invalid URL: {url}")
        return
        
    if url in visited_urls:
        return

    visited_urls.add(url)

    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        # Extract links from 'a' tags
        for tag in soup.find_all("a", href=True):
            link = tag["href"]
            if inside or link.startswith(url):
                print_result(link, "href", show_source, show_where, show_json, url)

        # Extract script sources
        for tag in soup.find_all("script", src=True):
            print_result(tag["src"], "script", show_source, show_where, show_json, url)

        # Extract form actions
        for tag in soup.find_all("form", action=True):
            print_result(tag["action"], "form", show_source, show_where, show_json, url)

        # Extract image sources
        for tag in soup.find_all("img", src=True):
            print_result(tag["src"], "img", show_source, show_where, show_json, url)

        # Extract CSS file sources
        for tag in soup.find_all("link", rel="stylesheet", href=True):
            print_result(tag["href"], "css", show_source, show_where, show_json, url)

        # Extract video sources
        for tag in soup.find_all("video", src=True):
            print_result(tag["src"], "video", show_source, show_where, show_json, url)

        # Extract audio sources
        for tag in soup.find_all("audio", src=True):
            print_result(tag["src"], "audio", show_source, show_where, show_json, url)

        # Extract iframe sources
        for tag in soup.find_all("iframe", src=True):
            print_result(tag["src"], "iframe", show_source, show_where, show_json, url)

        # Extract meta refresh redirects
        meta_refresh = soup.find("meta", attrs={"http-equiv": "refresh"})
        if meta_refresh and meta_refresh.get("content"):
            redirect_url = re.search(r'url=(.*?)["\']', meta_refresh["content"])
            if redirect_url:
                print_result(redirect_url.group(1), "meta_refresh", show_source, show_where, show_json, url)

        # Extract meta tags for social media
        for tag in soup.find_all("meta", property=re.compile(r'^og:|twitter:')):
            if tag.get("content"):
                print_result(tag["content"], "meta_social", show_source, show_where, show_json, url)

        # Extract additional resources linked in the page's source code
        for tag in soup.find_all(["link", "script", "img"], src=True):
            if tag.name == "link" and tag["rel"][0] == "icon":  # Favicon
                print_result(tag["href"], "favicon", show_source, show_where, show_json, url)
            elif tag.name == "script" and tag.get("type") == "application/json":  # JSON data
                print_result(tag["src"], "json", show_source, show_where, show_json, url)
            elif tag.name == "img" and tag.get("srcset"):  # Image sources in srcset attribute
                srcset = tag["srcset"].split(",")
                for source in srcset:
                    source_url = source.strip().split()[0]
                    print_result(source_url, "img_srcset", show_source, show_where, show_json, url)

        # Extract embedded JavaScript files
        for script in soup.find_all("script", src=False):
            if script.text.strip():  # Non-empty script tags
                print_result(script.text.strip(), "script_inline", show_source, show_where, show_json, url)

        # Extract embedded CSS styles
        for style in soup.find_all("style"):
            if style.text.strip():  # Non-empty style tags
                print_result(style.text.strip(), "css_inline", show_source, show_where, show_json, url)

        # Extract other types of links
        for tag in soup.find_all(["link", "script"], href=True):
            if tag.name == "link" and tag["rel"][0] != "icon":  # Other types of links in link tags
                print_result(tag["href"], "link", show_source, show_where, show_json, url)
            elif tag.name == "script" and not tag.get("src"):  # Embedded script tags without src attribute
                if tag.text.strip():  # Non-empty script tags
                    print_result(tag.text.strip(), "script_inline", show_source, show_where, show_json, url)

        if depth > 1:
            for tag in soup.find_all("a", href=True):
                link = tag["href"]
                if not inside and not link.startswith(url):
                    continue
                with ThreadPoolExecutor() as executor:
                    executor.submit(crawl_url, link, inside, depth - 1, show_source, show_where, show_json)

    except KeyboardInterrupt:
        print("Crawling interrupted by user.")
        sys.exit(0)

    except Exception as e:
        print(f"Error crawling {url}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Web crawler")
    parser.add_argument("urls", nargs="*", help="URLs to crawl", type=str)
    parser.add_argument("-i", "--inside", action="store_true", help="Only crawl inside path")
    parser.add_argument("-d", "--depth", type=int, default=2, help="Depth to crawl")
    parser.add_argument("-s", "--show-source", action="store_true", help="Show the source of URL")
    parser.add_argument("-w", "--show-where", action="store_true", help="Show where the URL is found")
    parser.add_argument("-j", "--show-json", action="store_true", help="Output as JSON")
    parser.add_argument("--headers", type=str, default="", help="Custom headers separated by two semi-colons")
    args = parser.parse_args()
    parse_headers(args.headers)

    if not args.urls:
        print("No URLs provided.")
        sys.exit(1)

    for url in args.urls:
        crawl_url(url, args.inside, args.depth, args.show_source, args.show_where, args.show_json)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Program terminated by user.")
