from datetime import datetime, timedelta

def date_after_n_days(n):
    if not isinstance(n, int) or n < 0:
        raise ValueError("Input 'n' must be a positive integer.")

    today = datetime.today().strftime("%Y%m%d")
    date = datetime.strptime(today, '%Y%m%d').date()
    day_after_n_days = date + timedelta(days=n)
    day_after_n_days = day_after_n_days.strftime('%Y%m%d')
    return day_after_n_days

def needed_expiries(days_to_expiry_list, expiries):
    list_future_days = []
    for n in days_to_expiry_list:
        try:
            list_future_days.append(date_after_n_days(n))
        except ValueError:
            continue

    needed_expiries = []
    for future_day in list_future_days:
        min_diff = float('inf')
        result = None
        for expiry in expiries:
            try:
                expiry_int = int(expiry)
                future_day_int = int(future_day)
                if expiry_int < future_day_int:
                    continue
                if abs(expiry_int - future_day_int) < min_diff:
                    result = expiry
                    min_diff = abs(expiry_int - future_day_int)
            except ValueError:
                continue
        needed_expiries.append(result)

    return sorted(set(needed_expiries))
