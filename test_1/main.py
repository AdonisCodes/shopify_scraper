import csv
import os
import re
import time
import winsound

import requests as requests
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.support import expected_conditions as EC
from forex_python.converter import CurrencyCodes
import openai

openai.api_key = "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"


def extract_description(text):
    time.sleep(10)
    completion = ''
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            messages=[
                {"role": "system", "content": "You are a bot that can extract the description from a given text, and only reply with the description, following the user instructions, reply only with the correct response and no other boilerplate like Description: or The description is: ect..."},
                {"role": "user", "content": f'''
                Your job is to extract the description from a given product, and you are given only the inner text of the webpages main element. You should use keywords like more about product, description, more, information ect to locate the description, Return only the segmented description. Here is the innerText of the main element:
                {text.strip()}'''}
            ]
        )
    except:
        extract_description(text)

    return completion.choices[0].message.content

def stock_check(text):
    time.sleep(10)
    completion = ''
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            messages=[
                {"role": "system", "content": 'Your job is to extract information from a given product, and you are given only the inner text of the webpages main element.  Please extract and check if  the product is currently in stock, if not please just reply with "IN STOCK" if out of stock reply with "OUT OF STOCK" and if unknown reply with "UNKNOWN",  reply extremely accurately and reply with the response only.'},
                {"role": "user", "content": f'''
                Your job is to extract information from a given product, and you are given only the inner text of the webpages main element.  Please extract and check if  the product is currently in stock, if not please just reply with "IN STOCK" if out of stock reply with "OUT OF STOCK" and if unknown reply with "UNKNOWN",  reply extremely accurately and reply with the response only:
                {text.strip()}'''}
            ]
        )
    except:
        stock_check(text)
    return completion.choices[0].message.content


def inventory_check(text):
    time.sleep(20)
    completion = ''
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            messages=[
                {"role": "system", "content": 'Your job is to extract information from a given product, and you are given only the inner text of the webpages main element.  Please extract and return the amount of inventory if it exists else reply just with "N/A", if not please just reply with "IN STOCK" if out of stock reply with "OUT OF STOCK" and if unknown reply with "UNKNOWN",  reply extremely accurately and reply with the response only.'},
                {"role": "user", "content": f'''
                Your job is to extract information from a given product, and you are given only the inner text of the webpages main element.  Please extract and return the amount of inventory if it exists else reply just with "N/A", if not please just reply with "IN STOCK" if out of stock reply with "OUT OF STOCK" and if unknown reply with "UNKNOWN",  reply extremely accurately and reply with the response only:
                {text.strip()}'''}
            ]
        )
    except:
        inventory_check(text)

    return completion.choices[0].message.content


def extract_reviews(text):
    time.sleep(20)
    completion = ''
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            messages=[
                {"role": "system",
                 "content": 'Your job is to extract information from a given product, and you are given only the inner text of the webpages main element.  Please extract and return the product reviews in ordered list form where the format is N. Username - Review , if, If there is no reviews available, please just reply with "N/A", reply extremely accurately and reply with the response only:'},
                {"role": "user", "content": f'''
                Your job is to extract information from a given product, and you are given only the inner text of the webpages main element.  Please extract and return the product reviews in ordered list form where the format is N. Username - Review , if, If there is no reviews available, please just reply with "N/A", reply extremely accurately and reply with the response only:
                {text.strip()}'''}
            ]
        )
    except:
        extract_reviews(text)

    return completion.choices[0].message.content


def extract_rating(text):
    time.sleep(20)
    completion = ''
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            messages=[
                {"role": "system",
                 "content": 'Your job is to extract information from a given product, and you are given only the inner text of the webpages main element.  Please extract and return the average rating from the text it will be in the format of 4.5 out of 5, only reply with the first number you find, reply extremely accurate and with the response only:'},
                {"role": "user", "content": f'''
                Your job is to extract information from a given product, and you are given only the inner text of the webpages main element.  Please extract and return the average rating from the text it will be in the format of 4.5 out of 5, only reply with the first number you find, reply extremely accurate and with the response only:
                {text.strip()}'''}
            ]
        )
    except:
        extract_rating(text)

    return completion.choices[0].message.content



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
    options.add_argument("--enable-precise-geolocation")
    options.add_experimental_option("geolocation", {"latitude": 37.0902, "longitude": -95.7129})
    # options.add_argument("--headless")
    driver = Chrome(options=options)

    return driver

def check_shopify(store, page_source):
    if "shopify" not in page_source:
        print(f"Not a Shopify Page, Manually scrape the page: {store}")
        return False
    return True

def get_site(driver, site):
    driver.get(f"{site}")
    wait = WebDriverWait(driver, 100)  # Wait for a maximum of 10 seconds
    wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
    return driver.page_source

def get_all_products(driver, site):
    index = 1
    products = []
    duplicate_times = 0
    while True:
        if duplicate_times > 50:
            break

        source = get_site(driver, f"{site}collections/all?page={index}&itemsPerPage=100")

        scroll_pause_time = 1
        screen_height = driver.execute_script("return window.screen.height;")
        i = 1

        while True:
            driver.execute_script("window.scrollTo(0, {screen_height}*{i});".format(screen_height=screen_height, i=i))
            i += 1
            time.sleep(scroll_pause_time)
            scroll_height = driver.execute_script("return document.body.scrollHeight;")
            if (screen_height) * i > scroll_height:
                break

        soup = BeautifulSoup(source, 'html.parser')

        br = False
        anchor_tags = soup.find_all('a')
        matches = 0
        pattern = r'/products/[\w-]+'
        for tag in anchor_tags:
            href = tag.get("href")
            if href:
                match = re.search(pattern, href)
                if match:
                    if f"{site}{match.group(0)}" not in products:
                        products.append(f"{site}{match.group(0)}")
                        matches += 1
                        continue

                    br = True

        if br:
            duplicate_times += 1
            if index > 2000:
                break

        if matches == 0:
            break

        index += 1
        print(f"Page {index} Duplication: {duplicate_times}")

    return set(products)


def write_to_csv(data, filename):
    file_exists = os.path.isfile(filename)
    with open(filename, 'a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            # Write the header only if the file doesn't exist
            writer.writerow(['Brand Url', 'Product Url', 'Product Title', 'Price', 'Currency', 'options1', 'options2', 'Description', 'Stock', 'Inventory Count', 'Average Rating', 'Reviews'])  # Replace with your column names

        # Write the data rows
        writer.writerow(data)


def scrape_product_info(driver, store, url):
    # Go to that website
    source = get_site(driver, url)
    time.sleep(10)

    scroll_pause_time = 1
    screen_height = driver.execute_script("return window.screen.height;")
    i = 1

    while True:
        driver.execute_script("window.scrollTo(0, {screen_height}*{i});".format(screen_height=screen_height, i=i))
        i += 1
        time.sleep(scroll_pause_time)
        scroll_height = driver.execute_script("return document.body.scrollHeight;")
        if (screen_height) * i > scroll_height:
            break


    # Get the HTML
    soup = BeautifulSoup(source, 'html.parser')
    # Get the product Title
    match = re.search(r"products/(.*)", url)
    product_title = match.group(1).replace("-", " ").replace("_", " ")
    description = soup.main.get_text(separator="\n")
    inner_text = description

    # Get the proper Currency and Price
    price = ''
    currency = ''
    pattern = r"(?<!\S)([A-Z]{1,3})?\d+(\.\d{2})?(?!\S)"
    matches = re.findall(pattern, source)
    for match in matches:
        currency = match[0] if match[0] else ""  # Optional currency symbol
        price = f"{currency}{match[1]}" if match[1] else ""  # Full amount including symbol
        currency_codes = CurrencyCodes()
        currency = currency_codes.get_currency_code_from_symbol(currency)
        if currency == "ARS":
            currency = "USD"

    description = extract_description(text=inner_text)
    stock = stock_check(inner_text)
    inventory_count = inventory_check(inner_text)
    average_rating = extract_rating(inner_text)
    reviews = extract_reviews(inner_text)

    items = [store, f"{url}", product_title, price, currency, "", "", description, stock, inventory_count, average_rating, reviews]
    l2 = []
    for item in items:
        new_item = item.strip().replace("\n", " ")

        def replace_non_utf8_chars(text):
            try:
                # Attempt to encode the text using UTF-8
                encoded_text = text.encode('utf-8')
                return text
            except UnicodeEncodeError:
                # Replace non-UTF-8 characters with empty strings
                cleaned_text = ''.join(char if ord(char) < 128 else '' for char in text)
                return cleaned_text

        new_item = replace_non_utf8_chars(new_item)

        try:
            decoded = new_item.decode('utf-8')
            l2.append(decoded)
        except:
            l2.append(new_item)

    return l2


def main():
    stores = []
    driver = setup_driver()
    with open("../stores.txt", "r") as store_f:
        for line in store_f:
            stores.append(line.strip())

    for store in stores:
        check_shopify_source = get_site(driver, store)
        if check_shopify_source is None:
            continue



        # Find all the products in all the pages of that site
        products = get_all_products(driver, store)
        if products is None:
            continue
        # Scrape and append all the information of the products to the CSV file
        for product in products:
            product_info = scrape_product_info(driver, store, product)
            if product_info is None:
                continue

            print(product_info)
            write_to_csv(product_info, "a.csv")
            winsound.Beep(1000, 1)


# try:
main()
# except Exception as e:
#     print(e)
#     winsound.Beep(500, 10)
