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
def send_email(watchlist_items=None, deal_items=None):
    sender_email = "nopschims@gmail.com"
    receiver_email = "pschims@gmail.com"
    password = gmail_app_pw

    if watchlist_items:
        watchlist_items_html = ''.join(f'<li>{watchlist_item}</li>' for watchlist_item in watchlist_items)
        watchlist_html = f"""
        <p>Watchlist:</p>
        <ul>
            {watchlist_items_html}
        </ul>
        """
    else:
        watchlist_html = ''

    if deal_items:
        deal_items_html = ''.join(f'<li>{deal_item}</li>' for deal_item in deal_items)
        deal_html = f"""
        <p>Deals:</p>
        <ul>
            {deal_items_html}
        </ul>
        """
    else:
        deal_html = ''


    # Create the complete HTML body
    body_html = f"""
    <html>
    <head></head>
    <body>
        <h1>Booz update </h1>
        <p><strong>For {time.ctime()}</strong></p>
        {watchlist_html}
        {deal_html}
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
