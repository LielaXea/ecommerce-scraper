# E-commerce Product Scraper

Web scraper for extracting product data from e-commerce websites.

## Features

- **Pretty fast**: runs async
- **Pretty robust**: has some error handling, retry logic and rate limiting
- **Pretty clean**: Validates and formats data
- **Excel**: exports to Excel
- **A bit configuragle**: Can change some stuff (i.e page numbers, filename and concurrent requests) with command line args

## Requirements

- Python 3.9+
- Run 'pip install -r requirements.txt' for dependencies

## Installation

```bash
# Clone this repo
git clone https://github.com/LielaXea/ecommerce-scraper.git
cd ecommerce-scraper

# Install dependencies
pip install -r requirements.txt
```
## Usage

```bash
# Basic Usage
python scraper.py 

# Custom output file name
python scraper.py --output yourfile.xlsx

# Go faster 
python scraper.py --concurrent 10

# More pages
python scraper.py --pages 100
```
### Output will look like this

![Terminal output](/images/output.png "Terminal")

### Data will look like this 

![Sheets preview](images/sheets.png "Sheets")

## Configuration 

Edit scraper.py to fit thy needs:

```python
# Change base URL
base_url = "http://your-target-site.com"

# Adjust user agents
USER_AGENTS = [
    'Mozilla/5.0 ...',
    # Add more
]

# Modify selectors for different sites
products = soup.select('div.your-product-class')
```
## Legal & Ethics

This scraper was built because I'm BROKE and JOBLESS, only use it for educational purposes or on authorized websites. Always check robots.xml and respect rate limits.

## Logging

Logs are saved to 'scraper.log'


- Built with [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/), [aiohttp](https://docs.aiohttp.org/) and [Pandas](https://pandas.pydata.org/)
