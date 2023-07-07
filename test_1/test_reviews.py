import csv
import random

import requests
from bs4 import BeautifulSoup

proxies = []
with open("../proxies.txt", "r") as f:
    for line in f:
        proxies.append(f"http://{line.strip()}")


# Define the review classes
review_classes = [
    ["jdgm-rev", "jdgm-divider-top", "jdgm--done-setup"],
    ["okeReviews-reviews-review"],
    ['product-review-list-review-container'],
    ['R-ContentList__item', 'u-textLeft--all'],
    ['yotpo-review', 'yotpo-regular-box']
]

# Open the CSV file
with open('main.csv', 'r', encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile)
    rows = list(reader)  # Convert reader object to a list of rows

    # Skip the header row
    header = rows[0]
    data_rows = rows[1:]

    # Extract the values from the second column (product_link)
    links = [row[1] for row in data_rows]

counter = 0
# Iterate over the links
for i, link in enumerate(links):
    if counter > 0:
        counter -= 1
        print("Skiping product")
        continue

    try:
        proxy = {'http': random.choice(proxies)}
        response = requests.get(link, proxies=proxy)
        response = response.content
    except:
        continue

    reviews = ''
    soup = BeautifulSoup(response, 'html.parser')

    # Iterate over the review classes
    for review_class in review_classes:
        reviews_containers = soup.find_all('div', attrs={'class': review_class})

        if len(reviews_containers) == 0:
            print("Not the same review system")
            continue

        for review in reviews_containers:
            reviews += review.text.replace("\n", " ").replace(",", " ")

    # Append the reviews to the 12th column (index 11) of the corresponding row
    if reviews == '':
        reviews = "N/A"
        counter = 20

    data_rows[i][11] = reviews
    print(reviews)

# Write the modified data back to the CSV file
with open('main.csv', 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(header)  # Write the header row
    writer.writerows(data_rows)  # Write the modified data rows
