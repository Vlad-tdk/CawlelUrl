from requests_html import HTMLSession
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import colorama
import argparse
import sys

# initialize colorama module
colorama.init()

GREEN = colorama.Fore.GREEN
GRAY = colorama.Fore.LIGHTBLACK_EX
RESET = colorama.Fore.RESET
YELLOW = colorama.Fore.YELLOW

# initialize sets of links (unique links)
internal_links = set()
external_links = set()

visited_links = 0


def is_valid_url(url):
    """
    Checks whether `url` is a valid URL.
    """
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)


def extract_all_links_from_website(url):
    """
    Returns all URLs found on `url` belonging to the same website.
    """
    # all URLs of `url`
    links = set()
    # domain name of the URL without the protocol
    domain_name = urlparse(url).netloc
    # initialize an HTTP session
    session = HTMLSession()
    try:
        # make HTTP request & retrieve response
        response = session.get(url)
        # execute JavaScript
        try:
            response.html.render()
        except:
            pass
        soup = BeautifulSoup(response.html.html, "html.parser")
        for a_tag in soup.find_all("a"):
            href = a_tag.get("href")
            if href == "" or href is None:
                # empty href tag
                continue
            # join the URL if it's relative (not absolute link)
            href = urljoin(url, href)
            parsed_href = urlparse(href)
            # remove URL GET parameters, URL fragments, etc.
            href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
            if not is_valid_url(href):
                # not a valid URL
                continue
            if href in internal_links:
                # already in the set
                continue
            if domain_name not in href:
                # external link
                if href not in external_links:
                    print(f"{GRAY}[!] External link: {href}{RESET}")
                    external_links.add(href)
                continue
            print(f"{GREEN}[*] Internal link: {href}{RESET}")
            links.add(href)
            internal_links.add(href)
    except Exception as e:
        print(f"{YELLOW}[!] Error extracting links from {url}: {e}{RESET}")


def crawl_web_page(url, max_urls=30):
    """
    Crawls a web page and extracts all links.
    You'll find all links in global variables `external_links` and `internal_links`.
    params:
        max_urls (int): number of max urls to crawl, default is 30.
    """
    global visited_links
    visited_links += 1
    print(f"{YELLOW}[*] Crawling: {url}{RESET}")
    extract_all_links_from_website(url)
    if visited_links > max_urls:
        return
    links = internal_links.copy()  # copy the set of links to avoid changing it during crawling
    for link in links:
        crawl_web_page(link, max_urls)


def main(url, max_urls=30):
    crawl_web_page(url, max_urls)
    print("[+] Total Internal links:", len(internal_links))
    print("[+] Total External links:", len(external_links))
    print("[+] Total URLs:", len(external_links) + len(internal_links))
    print("[+] Total crawled URLs:", max_urls)

    domain_name = urlparse(url).netloc

    # save the internal links to a file
    try:
        with open(f"{domain_name}_internal_links.txt", "w") as f:
            for internal_link in internal_links:
                print(internal_link.strip(), file=f)
    except Exception as e:
        print(f"{YELLOW}[!] Error saving internal links: {e}{RESET}")

    # save the external links to a file
    try:
        with open(f"{domain_name}_external_links.txt", "w") as f:
            for external_link in external_links:
                print(external_link.strip(), file=f)
    except Exception as e:
        print(f"{YELLOW}[!] Error saving external links: {e}{RESET}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Link Extractor Tool with Python")
    parser.add_argument("file", help="Path to the file containing the list of websites.")
    parser.add_argument("-m", "--max-urls", help="Number of max URLs to crawl, default is 30.", default=30, type=int)
    
    args = parser.parse_args()
    file_path = args.file
    max_urls = args.max_urls

    try:
        with open(file_path, "r") as file:
            for line in file:
                site_url = line.strip()
                print(f"{YELLOW}[*] Processing website: {site_url}{RESET}")
                internal_links.clear()
                external_links.clear()
                visited_links = 0
                main(site_url, max_urls)
                print()  # Add a blank line between processed websites
    except FileNotFoundError:
        print(f"{YELLOW}[!] File with the list of websites not found: {file_path}{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"{YELLOW}[!] Error reading file: {e}{RESET}")
        sys.exit(1)
