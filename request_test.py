import requests

import my_secrets

# Base URL (example)
url = my_secrets.product_url

# Headers from Chrome DevTools
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
}

ids = [25554,108159]

# Example of query parameters (if applicable)
params = {"ids":ids,"fulfillment_type":"pickup","location_id":404,"shopify_shop_domain":"bevmo-ca.myshopify.com"}

# Making the request
response = requests.post(url, headers=headers, json=params)

# Checking the response
if response.status_code == 200:
    data = response.json()
    #print(data)
    for p in data['products']:
      if p['id'] in ids and p['quantity'] > 0:
        print(p['title'])
        print(p['offer'])
        print(p['price'])       
        
else:
    print(f"Error: {response.status_code} - {response.text}")
