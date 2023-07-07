import json
import random
import requests

proxies = []
with open("../proxies.txt", "r") as f:
    for line in f:
        proxies.append(f"http://{line.strip()}")

test_url = 'https://fashionnova.com/'
i = 1
count = 0
while True:
    proxy = {'http': proxies[i % 10]}
    response = requests.get(f"{test_url}/collections.json?page={i}", proxies=proxy)
    try:
        response = json.loads(response.content)
    except:
        print("ERROR")
        response = {"collections": []}

    collections = response["collections"]
    if len(collections) == 0:
        break

    for collection in collections:
        count += collection["products_count"]

    i += 1
    print(f"Current Page: {i}, Total Products: {count}")


products_count = 0
p_i = 0
while True:
    if products_count >= count:
        break

    proxy = {'http': proxies[p_i % 10]}
    response = requests.get(f"{test_url}/products.json?page={p_i}", proxies=proxy)
    response = json.loads(response.content)

    products = response["products"]

    if len(products) == 0:
        break

    with open("test.txt", "a") as t_f:
        for product in products:
            t_f.write(f"{json.dumps(product)}\n")
            products_count += 1

    p_i += 1

with open("test.txt", "r") as t_f:
    arr = []
    for line in t_f:
        arr.append(line.strip())

    with open("test.txt", "w") as w_f:
        for line in set(arr):
            w_f.write(f"{json.dumps(line)}\n")
