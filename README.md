# Price Tracker App

## Overview

This project is designed to **scrape retail sites** to track price changes and notify users of **top deals**. Users can also add individual items to a **watchlist** and receive notifications when their **custom price target** is met.

## Features

### Web Scraping & Data Collection
- 📦 **Scrape retail websites** for price tracking using:
  - **Selenium** for dynamic content scraping.
  - **Requests** for lightweight HTTP requests.
- 🛒 **Track item price history** to analyze trends over time.

### Data Management
- 🗄️ **Store price data** using SQLAlchemy and a relational database.
- 📊 **Graph price history over time** (future enhancement, inspired by CamelCamelCamel).

### API & Backend Services
- 🚀 **FastAPI** powers the backend to handle asynchronous requests efficiently.
- 🔄 **Expose services via API** for integration with front-end applications.

### Notifications & Alerts
- 📧 **Email notifications** for top deals and recent price drops.
- 📱 **Text alerts** when a **watchlisted item** meets a **user-defined price point**.

### Future Enhancements
- 📊 **Interactive dashboards** built with **Streamlit** for data visualization.
- 📈 **Advanced analytics** to help users decide the best time to buy items.

