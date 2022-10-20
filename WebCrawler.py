from atexit import register
from http import client
from math import prod

import os
import requests
import urllib
import json
from collections import OrderedDict
import time

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

# Get values from env.json file
with open(os.path.dirname(os.path.realpath(__file__)) + "/env.json", 'r') as f:
    env_file = json.load(f)

client_id = env_file['ID']
client_secret = env_file['SECRET']
direct = env_file['DIR']

# Use chromedriver for crawling
options = webdriver.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)
options.add_experimental_option("prefs", {"prfile.managed_default_content_setting.images": 2})
driver = webdriver.Chrome(direct + 'Khureen/chromedriver', options=options)

driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
            """
})

# Input keyword and display
keyword = "당근"
display = "100"

# Get eco-friendly products for keywords from API
query = "친환경 " + keyword
query = urllib.parse.quote(query)

# Create a folder with the name of the keyword
directory = direct + "Khureen/GreenLR/items/" + keyword
try:
    if not os.path.exists(directory):
        os.makedirs(directory)
except OSError:
    print('Error: Creating directory. ' +  directory)

# Get request to Naver Shopping API
url = "https://openapi.naver.com/v1/search/shop?query=" + query + "&display=" + display + "&filter=naverpay"

request = urllib.request.Request(url)
request.add_header('X-Naver-Client-Id', client_id)
request.add_header('X-Naver-Client-Secret', client_secret)

response = urllib.request.urlopen(request)
api_text = response.read().decode('utf-8')

# Save request result as api_result.json file
file = open(direct + "Khureen/GreenLR/src/api_result.json", "w") 
file.write(api_text)
file.close()

# Get value from api_result.json file
with open(direct + "Khureen/GreenLR/src/api_result.json", 'r') as f:
    json_data = json.load(f)

# Repeat as many times as the number of data retrieved from the API
count = 0
for i in range(int(display)):
    try: # Skip if exception occurs
        # Get value from API
        productID = json_data['items'][i]['productId']
        name = json_data['items'][i]['title'].replace('<b>', '').replace('</b>', '')
        vendor = json_data['items'][i]['mallName']
        picUrl = json_data['items'][i]['image']
        price = json_data['items'][i]['lprice']
        deliveryFee = "None"

        # Convert originalURL
        detailpicUrl = []
        originalUrl = json_data['items'][i]['link']
        driver.get(url=originalUrl)
        driver.implicitly_wait(3)
        originalUrl = driver.find_elements('xpath', '//*[@class="product_btn_link__XRWYu"]')[1].get_attribute('href')
        driver.get(url=originalUrl)
        driver.implicitly_wait(3)

        # Skip when connected to a shopping mall other than Naver Shopping
        if driver.title.find("잠깐! 네이버") != -1:
            continue   
        time.sleep(1)

        # Crawling information that cannot be fetched from the API
        elem = driver.find_element('xpath', '//*')
        source_code = elem.get_attribute("outerHTML")
        detail = driver.find_element('xpath', '//*[@id="INTRODUCE"]')
        thumbnail = driver.find_element('xpath', '//*[@id="_productTabContainer"]')
        deliveryFee = source_code.split("\"baseFee\":")[-1].split(",")[0]

        # Crawling information that cannot be fetched from the API
        try:
            thumbnailUrl = thumbnail.get_attribute('innerHTML')
            k = thumbnailUrl.find('data-src')
            thumbnailUrl = thumbnailUrl[k:].split("\"")[1]
        except:
            thumbnailUrl = picUrl

        # Get detail images
        k = detail.get_attribute('innerHTML').split('data-src')
        for line in k[1:]:
            detailImg = line.split('\"')[1]
            check1 = 'http' in detailImg[:8]
            check2 = 'developers.naver.com' not in detailImg
            check3 = 'help.naver.com' not in detailImg
            if check1 and check2 and check3:
                detailpicUrl.append(detailImg)
        if len(detailpicUrl) == 0:
            continue
        
        # Create a json file using the obtained values
        count += 1
        print(str(count) + " : " + productID)

        file_data = OrderedDict()
        file_data["name"] = name
        file_data["vendor"] = vendor
        file_data["picUrl"] = picUrl
        file_data["thumbnailUrl"] = thumbnailUrl
        file_data["price"] = price
        file_data["deliveryFee"] = deliveryFee
        file_data["detailpicUrl"] = detailpicUrl
        file_data["originalUrl"] = originalUrl

        result = json.dumps(file_data, ensure_ascii=False, indent='\t')

        file = open(directory + "/" + productID + ".json", "w") 
        file.write(result)
        file.close()
    except:
        print("PASS because of error.")
