from ..dependencies import client
from sqlmodel import create_engine

postgresql_secret = client.secrets.kv.read_secret_version(path="postgresql", mount_point="kv", raise_on_deleted_version=True)['data']['data']
engine = create_engine(url=postgresql_secret['neon'], echo=True)