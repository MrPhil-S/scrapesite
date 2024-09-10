import logging
import os
import re
import smtplib
import time
import traceback  # <<<<<<<<<<<<<remove this later
from decimal import Decimal
from email.mime.text import MIMEText

import mysql.connector
from mysql.connector import Error
#from selenium import webdriver
from selenium.common.exceptions import (NoSuchElementException,
                                        StaleElementReferenceException)
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.wait import WebDriverWait

import driver
import helpers
import my_secrets

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG, filename='app.log', filemode='w', format='%(asctime)s - %(levelname)s - %(message)s')
logger.info(f"Job started")


def clean_money(price_saleprice_dirty):
    price_saleprice_clean = price_saleprice_dirty.replace('$','').replace(',','')
    
    return price_saleprice_clean

def insert_booz_data(booz_id, price, sale_price, run_id, check_price):
    insert_booz_data = """INSERT INTO booz_scraped (booz_id, price, sale_price, run_id)
        VALUES (%s,%s,%s,%s)
        """
    if check_price:
        cursor.execute("""
        SELECT price, sale_price
        FROM booz_scraped bs
        WHERE bs.scrape_date = 
            (SELECT MAX(scrape_date)
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
                cursor.execute(insert_booz_data, (booz_id, price, sale_price, run_id))
                connection.commit()
                print(f'inserted prices info for EXISTING item {booz_id}')
            else:
                print(f'Price unchanged for EXISTING item {booz_id}')
        else:#price does not need to be checked, this is a new item
            cursor.execute(insert_booz_data, (booz_id, price, sale_price, run_id))
            connection.commit()
            print(f'inserted prices info for backfilled item {booz_id}')
    else:#price does not need to be checked, this is a new item
        cursor.execute(insert_booz_data, (booz_id, price, sale_price, run_id))
        connection.commit()
        print(f'inserted prices info for NEW item {booz_id}')


def get_watchlist_hits():
    cursor.execute("""
                    SELECT b.booz_id, b.link, b.booz_name, b.link, COALESCE(bs.sale_price, bs.price) price, w.price_point
                    FROM `booz` b 
                    LEFT JOIN
                        (SELECT
                            ROW_NUMBER() OVER (PARTITION BY booz_id ORDER BY scrape_date DESC) AS row_num,
                            booz_id, 
                            price,
                            sale_price,
                            scrape_date 
                        FROM  booz_scraped )bs 
                    ON b.booz_id = bs.booz_id and bs.row_num = 1
                    LEFT JOIN watchlist w
                    ON w.booz_name = b.booz_name
                    WHERE COALESCE(bs.sale_price, bs.price) < w.price_point""")
    watchlist_hits = cursor.fetchall()

    formatted_watchlist = [f'''<a href="{row["link"]}">{row["booz_name"]}</a> ({row["booz_id"]}) 
                           <br> The price is below the price point of ${row["price_point"]}: It is now <b>${row["price"]}</b>''' 
                           for row in watchlist_hits]
     
    return formatted_watchlist


def get_sale_hits(discount):
    cursor.execute(f"""
                    SELECT b.booz_id, b.booz_name, b.link, bs.price, bs.sale_price, cast(100-(bs.sale_price/bs.price*100) as int) discount
                    FROM  booz b 
                    JOIN 
                        (SELECT
                            ROW_NUMBER() OVER (PARTITION BY booz_id ORDER BY scrape_date DESC) AS row_num,
                            booz_id, 
                            price,
                            sale_price
                        FROM  booz_scraped ) bs 
                    ON b.booz_id = bs.booz_id and bs.row_num = 1
                    WHERE 100-(bs.sale_price/bs.price*100) > {discount}
                    ORDER BY 100-(bs.sale_price/bs.price*100) DESC""")
    sale_hits = cursor.fetchall()

    formatted_salelist = [f'''<a href="{row["link"]}">{row["booz_name"]}</a> ({row["booz_id"]})
                          <br> <s>${row["price"]}</s>  <b>${row["sale_price"]} {row["discount"]}%</b> off!
                          ''' for row in sale_hits]
                #<br><img src="data:image/png;base64,{helpers.generate_price_history_chart(row["booz_id"])}" alt="Price History Chart">
                          
    return formatted_salelist

def get_new_or_changed_prices(run_id):
    cursor.execute(f"""
WITH cte AS
(SELECT 
    	b.booz_id,
    	b.booz_name,
    	b.link,
    	bs.price,
    	bs.sale_price,
    	bs.run_id,
    	ROW_NUMBER() OVER (PARTITION BY bs.booz_id ORDER BY bs.scrape_date DESC) AS row_num
    FROM booz_scraped bs
    JOIN booz  b
    ON bs.booz_id = b.booz_id
    WHERE bs.run_id <= 31)
SELECT
 	current_price.booz_id,
    current_price.booz_name,
    current_price.link,
    current_price.price c_price,
    current_price.sale_price c_sale_price,
    CAST(100-(current_price.sale_price/current_price.price * 100) AS INT) c_discount,
    previous_price.price p_price,
    previous_price.sale_price p_sale_price,
    CAST(100 - (previous_price.sale_price/previous_price.price *100) AS INT) p_discount,
    CASE WHEN current_price.sale_price >= previous_price.price THEN 1 
        WHEN current_price.price > previous_price.price AND current_price.sale_price IS NOT NULL THEN 2 
        ELSE NULL END gouge_type
 FROM cte current_price
 JOIN cte previous_price 
 ON current_price.booz_id = previous_price.booz_id AND previous_price.row_num = 2 
 WHERE current_price.row_num = 1""")
    new_or_changed_prices = cursor.fetchall()
    formatted_new_or_changed_prices = [f'''<a href="{row["link"]}">{row["booz_name"]}</a> ({row["booz_id"]})<br>'''
                          + (f'''Currently <s>${row["c_price"]}</s> <b>${row["c_sale_price"]} {row["c_discount"]}%</b> off!''' if row["c_sale_price"] is not None else 
                             f'''Currently ${row["c_price"]}''')

                          + (f''' Previously <s>${row["p_price"]}</s> <b>${row["p_sale_price"]} {row["p_discount"]}%</b> off!''' if row["p_sale_price"] is not None else 
                             f''' Previously ${row["p_price"]}''')
                          + (f'''<b style="color:red"> (Sale not better then previous price!) </b>''' if row["gouge_type"] == 1 else
                             f'''<b style="color:red"> (Bumped price above previous price) </b>''' if row["gouge_type"] == 2 else
                             '')
                          for row in new_or_changed_prices]

    return formatted_new_or_changed_prices

def get_percent_discounted():
    cursor.execute("""
        SELECT CAST(COUNT(sale_price) / COUNT(*) * 100 AS INT) AS percent_discounted
        FROM booz_scraped
    """)
    result = cursor.fetchone()
    return result["percent_discounted"]

def get_average_discount():
    cursor.execute("""
        SELECT CAST(AVG(100-(bs.sale_price/bs.price*100) )as int) average_discount 
        FROM booz_scraped bs
        WHERE sale_price is not null""")
    result = cursor.fetchone()
    return result["average_discount"]


# Setup the Chrome driver
#options = driver.webdriver.ChromeOptions()
#driver.options.add_argument('--headless')  # Run in headless mode
#driver.options.add_argument('--disable-gpu')  # Disable GPU acceleration
driver = driver.driver
#driver = webdriver.Chrome()

url = my_secrets.url

# Open the URL
driver.get(url)
booz_page = url.rsplit('/', 1)[-1]

card__information =  By.CLASS_NAME, "card__information"
WebDriverWait(driver, 20).until(EC.presence_of_element_located(card__information))

username = helpers.get_username()

#### Environment settings  #######
if username == 'pi':
    helpers.scroll_to_bottom(driver)
    connection = mysql.connector.connect(**my_secrets.db_config_production)
    #TODO: #Add random dealy
else:
    connection = mysql.connector.connect(**my_secrets.db_config_dev)
    pass 

time.sleep(10)

cards = driver.find_elements(By.CLASS_NAME, "card__information")
print(f'card count: {len(cards)}')

scraped_booz = []

try:    
    for card in cards:
        name = card.find_element(By.CLASS_NAME, 'card__heading').text
        link_element = card.find_element(By.CLASS_NAME, 'full-unstyled-link')
        link = link_element.get_attribute('href')
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
            'sale_price': sale_price,
            'link': link 
        })
except StaleElementReferenceException:
    print("StaleElementReferenceException encountered")
    traceback.print_exc()


finally:
    driver.quit()   

try:
    helpers.get_execution_context
    #helpers.get_username    

    if connection.is_connected():
        cursor = connection.cursor(dictionary=True)

        insert_run_query = """
            INSERT INTO run (username, execution_context) 
            VALUES (%s, %s)"""
        username = helpers.get_username()
        execution_context = helpers.get_execution_context()

        # Execute the query with the parameters
        cursor.execute(insert_run_query, (username, execution_context))
        connection.commit()
        run_id = cursor.lastrowid

        # cursor.execute("""
        # SELECT price, sale_price
        # FROM booz_scraped bs
        # WHERE bs.date_scraped = 
        #     (SELECT MAX(date_scraped)
        #      FROM booz_scraped
        #      WHERE booz_id = %s)
        # AND bs.booz_id = %s
        # """, (booz_id,booz_id,))
        # existing_data = cursor.fetchone()

        cursor.execute("""
                       SELECT b.booz_id, booz_name, bs.price, bs.sale_price 
                       FROM booz b 
                       LEFT JOIN booz_scraped bs 
                       on b.booz_id = bs.booz_id""")
        existing_items = cursor.fetchall()
        booz_names_existing = {item['booz_name']: item['booz_id'] for item in existing_items}

        #booz_names_existing = {row[0]: row[1] for row in result}  # row[0] is booz_id, row[1] is booz_name

        for item in scraped_booz:
            if item['booz_name'] in booz_names_existing:
                booz_id = booz_names_existing[item['booz_name']] #<<< id that correct?
                insert_booz_data(booz_id, item['price'], item['sale_price'], run_id, True)
            else:
                booz_name = item['booz_name']
                link = item['link']
                insert_query = """
                    INSERT INTO booz (booz_name, type, link, run_id)
                    VALUES (%s, %s, %s, %s)
                    """
                cursor.execute(insert_query, (booz_name, booz_page, link, run_id))
                connection.commit()
                booz_id = cursor.lastrowid
                print(f'inserted {booz_name}')
                insert_booz_data(booz_id, item['price'], item['sale_price'], run_id, False)
    else:
        print("Not connected to the database")
    formatted_watchlist = get_watchlist_hits()
    formatted_salelist = get_sale_hits(25)
    formatted_new_or_changed_prices = get_new_or_changed_prices(run_id)
    percent_discounted = get_percent_discounted()
    average_discount = get_average_discount()
    helpers.send_email(formatted_salelist, formatted_new_or_changed_prices, percent_discounted, average_discount, formatted_watchlist)

    

except (Error, mysql.connector.Error) as Error:
    print(f"Error: {Error}")
    traceback.print_exc()
    logger.error(traceback.print_exc())

finally:
    if cursor:
        cursor.close()
    if connection.is_connected():
        connection.close()

logger.info(f"Job finished successfully")
          


    # except Exception as e:
    #     # Rollback in case of any error
    #     connection.rollback()
    #     print(f"An error occurred looping over cards: {e}")
    #     traceback.print_exc()




