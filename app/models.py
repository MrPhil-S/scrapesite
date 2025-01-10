from datetime import datetime

from sqlalchemy import (Column, DateTime, ForeignKey, Integer, Numeric, String,
                        create_engine, text)
from sqlalchemy.orm import declarative_base, sessionmaker

from .database import Base
from .my_secrets import dev_sql_alchemy, prod_sql_alchemy


class Booz(Base):
	__tablename__ = 'booz'
	booz_id = Column(Integer, primary_key=True, autoincrement=True)
	booz_name = Column(String(200), nullable=False)
	source_site = Column(String(50), nullable=False)
	type = Column(String(100), nullable=False)
	link = Column(String(255), nullable=False)		
	add_date = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'), nullable=False)
	scrape_method = Column(String(40), nullable=False)		
	product_identifier = Column(String(50))
	watchlist_price = Column(Numeric(8,2))
	watchlist_add_date = Column(DateTime)
	run_id = Column(Integer, ForeignKey('run.run_id'), nullable=False)            

class Booz_scraped(Base):
	__tablename__ = 'booz_scraped'
	booz_scraped_id = Column(Integer, primary_key=True, autoincrement=True)
	booz_id = Column(Integer, ForeignKey('booz.booz_id'), nullable=False)
	price = Column(Numeric(8,2), nullable=False)
	sale_price = Column(Numeric(8,2))
	scrape_date = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'), nullable=False)
	run_id = Column(Integer, ForeignKey('run.run_id'), nullable=False)		

class Run(Base):
	__tablename__ = 'run'
	run_id = Column(Integer, primary_key=True, autoincrement=True)
	start_date = Column(DateTime,  server_default=text('CURRENT_TIMESTAMP'), nullable=False)
	complete_date = Column(DateTime)
	bm_scrape_count = Column(Integer)
	tw_scrape_count = Column(Integer)
	username = Column(String(100), nullable=False)
	execution_context = Column(String(100), nullable=False)


# # Set up the database URL (change username, password, dbname as needed)
# DATABASE_URL = dev_sql_alchemy

# # Create the engine
# engine = create_engine(DATABASE_URL, echo=True)

# # Set up sessionmaker to manage database sessions
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)