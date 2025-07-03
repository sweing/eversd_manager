import requests
from bs4 import BeautifulSoup
import base64
import re

def get_vimm_info(url):
    """
    Scrapes a Vimm.net page for game information using the new layout.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        session = requests.Session()
        response = session.get(url, headers=headers, verify=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        details = {
            'title': '',
            'platform': '',
            'release_date': '',
            'developer': '',
            'publisher': '',
            'genre': '',
            'description': '',
            'download_link': None
        }

        # --- Extract Title ---
        title_canvas = soup.select_one('h2 canvas[data-v]')
        if title_canvas and 'data-v' in title_canvas.attrs:
            b64_title = title_canvas['data-v']
            details['title'] = base64.b64decode(b64_title).decode('utf-8', 'ignore')

        # --- Extract Platform ---
        platform_div = soup.select_one('div.sectionTitle')
        if platform_div:
            details['platform'] = platform_div.text.strip()

        # --- Extract Details from Table ---
        details_table = soup.find('table', class_='cellpadding1')
        if details_table:
            for row in details_table.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) >= 2:
                    key = cells[0].text.strip().lower()
                    value = cells[-1].text.strip()
                    if 'year' in key:
                        details['release_date'] = value
                    elif 'developer' in key:
                         details['developer'] = value
                    elif 'publisher' in key:
                         details['publisher'] = value
                    elif 'genre' in key:
                         details['genre'] = value


        return details, None

    except requests.exceptions.RequestException as e:
        return None, f"Error fetching URL: {e}"
    except Exception as e:
        return None, f"An unexpected error occurred: {e}"

if __name__ == '__main__':
    # Test the scraper
    test_url = "https://vimm.net/vault/4157" # Mario Tennis GBC
    info, error = get_vimm_info(test_url)
    if error:
        print(f"Error: {error}")
    else:
        import json
        print(json.dumps(info, indent=4))