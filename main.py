from contextlib import asynccontextmanager
import csv
from pathlib import Path
from typing import Union

from fastapi import FastAPI
import gspread
from pydantic_settings import BaseSettings, SettingsConfigDict

DATA_FILE_NAME = "tune_data.csv"

class Settings(BaseSettings):
    blox_data_path: str
    sheet_id: str
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()

data_cache = None

@asynccontextmanager
async def lifespan(_: FastAPI):
    fetch_latest_data()
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/refresh")
def refresh():
    fetch_latest_data()

@app.get("/tunes")
def get_tunes():
    if data_cache is None:
        return {"error": "Data cache is empty. Try refreshing the data."}
    
    tunes = [
        {"title": title, "key": key, "type": type}
        for (title, key, type) in data_cache
    ]
    return {"tunes": tunes}

def get_data_path():
    return Path(settings.blox_data_path) / DATA_FILE_NAME

def fetch_latest_data():
    global data_cache
    service_acct_file = Path(settings.blox_data_path) / "client-secrets.json"
    gc = gspread.service_account(filename=str(service_acct_file))
    sheet = gc.open_by_key(settings.sheet_id)
    worksheet = sheet.get_worksheet(0)
    data_cache = worksheet.get_all_values()[1:]
    
    with open(get_data_path(), mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(data_cache)
    
