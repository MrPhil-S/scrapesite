import os
import re
import smtplib
import time
import traceback  # <<<<<<<<<<<<<remove this later
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

def clean_money(price_saleprice_dirty):
    price_saleprice_clean = price_saleprice_dirty.replace('$','').replace(',','')
    
    return price_saleprice_clean

def insert_booz_data(booz_id, price, sale_price):
    insert_booz_data = """
        INSERT INTO booz_scraped (booz_id, price, sale_price)
        VALUES (%s,%s,%s )
        """
    cursor.execute(insert_booz_data, (booz_id, price, sale_price))

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
    traceback.print_exc()



select_names = """SELECT booz_id, booz_name FROM booz"""
cursor = connection.cursor()
cursor.execute(select_names)
result = cursor.fetchall()
booz_names_existing = {row[0]: row[1] for row in result}  # row[0] is booz_id, row[1] is booz_name




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
    
    cursor = connection.cursor()
    try:    
        for card in cards:
            name = card.find_element(By.CLASS_NAME, 'card__heading').text
                        
            price_saleprice_dirty = card.find_element(By.CLASS_NAME, 'card__product-price').text
            price_saleprice_clean_list = clean_money(price_saleprice_dirty).split()
            if len(price_saleprice_clean_list) == 2:
                price, sale_price = price_saleprice_clean_list
            elif len(price_saleprice_clean_list) == 1:
                price = price_saleprice_clean_list[0]
                sale_price = None
            else:
                price = sale_price = None

            try:
                sale_price_string = card.find_element(By.CLASS_NAME, 'card__product-price-offer').text
                sale_price = clean_money(sale_price_string)
            except NoSuchElementException:
                sale_price = None
                traceback.print_exc()

                pass
            
            if name in booz_names_existing: 

                booz_id = booz_names_existing[0]

                insert_booz_data(booz_id, price, sale_price)
                #get booz__id of existing item
                # select_names = """SELECT booz_id FROM booz WHERE booz_name = %s"""
                # cursor.execute(select_names,name)
                # booz_name_existing = cursor.fetchone()
                print(f'inserted prices info for EXISTING {booz_names_existing[1]}')
            else: 
                try:
                    insert_query = """
                        INSERT INTO booz (booz_name, type)
                        VALUES (%s, 'Whisky')
                        """
                    cursor.execute(insert_query, (name,))
                    connection.commit()
                    booz_id = cursor.lastrowid
                    print(f'inserted {name}')

                    insert_booz_data(booz_id, price, sale_price)
                    print(f'inserted prices info for NEW {name}')


                except mysql.connector.Error as error:
                    print(f"new record create Error: {error} for {name}")
                    traceback.print_exc()


    except Exception as e:
        # Rollback in case of any error
        connection.rollback()
        print(f"An error occurred looping over cards: {e}")
        traceback.print_exc()


    finally:
        # Ensure that the cursor and connection are closed
        cursor.close()
        connection.close()






except Exception as e:
    print("Price check failed:", str(e))
    traceback.print_exc()


finally:
    # Close the driver
    driver.quit()
