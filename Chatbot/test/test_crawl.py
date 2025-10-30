import asyncio
import os
import pprint  # Used for cleaner dictionary printing
import sys
from dotenv import load_dotenv

# This adds your project root to the Python path
# so the 'from backend...' import works
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# --- Adjust this import path if your file is located elsewhere ---
from backend.service.crawl_data import CrawlDataService


load_dotenv()


async def main():
    """
    Main async function to run the crawler test.
    """

    # # 1. Load credentials securely from environment variables
    # wiki_user = os.environ.get("WIKI_USER")
    # wiki_pass = os.environ.get("WIKI_PASS")

    # if not wiki_user or not wiki_pass:
    #     print("=" * 50)
    #     print("ERROR: Missing Credentials")
    #     print("Please set the WIKI_USER and WIKI_PASS environment variables.")
    #     print("  On Linux/macOS: export WIKI_USER='your_username'")
    #     print("  On Windows CMD:   set WIKI_USER='your_username'")
    #     print("  On PowerShell:    $env:WIKI_USER='your_username'")
    #     print("=" * 50)
    #     return

    # print(f"[INFO] Starting crawler test as user: {wiki_user}")

    USERNAME = os.environ.get("USERNAME")
    PASSWORD = os.environ.get("PASSWORD")

    # 2. Initialize and run the service
    service = CrawlDataService()
    found_files = []

    try:
        found_files = await service.crawl_all_file_links(
            username=USERNAME, password=PASSWORD
        )
    except Exception as e:
        print(f"[CRITICAL] An error occurred during the crawl: {e}")

    # 3. Print the results
    print("\n" + "=" * 50)
    print(" CRAWL COMPLETE ")
    print(f" Total files found: {len(found_files)}")
    print("=" * 50)

    if found_files:
        print("--- Found Files ---")
        pprint.pprint(found_files)


if __name__ == "__main__":
    asyncio.run(main())
