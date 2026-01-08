import re
import requests
from time import sleep
import json
import os
from bs4 import BeautifulSoup

SERPER_API_KEY = os.environ.get('SERPER_API_KEY')

def generate_phone_number_variants(phone_number):
    # Extract digits from the phone number
    digits = re.sub(r'\D', '', phone_number)

    # Generate different variants
    variants = []
    variants.append(phone_number.strip())  # Original format, without trailing newline
    variants.append(digits.strip())  # No spaces or hyphens, without trailing newline

    # Remove country code if present
    if digits.startswith('+'):
        variants.append(digits[1:].strip())  # No country code, without the '+' sign and trailing newline

    # Remove parentheses and hyphens
    digits_only = re.sub(r'\D', '', digits)

    # Generate variants without area code
    if len(digits_only) > 10:
        variants.append(digits_only[len(digits_only)-10:].strip())  # No area code, without trailing newline
        variants.append(digits_only[len(digits_only)-9:].strip())  # No country code, without the first digit and trailing newline

    return variants

def get_page_content(url: str) -> str:
    try:
        html = requests.get(url, timeout=10).text
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text(strip=True, separator='\n')
        return text[:6000]
    except requests.exceptions.RequestException as e:
        return f"Error: {e}"

def get_search_results(search_query: str):
    url = "https://google.serper.dev/search"
    
    payload = json.dumps({
        "q": search_query,
        "num": 4
    })
    
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }
    
    response = requests.post(url, headers=headers, data=payload, timeout=60)
    
    if not response.ok:
        raise Exception(f"HTTP error {response.status_code}")
    
    sleep(1)  # avoid rate limit
    
    # Parse Serper response format
    results = response.json().get("organic", [])
    
    # Convert to format similar to Brave
    formatted_results = []
    for result in results:
        formatted_results.append({
            "url": result.get("link"),
            "title": result.get("title"),
            "description": result.get("snippet")
        })
    
    return formatted_results

    
def checkPhoneLogic(phoneNumberVariants):
    queries_json = {"queries": phoneNumberVariants}
    queries = queries_json["queries"]
    urls_seen = set()
    web_search_results = []
    
    for query in queries:
        search_results = get_search_results(query)
        for result in search_results:
            url = result.get("url")
            if not url or url in urls_seen:
                continue
            
            urls_seen.add(url)
            page_content = get_page_content(url)
            if page_content.startswith("Error:"):
                result["page_content"] = page_content
            else:
                result["page_content"] = page_content[:6000]
            web_search_results.append(result)
            

    formatted_search_results = "\n".join(
            [
                f'<item index="{i+1}">\n<source>{result.get("url")}</source>\n<page_content>\n{get_page_content(result.get("url"))}\n</page_content>\n</item>'
                for i, result in enumerate(web_search_results)
            ]
        )

    return(formatted_search_results)
