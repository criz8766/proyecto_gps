import os
from pymongo import MongoClient
from pymongo.database import Database

_client = None
_database = None


def get_mongo_client():
    """
    Obtiene el cliente de MongoDB, creándolo si no existe.
    """
    global _client
    if _client is None:
        mongo_host = os.getenv("MONGO_HOST", "mongo")
        mongo_port = int(os.getenv("MONGO_PORT", "27017"))
        mongo_user = os.getenv("MONGO_USER", None)
        mongo_password = os.getenv("MONGO_PASSWORD", None)

        if mongo_user and mongo_password:
            _client = MongoClient(
                host=mongo_host,
                port=mongo_port,
                username=mongo_user,
                password=mongo_password
            )
        else:
            _client = MongoClient(host=mongo_host, port=mongo_port)

    return _client


def get_database() -> Database:
    """
    Obtiene la base de datos de MongoDB para informes.
    """
    global _database
    if _database is None:
        client = get_mongo_client()
        db_name = os.getenv("MONGO_DB", "farmacia_informes")
        _database = client[db_name]

    return _database


def close_connection():
    """
    Cierra la conexión con MongoDB.
    """
    global _client, _database
    if _client:
        _client.close()
        _client = None
        _database = None