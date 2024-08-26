import os
import re
import smtplib
import time
import traceback  # <<<<<<<<<<<<<remove this later
from decimal import Decimal
from email.mime.text import MIMEText

import mysql.connector
from mysql.connector import Error
from selenium import webdriver
from selenium.common.exceptions import (NoSuchElementException,
                                        StaleElementReferenceException)
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

def clean_money(price_saleprice_dirty):
    price_saleprice_clean = price_saleprice_dirty.replace('$','').replace(',','')
    
    return price_saleprice_clean

def insert_booz_data(booz_id, price, sale_price, check_price):
    insert_booz_data = """INSERT INTO booz_scraped (booz_id, price, sale_price)
        VALUES (%s,%s,%s )
        """
    if check_price:
        cursor.execute("""
        SELECT price, sale_price
        FROM booz_scraped bs
        WHERE bs.date_scraped = 
            (SELECT MAX(date_scraped)
             FROM booz_scraped
             WHERE booz_id = %s)
        AND bs.booz_id = %s
        """, (booz_id,booz_id,))
        existing_data = cursor.fetchone()
        if existing_data:
            
            existing_price = existing_data.get('price')
            existing_sale_price = existing_data.get('sale_price')

            # Convert existing_price to Decimal if it is not already
            if isinstance(existing_price, str):
                existing_price = Decimal(existing_price)
            if isinstance(existing_sale_price, str):
                existing_sale_price=Decimal(existing_sale_price)

            cursor.reset() 
            if existing_price != price or existing_sale_price != sale_price:
                cursor.execute(insert_booz_data, (booz_id, price, sale_price))
                print(f'inserted prices info for EXISTING item {booz_id}')
            else:
                print(f'Price unchanged for EXISTING item {booz_id}')
        else:
            cursor.execute(insert_booz_data, (booz_id, price, sale_price))
            print(f'inserted prices info for NEW item {booz_id}')

# Setup the Chrome driver
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # Run in headless mode
#options.add_argument('--disable-gpu')  # Disable GPU acceleration
driver = webdriver.Chrome(options=options)
driver = webdriver.Chrome()

url = my_secrets.url
# Open the URL
driver.get(url)

card__information =  By.CLASS_NAME, "card__information"
WebDriverWait(driver, 20).until(EC.presence_of_element_located(card__information))

#scroll_to_bottom() 

cards = driver.find_elements(By.CLASS_NAME, "card__information")
print(f'card count: {len(cards)}')

scraped_booz = []

try:    
    for card in cards:
        name = card.find_element(By.CLASS_NAME, 'card__heading').text
                    
        price_saleprice_dirty = card.find_element(By.CLASS_NAME, 'card__product-price').text
        price_saleprice_clean_list = clean_money(price_saleprice_dirty).split()
        if len(price_saleprice_clean_list) == 2:
            price, sale_price = price_saleprice_clean_list
            if isinstance(price, str):
                price = Decimal(price)
            if isinstance(sale_price, str):
                sale_price = Decimal(sale_price)    

        elif len(price_saleprice_clean_list) == 1:
            price = price_saleprice_clean_list[0]
            if isinstance(price, str):
                price = Decimal(price)    

            sale_price = None
        else:
            price = sale_price = None

        try:
            sale_price_string = card.find_element(By.CLASS_NAME, 'card__product-price-offer').text
            #TODO  : Log that there are two sale prices
            sale_price = clean_money(sale_price_string)
            if isinstance(sale_price, str):
                sale_price = Decimal(sale_price)    
 
        except NoSuchElementException:
            sale_price = None
            #print(f'ERROR: Sale price elemtent not found for: {name}')
            #traceback.print_exc()

        scraped_booz.append({
            'booz_name': name,
            'price': price,
            'sale_price': sale_price 
        })
except StaleElementReferenceException:
    print("StaleElementReferenceException encountered")

finally:
    driver.quit()   


# Database connection parameters
db_config = my_secrets.db_config

try:
    # Establish a connection to the MariaDB database
    connection = mysql.connector.connect(**db_config)

    if connection.is_connected():
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""SELECT b.booz_id, booz_name, bs.price, bs.sale_price FROM booz b JOIN booz_scraped bs on b.booz_id = bs.booz_id""")
        existing_items = cursor.fetchall()
        booz_names_existing = {item['booz_name']: item['booz_id'] for item in existing_items}

        #booz_names_existing = {row[0]: row[1] for row in result}  # row[0] is booz_id, row[1] is booz_name

        for item in scraped_booz:
            if item['booz_name'] in booz_names_existing:
                booz_id = booz_names_existing[item['booz_name']]
                insert_booz_data(booz_id, item['price'], item['sale_price'], True)
            else:
                insert_query = """
                    INSERT INTO booz (booz_name, type)
                    VALUES (%s, 'Whisky')
                    """
                cursor.execute(insert_query, (name,))
                connection.commit()
                booz_id = cursor.lastrowid
                print(f'inserted {name}')
                insert_booz_data(booz_id, item['price'], item['sale_price'], False)
except Error:
    print(f"Error: {Error}")
    traceback.print_exc()

finally:
    if cursor:
        cursor.close()
    if connection.is_connected():
        connection.close()

    
          


    # except Exception as e:
    #     # Rollback in case of any error
    #     connection.rollback()
    #     print(f"An error occurred looping over cards: {e}")
    #     traceback.print_exc()




