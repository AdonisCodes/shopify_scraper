import csv
import json
import os
import random
import re
import time

import requests
import unicodedata
from bs4 import BeautifulSoup
from selenium.webdriver import ChromeOptions, Chrome

websites = []
proxies = []
with open("proxies.txt", "r") as f:
    for line in f:
        proxies.append(f"http://{line.strip()}")


with open("stores_unsupported.txt", 'r') as f:
    for line in f:
        websites.append(line.replace('\n', ''))


def get_json(site, load_json):
    proxy = {'http': random.choice(proxies)}
    try:
        response = requests.get(f"{site}", proxies=proxy)
    except:
        return None

    if load_json:
        try:
            response = json.loads(response.content)
            return response
        except:
            return None
    return f"{response.content}"

def setup_driver():
    # initialize driver
    print("Launching chrome driver...")
    # create the chrome instance
    options = ChromeOptions()
    options.add_argument("--disable-application-cache")
    options.add_argument("--disable-cache")
    options.add_argument("--disk-cache-size=0")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-images")
    options.add_argument("--blink-settings=imagesEnabled=false")
    # options.add_argument("--enable-precise-geolocation")
    # options.add_experimental_option("geolocation", {"latitude": 37.0902, "longitude": -95.7129})
    options.add_argument("--headless")
    driver = Chrome(options=options)

    return driver


driver = setup_driver()
for website in websites:
    html = get_json(website, False)
    # Scrape all of the links
    soup = BeautifulSoup(html, 'html.parser')
    links = soup.find_all('a')
    slugs = []
    format = ''
    for link in links:
        for page in range(10):
            if link.get("href") is None:
                break
            print(website[13:-1], " : ", link["href"])
            if website[13:-1] in link['href']:
                html = driver.get(f"{link['href']}?page={page + 1}")
            else:
                html = driver.get(f"{website}/{link['href']}?page={page + 1}")

            time.sleep(3)
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            print(f'{website}/{link["href"]}?page={page+1}')
            print(f'{link["href"]}?page={page+1}')
            # Check if there is any slugs on the page
            data_slugs = soup.find_all(attrs={'data-slug': True})
            match = []
            for data_slug in data_slugs:
                match.append(data_slug['data-slug'])

            if match:
                for m in match:
                    slugs.append(m)
                    if len(slugs) == 1:
                        desired_phrase = slugs[0]
                        anchor_tags = soup.find_all('a', href=lambda href: href and desired_phrase in href)
                        if anchor_tags:
                            format = anchor_tags[0]["href"].replace(f"{website}", "")
                            format = format.replace(f"/{slugs[0]}", "")
                            print(format)
            else:
                break

    for slug in slugs:
        product_link = f"{website}/{format}/{slug}"
        response = requests.get(product_link)
        soup = BeautifulSoup(response.content, 'html.parser')
        info = soup.find('script', attrs={'type': 'application/ld+json'})
        if info:
            info = info.get_text()
        else:
            continue
        info = json.loads(info)
        product = info
        # Now that we have the info, add it to the final.csv file
        data = [website, product_link, product["name"], product['Offers']['price'], product['Offers']['priceCurrency'], "N/A", "N/A",
                product["description"], product['Offers']["Availability"][-10:], "N/A", 'N/A', 'N/A']
        data_parsed = []
        for item in data:
            def replace_non_utf8_chars(text):
                try:
                    # Attempt to encode the text using UTF-8
                    encoded_text = text.encode('utf-8')
                    return encoded_text
                except UnicodeEncodeError:
                    # Replace non-UTF-8 characters with empty strings
                    cleaned_text = ''.join(char if ord(char) < 128 else '' for char in text)
                    return cleaned_text


            new_item = replace_non_utf8_chars(f"{item}".replace("\n", " ").replace(",", " ")) if type(
                item) != 'bool' else f"{item}"
            try:
                ittttemmmm = new_item.decode("utf-8")
                data_parsed.append(ittttemmmm)
                continue
            except:
                pass

            normalized_text = unicodedata.normalize('NFKD', new_item)
            data_parsed.append(normalized_text)

        file_exists = os.path.isfile('final.csv')
        with open('final.csv', 'a', newline='', encoding='utf-8-sig') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(
                    ['Brand Url', 'Product Url', 'Product Title', 'Price', 'Currency', 'options1', 'options2',
                     'Description', 'Stock', 'Inventory Count', 'Average Rating',
                     'Reviews'])

            writer.writerow(data_parsed)