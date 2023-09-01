# Parameters start

tws_mode = 'Paper'  # Choices Live, Paper. Live if Live account is open and Paper if paper account is open in IB TWS

# Client ID, If one connection running already on particular id
# then specify different id here to establish new connection
client_id = 11
# 'ES FUT CME USD 50 202309' 'SPY STK SMART USD 100' 'SPY STK SMART USD 100'
tickers = ['ES FUT CME USD 50 202309',]  # List of symbols  symbol,sec_type,exch,curr,multiplier,expiry_date=ticker
# 'AAPL STK SMART USD 100'
deltas = [0.50]  # Delta list to get the closest option for each delta in the list

days_to_expiries = [0]  # Days to expiry list for getting options for each of the days to expiry in the list

# Average parameter, if True then calculate average iv of all options else not for stock hv - option iv calculation
# Streaming can be affected if this parameter is true and if total options data stream crosses limit of 100 request.
# because to calculate average of all options higher options data streams required and in case
# if limit exceeds then this will be set to False automatically
avg_ivs = False

# Parameter to specify argument for stock HV Calculation, for ex. Close Close, High Low, Open Close etc
iv_args = 'Close Close'

# Choices 12 or 24. 12 for real time IV and 24 for future predicted IV.
# Note: tick type 12 iv has some irregular fluctuations.
tick_type_iv = 24

# Delay interval in minutes for checking for delta change
delay_in_minutes = 5

# Number of strikes above and below from atm strikes
up_down = 5

# parameter for stock,opt,iv changes
# availabe time_frame
# 1 min	2 mins	3 mins	5 mins	10 mins	15 mins	20 mins	30 mins 1 hour	2 hours	3 hours	4 hours	8 hours 1 day
change_time_frame = None

# Historical Iv (value in days)
change_days = 14

# Results table will keep getting updated on web page table
# use this url to go to web page http://127.0.0.1:8000
# wait for sometime after start so then required contracts can be fetched for streaming
# Data for each symbol will keep getting added after certain seconds as soon as it becomes available
# the symbol format for symbol column in table will be like symbol-call_strike-put_strike.
# so for ex. for spy 400 call and 395 put symbol in column will be SPY-400-395

# Note : Streaming can be affected if number of total options data stream crosses limit of 100 request


# Parameters End


if __name__ == '__main__':
    from scanner.websocket.main import socketRun, manager

    socketRun()
    import time

    time.sleep(2)

    while manager.change_time_frame is None:
        pass
    change_time_frame = manager.change_time_frame
    from scanner.controller import run

    run(tickers=tickers, deltas=deltas, avg_ivs=avg_ivs, iv_args=iv_args,
        days_to_expiries=days_to_expiries, tick_type_iv=tick_type_iv,
        delay_in_minutes=delay_in_minutes, tws_mode=tws_mode,
        client_id=client_id, up_down=up_down,
        change_time_frame=change_time_frame, change_days=change_days)
