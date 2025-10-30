import os
import asyncio
import httpx
import requests
from types import SimpleNamespace
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import urllib3

# Login and URL from WIKI:
LOGIN_URL = "https://wiki.imt-soft.com/index.php/Special:UserLogin"  # Login URL
LOGIN_ACTION = "https://wiki.imt-soft.com/index.php?title=Special:UserLogin&action=submitlogin&type=login"
MAIN_PAGE = "https://wiki.imt-soft.com/index.php/Main_Page"
MAX_LINKS = 10000

# # Function to login to the current file link
#     async def login_session(self, username: str, password: str) -> bool:
#         try:
#             login_page_resp = await self.client.get(LOGIN_URL)
#             login_page_resp.raise_for_status()

#             soup = BeautifulSoup(login_page_resp.text, "html.parser")
#             login_token_element = soup.find("input", {"name": "wpLoginToken"})

#             if not login_token_element:
#                 print("[ERROR] Could not find login token on the page.")
#                 return False

#             login_token = login_token_element["value"]

#             payload = {
#                 "wpName": username,
#                 "wpPassword": password,
#                 "wpLoginToken": login_token,
#                 "wpLoginAttempt": "Log in",
#             }

#             login_resp = await self.client.post(LOGIN_ACTION, data=payload)
#             login_resp.raise_for_status()

#             if "wpName1" in login_resp.text or "Incorrect password" in login_resp.text:
#                 print("[ERROR] Login failed. Check credentials or form payload.")
#                 return False

#             print("[INFO] Login successful.")
#             return True

#         except httpx.RequestError as e:
#             print(f"[ERROR] An error occurred during login: {e}")
#             return False

# Login and URL from WIKI:
LOGIN_URL = "https://wiki.imt-soft.com/index.php/Special:UserLogin"  # Login URL
LOGIN_ACTION = "https://wiki.imt-soft.com/index.php?title=Special:UserLogin&action=submitlogin&type=login"
MAIN_PAGE = "https://wiki.imt-soft.com/index.php/Main_Page"
MAX_LINKS = 10000


class CrawlDataService:
    def __init__(self):
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.client = httpx.AsyncClient(
            verify=False,
            timeout=30.0,
            follow_redirects=True,  # Reverted to 30.0 for stability
        )
        self.semaphore = asyncio.Semaphore(10)  # Limit to 10 concurrent requests

    # Function to check whether the current file link is a READABLE file link (e.g., pdf, xlsx, etc.)
    def is_file_link(self, url: str) -> bool:
        file_extensions = [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".txt"]
        parsed = urlparse(url)
        path_lower = parsed.path.lower()
        return (
            any(path_lower.endswith(ext) for ext in file_extensions)
            or "/pdf/" in path_lower
        )

    # Function to login to the current file link
    async def login_session(self, username: str, password: str) -> bool:
        try:
            print(f"[DEBUG] Requesting login page: {LOGIN_URL}")
            login_page_resp = await self.client.get(LOGIN_URL)
            print(f"[DEBUG] Login page status: {login_page_resp.status_code}")
            login_page_resp.raise_for_status()

            soup = BeautifulSoup(login_page_resp.text, "html.parser")
            login_token_element = soup.find("input", {"name": "wpLoginToken"})

            if not login_token_element:
                print("[ERROR] Could not find login token on the page.")
                return False

            login_token = login_token_element["value"]

            payload = {
                "wpName": username,
                "wpPassword": password,
                "wpLoginToken": login_token,
                "wpLoginAttempt": "Log in",
            }

            print(f"[DEBUG] Submitting login to: {LOGIN_ACTION}")
            login_resp = await self.client.post(LOGIN_ACTION, data=payload)
            print(f"[DEBUG] Login response status: {login_resp.status_code}")
            login_resp.raise_for_status()

            if "wpName1" in login_resp.text or "Incorrect password" in login_resp.text:
                print("[ERROR] Login failed. Check credentials or form payload.")
                return False

            print("[INFO] Login successful.")
            return True

        except httpx.RequestError as e:
            print(f"[ERROR] An error occurred during login: {e}")
            return False

    # Function to save scraped data to a text file
    def save_to_file(self, file_data: list, filename: str = "scraped_files.txt"):
        try:
            with open(filename, "w", encoding="utf-8") as file:
                file.write("Scraped Files:\n")
                file.write("=" * 50 + "\n")
                for item in file_data:
                    file.write(f"Name: {item['name']}\n")
                    file.write(f"URL: {item['url']}\n")
                    file.write("-" * 50 + "\n")
                file.write(f"Total files saved: {len(file_data)}\n")
            print(f"[INFO] Data saved to {filename}")
        except IOError as e:
            print(f"[ERROR] Failed to save data to {filename}: {e}")

    async def fetch_page(self, url: str) -> tuple[BeautifulSoup, str]:
        async with self.semaphore:
            try:
                response = await self.client.get(url)
                if response.status_code != 200:
                    print(
                        f"[WARNING] Skipped {url} due to status {response.status_code}"
                    )
                    return None, url
                return BeautifulSoup(response.text, "html.parser"), url
            except httpx.RequestError as e:
                print(f"[WARNING] Skipped {url} due to error: {e}")
                return None, url

    async def crawl_page(
        self,
        url: str,
        depth: int,
        visited_urls: set,
        to_crawl: list,
        found_files: set,
        max_depth: int,
        max_links: int,
    ):
        if depth > max_depth or url in visited_urls or len(found_files) >= max_links:
            return

        visited_urls.add(url)
        print(f"[INFO] Crawling: {url} at depth {depth}")

        soup, _ = await self.fetch_page(url)
        if soup is None:
            return

        all_links = soup.find_all("a", href=True)
        for link in all_links:
            href = link.get("href")
            if not href:
                continue

            full_url = urljoin(url, href)
            # Skip anchor links
            if full_url.startswith(f"{MAIN_PAGE}#"):
                continue

            if self.is_file_link(full_url):
                file_data = {
                    "name": link.get_text(strip=True) or link.get("title") or full_url,
                    "url": full_url,
                }
                file_tuple = (file_data["name"], file_data["url"])
                if file_tuple not in found_files:
                    found_files.add(file_tuple)

            # Only add non-file links for exploration if within depth limit
            elif (
                depth < max_depth
                and not self.is_file_link(full_url)
                and full_url not in visited_urls
            ):
                to_crawl.append((full_url, depth + 1))

    async def crawl_all_file_links(
        self,
        username: str = None,
        password: str = None,
        max_links: int = MAX_LINKS,
        max_depth: int = 3,
    ):
        login_ok = await self.login_session(username, password)
        if not login_ok:
            print("[ERROR] Cannot proceed with crawl, login failed.")
            return []

        print("[INFO] Logged in Wiki session!!!")
        found_files = set()
        visited_urls = set()
        to_crawl = [(MAIN_PAGE, 0)]

        while to_crawl and len(found_files) < max_links:
            # Batch process up to 20 URLs concurrently (increased from 10)
            tasks = [
                self.crawl_page(
                    url,
                    depth,
                    visited_urls,
                    to_crawl,
                    found_files,
                    max_depth,
                    max_links,
                )
                for url, depth in to_crawl[:20]
            ]
            await asyncio.gather(
                *tasks, return_exceptions=True
            )  # Handle exceptions gracefully
            to_crawl = to_crawl[20:]  # Remove processed URLs

        print(f"[INFO] Found {len(found_files)} file(s).")
        result = [{"name": name, "url": url} for name, url in found_files]

        # Save the results to a file
        self.save_to_file(result)

        await self.client.aclose()
        print("[INFO] Session closed.")

        return result
