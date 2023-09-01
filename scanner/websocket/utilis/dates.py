

from datetime import datetime, timedelta
def is_weekend(date):
    return date.weekday() in [5, 6]  # Saturday and Sunday have weekday values 5 and 6, respectively.

def get_dates_last_15_business_days():
    date_str=datetime.today().strftime("%Y%m%d")
    
    date_format = "%Y%m%d"
    start_date = datetime.strptime(date_str, date_format)
    
    date_list = []
    delta = timedelta(days=1)
    days_count = 0

    while days_count < 15:
        current_date = start_date - delta
        if not is_weekend(current_date):
            date_list.append(current_date.strftime(date_format))
            days_count += 1
        delta += timedelta(days=1)

    return date_list[::-1]  # Reversing the list to get dates in ascending order.


