import mysql.connector

from my_secrets import db_config


def connect_to_db():
    connection = mysql.connector.connect(**db_config)
    return connection