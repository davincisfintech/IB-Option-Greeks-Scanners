import asyncio
import threading
import time

from scanner.client.ib import TradingApp
from scanner.settings import logger
from scanner.streaming.find_deltas import FindDeltas
from scanner.streaming.scan import Scan
from scanner.streaming.stocks_iv import IvBetaCalculation
from scanner.streaming.stream_contract_chain import StreamOptionchain
from scanner.streaming.stream_deltas import StreamDeltas
from scanner.streaming.update_streaming_key import UpdateStremingKeyInContractChain


def run(tickers, client_id, tws_mode, deltas, avg_ivs, iv_args, days_to_expiries, tick_type_iv,
        delay_in_minutes, up_down, change_time_frame, change_days):
    def websocket_con():
        app.run()

    subscribed = False
    up_down = up_down
    app = TradingApp(tickers=tickers, deltas=deltas, up_down=up_down, days_to_expiries=days_to_expiries,
                     tick_type_iv=tick_type_iv, delay_in_minutes=delay_in_minutes)

    socket_port = 7497 if tws_mode.lower() == 'paper' else 7496
    app.connect("127.0.0.1", socket_port, clientId=client_id)
    con_thread = threading.Thread(target=websocket_con, daemon=True)
    con_thread.start()
    time.sleep(5)
    logger.info('server connected!')

    app.stock_ltp()
    while len(app.tickers) != len(app.ltp):
        pass
    app.get_contract_ids()
    app.get_contract_chain()

    iv_beta_obj = IvBetaCalculation(app=app, tickers=tickers, iv_args=iv_args)
    iv_beta_obj.get_ivs()
    iv_beta_obj.calculate_beta()

    async def run_instance(obj, delay=None):
        while True:
            obj.run()
            if delay:
                await asyncio.sleep(delay)

    async def logic():
        obj_streaming_contract_chain = StreamOptionchain(app=app)
        obj_update_streming_key_in_contract_chain = UpdateStremingKeyInContractChain(app=app)
        obj_find_deltas = FindDeltas(app=app, change_time_frame=change_time_frame, change_days=change_days)
        obj_stream_deltas = StreamDeltas(app=app)
        obj_scan = Scan(app=app, avg_ivs=avg_ivs)

        while True:
            task_streming_key_in_contract_chain = run_instance(obj_update_streming_key_in_contract_chain, delay=10)
            task_find_deltas = run_instance(obj_find_deltas, delay=10)  # change
            task_stream_deltas = run_instance(obj_stream_deltas, delay=10)
            task_scan = run_instance(obj_scan, delay=1)
            task_streaming_contract_chain = run_instance(obj_streaming_contract_chain,
                                                         delay=int(app.delay_in_minutes * 60))
            await asyncio.gather(task_streaming_contract_chain, task_streming_key_in_contract_chain, task_find_deltas,
                                 task_stream_deltas, task_scan)

    asyncio.run(logic())
