"""
Removes strikes from a list of prices based on the given Last Traded Price (LTP) ,a specified range and atm_index.
Args:
    l (list):                The list of strike prices.
    ltp (float):             The Last Traded Price (LTP) to use as a reference.
    up_down (int, optional): The range of strikes to keep on both sides of the LTP. Defaults to 1.

Returns:
    list: The filtered list of strikes within the specified range around the LTP.
    
Example:
        strikes = [100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200]
        ltp = 180
        up_down =2
        return: need_strikes =[175, 177.5, 180, 182.5]

"""


def remove_strikes(ticker,strikes_list, ltp, up_down=1):
    if ticker=='SPY':
        for i,strike in enumerate(strikes_list):
            if  (float(strike) % 1==0.5):
                strikes_list.remove(strikes_list[i])
        
    atm_index = None
    needed_strikes = list()
    i = 0
    for strike in strikes_list:
        if strike >= ltp:
            atm_index = i
            needed_strikes = strikes_list[atm_index - up_down:atm_index + up_down]
            break
        i += 1

    return needed_strikes
