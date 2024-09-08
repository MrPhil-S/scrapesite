import base64
import datetime
import os
import platform
import smtplib
import ssl
import subprocess
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import BytesIO

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from connection import connect_to_db
from my_secrets import gmail_app_pw

#from scrape_site import sale_booz_ids


def get_execution_context():
    return os.getenv('USER_EXECUTION', 'manual')

def get_username():
    if platform.system() == 'Windows':
        return os.getlogin() or os.environ.get('USERNAME', 'unknown')
    else:
        return os.getlogin() or subprocess.getoutput('whoami')


# Function to send email notification
def send_email(formatted_salelist, formatted_new_or_changed_prices, percent_discounted, average_discount, formatted_watchlist=None):
    sender_email = "nopschims@gmail.com"
    receiver_email = "pschims@gmail.com"
    password = gmail_app_pw

    if formatted_watchlist:
        formatted_watchlist_list = ''.join(f'<li>{watchlist_item}</li>' for watchlist_item in formatted_watchlist)
        watchlist_scection = f"""
        <p>Watchlist:</p>
        <ul>
            {formatted_watchlist_list}
        </ul>
        """
    else:
        watchlist_scection = ''

    if formatted_salelist:
        formatted_salelist_list = ''.join(f'<li>{deal_item}</li>' for deal_item in formatted_salelist)
        salelist_section = f"""
        <p>Top Deals:</p>
        <ul>
            {formatted_salelist_list}
        </ul>
        """
    else:
        salelist_section = ''

    if formatted_new_or_changed_prices:
        formatted_new_or_changed_prices_list = ''.join(f'<li>{price_item}</li>' for price_item in formatted_new_or_changed_prices)
        formatted_new_or_changed_prices_section = f"""
        <p>Price Changes for this run ID:</p>
        <ul>
            {formatted_new_or_changed_prices_list}
        </ul>
        """
    else:
        formatted_new_or_changed_prices_section = ''
    # Create the complete HTML body
    body_html = f"""
    <html>
    <head></head>
    <body>
        <h1>Booz update </h1>
        <p><strong>For {time.ctime()}</strong></p>
        <p>Here's what's new:</p>
        <p style="border-bottom: 1px solid black">
            <span style="font-weight: bold">Percent Discounted: </span>
            <span style="font-weight: bold; color: {percent_discounted >= 50 and 'green' or percent_discounted >= 25 and 'orange' or 'red'}">
                {percent_discounted}%</span>
            <span style="margin-left: 2em; font-weight: bold">Average Discount: </span>
            <span style="font-weight: bold; color: {average_discount >= 50 and 'green' or average_discount >= 25 and 'orange' or 'red'}">
                {average_discount}%</span>
        </p>
        {watchlist_scection}
        {salelist_section}
        {formatted_new_or_changed_prices_section}
    </body>
    </html>
    """

    msg = MIMEMultipart()
    msg['Subject'] = 'Booz update!'
    msg['From'] = sender_email
    msg['To'] = receiver_email

    msg.attach(MIMEText(body_html, 'html', 'utf-8'))    

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())

def generate_price_history_chart(booz_id):
    today = datetime.date.today()
    times = f'SELECT CAST(scrape_date AS DATE) scrape_date FROM booz_scraped WHERE booz_id = {booz_id} ORDER BY scrape_date'
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute(times)
    times = cursor.fetchall()
    times.append((today,))
    #times = [time[0] for time in times]
    cursor.reset()

    cursor.execute(f"""SELECT coalesce(sale_price, price) FROM booz_scraped WHERE booz_id = {booz_id} ORDER BY scrape_date""")
    prices = cursor.fetchall()
    prices.append(prices[-1])
    cursor.reset()

    df = pd.DataFrame({'scrape_date': [time[0] for time in times], 'price': [price[0] for price in prices]})

    fig, ax = plt.subplots()
    ax.step(df['scrape_date'], df['price'], where='post')

    for i, (date, price) in enumerate(zip(df['scrape_date'], df['price'])):
        ax.annotate(f"${price:.2f}", (date, price), textcoords="offset points", xytext=(0,10), ha='center')

    ax.xaxis.set_major_locator(mdates.DayLocator())
    ax.set_xticks(df['scrape_date'])
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    ax.set(xlabel='Date', ylabel='Price', title='Price History')

    ax.grid(True)
    #fig.savefig(f'price_history_{booz_id}.png', dpi=300, bbox_inches='tight')

    # Save the chart to a BytesIO object
    img_data = BytesIO()
    fig.savefig(img_data, format='png')
    img_data.seek(0)  # Rewind to the start of the file

    # Encode the image to base64
    img_base64 = base64.b64encode(img_data.getvalue()).decode('utf-8')
    
    return img_base64

#generate_price_history_chart(99)
