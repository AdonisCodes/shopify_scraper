import csv
import json
import os
import random
import re
import time

import openai
import requests
import unicodedata
from bs4 import BeautifulSoup


def get_json(site, load_json):
    proxies = []
    with open("proxies.txt", "r") as f:
        for line in f:
            proxies.append(f"http://{line.strip()}")

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


def get_currency(source):

    regex_pattern = r'data-currency="(\w{3})"'
    match = re.search(regex_pattern, source)

    if match:
        currency_code = match.group(1)
        return currency_code
    return "USD"


def extract_ratings(text):
    pattern = r"(\d+(\.\d+)?|\.\d+) out of 5"
    matches = re.findall(pattern, text)
    ratings = [float(match[0]) for match in matches]

    if len(ratings) > 0:
        return ratings[0]
    else:
        return "N/A"

def save_product(file, product, store, currency):
    proxies = []
    with open("proxies.txt", "r") as f:
        for line in f:
            proxies.append(f"http://{line.strip()}")

    # Get all the values needed into a list
    prices = ""
    var = ""
    for variant in product['variants']:
        if len(prices) == 0:
            prices = variant['price']
        else:
            prices += f" / {variant['price']}"

        if variant['title'] == "Default Title":
            if len(var) == 0:
                var = product['title']
            else:
                var = f" / {product['title']}"
        else:
            if len(var) == 0:
                var = variant['title']
            else:
                var = f" / {variant['title']}"
    prices = prices.split(" ")
    prices = set(prices)
    prices = " ".join(list(prices))
    op = ''
    for option in product['options']:
        if option['name'] == 'Title':
          if len(op) == 0:
              op += product['title']
              continue
          else:
              op += f' / {option["name"]}'
              continue

        if len(op) == 0:
            op += option['name']
        else:
            op += f' / {option["name"]}'

    # text = b''
    # try:
    #     proxy = {'http': random.choice(proxies)}
    #     response = requests.get(f"{store}/products/{product}", proxies=proxy)
    #     text = response.content
    # except:
    #     text = b''
    #
    # print("Getting Reviews")
    # pattern = r'\d{1,4}\sreviews'
    # reviews = re.findall(pattern, f'{text}', re.IGNORECASE)
    # print(reviews)
    # if len(reviews) > 0:
    #     reviews = f'{reviews[0]}'
    # else:
    #     reviews = 'N/A'

    description = product['body_html']
    if description is None or description == '':
        description = 'No description'

    soup = BeautifulSoup(description, 'html.parser')
    description = soup.get_text(separator=" ")

    info = [store, f"{store}/products/{product['handle']}", product["title"], prices, currency, op, var, description, product['variants'][0].get("available") if product['variants'][0].get("available") is not None else "N/A" , "N/A", 'N/A', 'N/A']
    info_parsed = []
    for item in info:
        def replace_non_utf8_chars(text):
            try:
                # Attempt to encode the text using UTF-8
                encoded_text = text.encode('utf-8')
                return encoded_text
            except UnicodeEncodeError:
                # Replace non-UTF-8 characters with empty strings
                cleaned_text = ''.join(char if ord(char) < 128 else '' for char in text)
                return cleaned_text

        new_item = replace_non_utf8_chars(f"{item}".replace("\n", " ").replace(",", " ")) if type(item) != 'bool' else f"{item}"
        try:
            ittttemmmm = new_item.decode("utf-8")
            info_parsed.append(ittttemmmm)
            continue
        except:
            pass

        normalized_text = unicodedata.normalize('NFKD', new_item)
        info_parsed.append(normalized_text)

    file_exists = os.path.isfile(file)
    with open(file, 'a', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(
                ['Brand Url', 'Product Url', 'Product Title', 'Price', 'Currency', 'options1', 'options2',
                 'Description', 'Stock', 'Inventory Count', 'Average Rating',
                 'Reviews'])

        writer.writerow(info_parsed)


def main():
    stores = []
    with open("stores.txt", "r") as store_f:
        for line in store_f:
            stores.append(line.strip())

    for store in stores:
        print(f"Store: {store}")
        # TODO: add checks to check if the website exists, if not just return none ( I can deal with it later on )
        check_shopify_source = get_json(f"{store}/shop.json", False)
        if check_shopify_source is None:
            time.sleep(10)
            with open("stores_unsupported.txt", "a") as unsup_f:
                unsup_f.write(f"{store}\n")
            continue

        check_shopify_source = re.findall(r'shopify' ,f"{check_shopify_source}", re.IGNORECASE)
        if len(check_shopify_source) < 20:
            time.sleep(10)
            print("Not Match")
            with open("stores_unsupported.txt", "a") as unsup_f:
                unsup_f.write(f"{store}\n")
            continue

        currency = get_currency(get_json(f"{store}/shop.json", False))
        if currency is None:
            currency = "USD"
        print(f"Currency: {currency}")

        p_i = 1
        while True:
            print(f"Scraping Products Page: {p_i}")
            response = get_json(f"{store}/products.json?page={p_i}", True)
            if response is None:
                break

            products = response["products"]
            if len(products) == 0:
                break

            # Write the product Info to a .csv file
            print(f"Writing Product Info of: {len(products)}")
            for product in products:
                save_product("final.csv", product, store, currency)
            p_i += 1


main()
