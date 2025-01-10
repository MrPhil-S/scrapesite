import matplotlib.pyplot as plt
import mysql.connector  # Assuming you are using MySQL
import pandas as pd

from connection import connect_to_db  # Connect to MySQL connection.

db_connection = connect_to_db()


# Connect to your MySQL database



# Fetch data from MySQL
query = """
    SELECT 
        DATE(scrape_date) AS sale_date,
        COUNT(DISTINCT booz_id) AS total_booz_ids,
        COUNT(DISTINCT CASE WHEN sale_price IS NOT NULL THEN booz_id END) AS sale_booz_ids,
        ROUND(
            100 * COUNT(DISTINCT CASE WHEN sale_price IS NOT NULL THEN booz_id END) / COUNT(DISTINCT booz_id),
            2
        ) AS sale_percentage
    FROM booz_scraped
    GROUP BY DATE(scrape_date)
    ORDER BY sale_date;
"""
df = pd.read_sql(query, con=db_connection)

# Close the database connection
db_connection.close()

# Plotting
plt.figure(figsize=(10, 6))
plt.plot(df['sale_date'], df['sale_percentage'], marker='o', linestyle='-', color='b')
plt.title('Percentage of Distinct Booz IDs on Sale Over Time')
plt.xlabel('Date')
plt.ylabel('Sale Percentage')
plt.xticks(rotation=45)
plt.grid(True)
plt.tight_layout()
plt.show()
