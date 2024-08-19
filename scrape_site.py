import os
import re
import smtplib
import time
from email.mime.text import MIMEText

import mysql.connector
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.wait import WebDriverWait

import helpers
import my_secrets


def scroll_to_bottom():
    # Get scroll height.
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to the bottom.
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(7)
        # Calculate new scroll height and compare with last scroll height.
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


# Setup the Chrome driver
#options = webdriver.ChromeOptions()
#options.add_argument('--headless')  # Run in headless mode
#options.add_argument('--disable-gpu')  # Disable GPU acceleration
#driver = webdriver.Chrome(options=options)
driver = webdriver.Chrome()

url = my_secrets.url
# Open the URL
driver.get(url)

# Database connection parameters
db_config = my_secrets.db_config

try:
    # Establish a connection to the MariaDB database
    connection = mysql.connector.connect(**db_config)

    if connection.is_connected():
        print("Connected to the database")
except mysql.connector.Error as error:
    print(f"Error: {error}")

try:
    # Wait for the price element to be present and visible
    # WebDriverWait(driver, 20).until(
    #     EC.visibility_of_element_located((By.CSS_SELECTOR, "full-unstyled-link"))
    # )

    card__information =  By.CLASS_NAME, "card__information"
    WebDriverWait(driver, 20).until(EC.presence_of_element_located(card__information))

    scroll_to_bottom() 

    cards = driver.find_elements(By.CLASS_NAME, "card__information")
    print(f'card count: {len(cards)}')
    for card in cards:
        name = card.find_element(By.CLASS_NAME, 'card__heading').text
        
        
        price_saleprice = card.find_element(By.CLASS_NAME, 'card__product-price').text.replace('$','').split()
        price = price_saleprice[0]
        sale_price = price_saleprice[0]

        try:
            sale_price = card.find_element(By.CLASS_NAME, 'card__product-price-offer').text.replace('$','')
        except NoSuchElementException:
            sale_price = None
            pass
        try:
            cursor = connection.cursor()
            insert_query = """
                INSERT INTO booz (name, type, date_scraped, price, sale_price)
                VALUES (%s, 'Whisky', NOW(), %s,%s)
                """
            record = (name, price, sale_price)
            cursor.execute(insert_query, record)
            #connection.commit()
        except mysql.connector.Error as error:
            print(f"Error: {error} for {record}")
    connection.commit()

    # Read previous price from file or database
    previous_price_file = "price.txt"
    if os.path.exists(previous_price_file):
        with open(previous_price_file, 'r') as f:
            previous_price = f.read().strip()
    else:
        previous_price = None

    # Compare current price with previous price
    if previous_price is not None and current_price != previous_price or 1==1:
        # Notify price change
        subject = "Price Change Alert"
        body = f"The price has changed!\nPrevious Price: {previous_price}\nCurrent Price: {current_price}"
        helpers.send_email(subject, body)
        print('email sent')

    # Update previous price file
    with open(previous_price_file, 'w') as f:
        f.write(current_price)

except Exception as e:
    print("Price check failed:", str(e))

finally:
    # Close the driver
    driver.quit()
