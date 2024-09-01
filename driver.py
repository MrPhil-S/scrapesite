
# Setup the windows Chrome driver
from selenium import webdriver

options = webdriver.ChromeOptions()
#options.add_argument('--headless')  # Run in headless mode
#options.add_argument('--disable-gpu')  # Disable GPU acceleration
driver = webdriver.Chrome(options=options)
#driver = webdriver.Chrome()


# Setup the pi Chrome driver
#from selenium.webdriver.chrome.service import Service
#from selenium.webdriver.chrome.options import Options

# options = Options()
# options.add_argument('--headless')
# options.add_argument('--no-sandbox')
# options.add_argument('--disable-dev-shm-usage')

# service = Service('/usr/bin/chromedriver')
# driver = webdriver.Chrome(service=service, options=options)