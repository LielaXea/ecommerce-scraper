"""
E-Commerce Scraper
Author: lielaxea
Github: github/LielaXea/Ecommerce-Scrap
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import pandas as pd 
import random
import time
import logging
from datetime import datetime
from tqdm import tqdm 
import argparse 

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)

class EcommerceScraper:

    USER_AGENTS = [
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]

    def __init__(self, base_url, max_pages=50, max_concurrent=5):
        """
        Args:
            base_url (str): Site URL 
            max_pages (int): Number of pages to scrape 
            max_concurrent (int): Max concurrent requests
        """
        self.base_url = base_url
        self.max_pages = max_pages
        self.max_concurrent = max_concurrent
        self.results = []
        self.errors = []

        logging.info(f"Scraper Initialized: {max_pages} pages, max {max_concurrent} concurrent")

    def get_headers(self):
        return {
            'User-Agent': random.choice(self.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.0,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        }

    async def fetch_page(self, session, page_num):
        """
        Args:
            session: aiohttp session 
            page_num (int): page number to be fetched
        """
        url = f"{self.base_url}/catalogue/page-{page_num}.html" #change this accordingly 
        
        for attempt in range(3):  #also change this
            try:
                async with session.get(
                    url,
                    headers=self.get_headers(),
                    timeout=aiohttp.ClientTimeout(total=10) # change this too
                ) as response:

                    if response.status == 200:
                        return await response.text()
                    else:
                        logging.warning(f"{response.status} on page {page_num}")

            except asyncio.TimeoutError:
                logging.warning(f"Timeout on page {page_num}, attempt {attempt + 1}")
            except Exception as e:
                logging.error(f"Error on page {page_num}: {str(e)[:50]}")

            if attempt < 2:
                await asyncio.sleep(2 ** attempt)

        self.errors.append({'page': page_num, 'error': 'Failed to fetch'})
        return None 

    def parse_page(self, html, page_num):
        """
        Args:
            html (str): html content
            page_num (int): page number
        """
        try:
            soup = BeautifulSoup(html, 'html.parser') #from here on make sure to change EVERYTHING to fit ur site
            products = soup.select('article.product_pod')

            for product in products:
                try:
                    title = product.h3.a['title']

                    price_text = product.select_one('.price_color').text
                    price = float(price_text.replace('£', '').strip()) #currency symbol replacing might not be needed at all

                    rating_class = product.select_one('.star-rating')['class']
                    rating_map = {'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5}
                    rating = rating_map.get(rating_class[1], 0)

                    availability = product.select_one('.instock.availability').text.strip()
                    in_stock = 'In stock' in availability

                    img_url = product.select_one('img')['src']
                    img_url = f"{self.base_url}/{img_url.replace('../', '')}"

                    product_url = product.h3.a['href']
                    product_url = f"{self.base_url}/catalogue/{product_url.replace('../../../', '')}"

                    self.results.append({
                        'Product Name': title, 
                        'Price (£)': price,
                        'Rating (1-5)': rating, 
                        'In Stock': in_stock,
                        'Availability text': availability, 
                        'Image URL': img_url,
                        'Product URL': product_url,
                        'Scraped from page': page_num
                    })

                except Exception as e:
                    logging.warning(f"Failed to parse product on page {page_num}: {e}")
                    continue
        
        except Exception as e: 
            logging.error(f"Parse error at page {page_num}: {e}")
            self.errors.append({'page': page_num, 'error': f'Parse error: {e}'})

    async def scrape_all(self):
        logging.info("Starting scrape...")
        start_time = time.time()

        semaphore = asyncio.Semaphore(self.max_concurrent)

        async with aiohttp.ClientSession() as session:
            tasks = []

            for page_num in range(1, self.max_pages + 1):
                async def scrape_page_wrapper(page=page_num):
                    async with semaphore:
                        html = await self.fetch_page(session, page)
                        if html:
                            self.parse_page(html, page)
                tasks.append(scrape_page_wrapper())

            for coro in tqdm(asyncio.as_completed(tasks),
                             total=len(tasks),
                             desc="Scraping pages"):
                await coro
        
        elapsed = time.time() - start_time

        logging.info(f"Scraping complete int {elapsed:.1f}s")
        logging.info(f"Products found: {len(self.results)}")
        logging.info(f"Errors: {len(self.errors)}")
        logging.info(f"Speed: {len(self.results)/elapsed:.1f} products/second")

    def export_to_excel(self, filename='products.xlsx'):
        """
        Args:
            filename (str): output file
        """

        if not self.results:
            logging.warning("No data to export")
            return 

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{filename.replace('.xlsx', '')}_{timestamp}.xlsx"

        df = pd.DataFrame(self.results)

        df = df.sort_values(['Rating (1-5)', 'Price (£)'], ascending=[False, True])

        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Products', index=False)

            workbook = writer.book
            worksheet = writer.sheets['Products']

            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).apply(len).max(),
                    len(col)
                ) + 2 
                worksheet.column_dimensions[chr(65 + idx)].width = min(max_length, 50)

        logging.info(f"Exported to {filename}")

        if self.errors:
            error_df = pd.DataFrame(self.errors)
            error_file = f"errors_{timestamp}.xlsx"
            error_df.to_excel(error_file, index=False)
            logging.warning(f"Errors exported to {error_file}")

        return filename 

        
    def print_summary(self):
        if not self.results:
            print("No data collected")
            return 
        df = pd.DataFrame(self.results)

        print("\n" + "="*70)
        print("Summary")
        print(f"Total products:        {len(df)}")
        print(f"Average price:         £{df['Price (£)'].mean():.2f}")
        print(f"Price range:           £{df['Price (£)'].min():.2f} - £{df['Price (£)'].max():.2f}")
        print(f"In stock:              {df['In Stock'].sum()} ({df['In Stock'].sum()/len(df)*100:.1f}%)")
        print(f"Average rating:        {df['Rating (1-5)'].mean():.2f}/5")
        print(f"\nRating distribution:")
        print(df['Rating (1-5)'].value_counts().sort_index())

def main():
    parser = argparse.ArgumentParser(
        description='E-Commerce product scraper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
            python scraper.py --pages 10 
            python scraper.py --pages 50 --output my_products.xlsx 
            python scraper.py --pages 100 --concurrent 10
        """
    )

    parser.add_argument(
        '--pages',
        type=int,
        default=10,
        help='Number of pages to scrape (default: 10)'
    )

    parser.add_argument(
        '--output',
        default='products.xlsx',
        help='Output file name (default: products.xlsx)'
    )

    parser.add_argument(
            '--concurrent',
            type=int,
            default=5,
            help='Max concurrent requests (default: 5)'
    )

    args = parser.parse_args()

    scraper = EcommerceScraper( #change to fit thy needs
        base_url="http://books.toscrape.com",
        max_pages=args.pages,
        max_concurrent=args.concurrent
    )

    asyncio.run(scraper.scrape_all())
    scraper.print_summary()
    output_file = scraper.export_to_excel(args.output)
    print(f"Saved results to {output_file}\n")

if __name__ == "__main__":
    main()
