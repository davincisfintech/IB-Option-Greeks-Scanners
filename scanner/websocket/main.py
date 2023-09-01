import asyncio
import json
import os
import threading
from datetime import datetime

import requests
from fastapi import FastAPI, WebSocket, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from main import tickers
from scanner.settings import logger
from scanner.websocket.utilis.dates import get_dates_last_15_business_days

needed_symbols = [ticker.split()[0] for ticker in tickers]
app = FastAPI()
from typing import Annotated


class ConnectionManager:
    def __init__(self):
        self.change_time_frame = None
        self.active_connections: list[WebSocket] = []
        self.finra_data = None
        self.data = {
            'table_data': [],
            'chart_data': {},
            'profile_chart_data': {},
            'by_expiry_chart_data': {},
            'chart_data_vanna': {},
            'profile_chart_data_vanna': {},
            'by_expiry_chart_data_vanna': {},
            'finra_table_data': [],
        }

    async def connect(self, websocket: WebSocket):
        try:
            await websocket.accept()
            self.active_connections.append(websocket)
        except Exception as e:
            logger.debug('error while connecting to websocket!')

    def disconnect(self, websocket: WebSocket):
        try:
            self.active_connections.copy().remove(websocket)
        except ValueError:
            logger.debug(f'value error while removing websocket connection')


    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                self.disconnect(connection)


def start_data_streaming():
    return datetime.datetime.now()


# connection manager
manager = ConnectionManager()


# Home Page
@app.get("/")
async def get():
    if manager.change_time_frame is None:
        return RedirectResponse("/form")
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        html_file_path = os.path.join(script_dir, "index.html")
        with open(html_file_path, "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content, status_code=200)


# Form Page
@app.get("/form")
async def get():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    html_file_path = os.path.join(script_dir, "form.html")
    with open(html_file_path, "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content, status_code=200)


# Handel Submit-Page
@app.post("/submit")
async def get(input_value: Annotated[str, Form()]):
    manager.change_time_frame = input_value
    return RedirectResponse("/", status_code=302)


# finra/get
@app.get("/finra")
async def get():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    html_file_path = os.path.join(script_dir, "finra.html")
    with open(html_file_path, "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content, status_code=200)


# priceTable/websocket
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    try:
        while True:
            await asyncio.sleep(1)
            data_from_scanner = manager.data
            if len(manager.data) < 1:
                pass
            else:
                await manager.broadcast(json.dumps(data_from_scanner))

    except Exception as e:
        logger.exception(e)
    finally:

        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat")


# endpoint
async def fetch_data_from_url(date_str):
    url = f'https://cdn.finra.org/equity/regsho/daily/CNMSshvol{date_str}.txt'
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception if the status code indicates an error

        data = response.text  # Replace .text with .content if you want to get the raw binary response
        return {"data": data}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


# finra/websocket
@app.websocket("/ws/finra/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    date_to_data = {}
    symbol_to_data = {}
    await manager.connect(websocket)

    if manager.finra_data is None:
        latest_date = get_dates_last_15_business_days()[-1]
        for date_str in get_dates_last_15_business_days():
            res = await fetch_data_from_url(date_str)
            if isinstance(res, dict) and ('data' in res and len(res['data'].split()) > 0):
                result = []
                lines = res['data'].split('\n')
                headers = ['Date', 'Symbol', 'ShortVolume', 'ShortExemptVolume', 'TotalVolume', 'Market']

                for line in lines[1:]:
                    values = line.split('|')
                    if len(values) != len(headers):
                        continue
                    if values[1] not in needed_symbols:
                        continue

                    Date, Symbol, ShortVolume, ShortExemptVolume, TotalVolume, Market = values
                    net_vol = round((int(ShortVolume) / int(TotalVolume)), 2)
                    if Symbol not in symbol_to_data:
                        symbol_to_data[Symbol] = {}
                    if Date not in symbol_to_data[Symbol]:
                        symbol_to_data[Symbol][Date] = {}
                    symbol_to_data[Symbol][Date] = net_vol

                    data_dict = dict(zip(headers, values))
                    data_dict['ShortVolume/TotalVolume'] = net_vol
                    result.append(data_dict)

                    if date_str == latest_date:
                        manager.data['finra_table_data'].append(data_dict)

                date_to_data[date_str] = result

        data_to_send = {}
        for symbol in symbol_to_data:
            dates = list()
            vol_values = list()
            for date in symbol_to_data[symbol]:
                dates.append(date)
                vol_values.append(symbol_to_data[symbol][date])
            data_to_send[symbol] = [dates, vol_values]
        manager.finra_data = data_to_send
    data_to_send = manager.finra_data

    try:
        while True:
            await asyncio.sleep(10)
            data = {
                'by_date_bar_chart_data_volume': data_to_send,
                'finra_table_data': manager.data['finra_table_data']
            }
            if len(data) < 1:
                pass
            else:
                await manager.broadcast(json.dumps(data))

    except Exception as e:
        logger.exception(e)
    finally:

        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat")


# step-2
def socket():
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)


# step-1
def socketRun():
    th1 = threading.Thread(target=socket)
    th1.start()
