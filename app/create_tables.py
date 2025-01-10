from models import Base  # Import the Base and engine from the models file
from models import engine

# Create the tables in the database
Base.metadata.create_all(bind=engine)
print("Tables created successfully!")