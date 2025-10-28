import datetime
from django.utils import timezone

def calculate_daily_attendance(punches_for_day):
    """
    Calculates detailed attendance stats from a queryset of one user's punches
    for a single day, which MUST be ordered by 'timestamp'.
    
    Returns a dictionary with:
    - first_punch_in: datetime or None
    - last_punch_out: datetime or None
    - total_time: timedelta (time between first_in and last_out)
    - total_worked: timedelta (sum of all IN-to-OUT periods)
    - total_break: timedelta (total_time - total_worked)
    - is_open: boolean (True if last punch was IN)
    - punches: the original queryset
    """
    stats = {
        'first_punch_in': None,
        'last_punch_out': None,
        'total_time': datetime.timedelta(0),
        'total_worked': datetime.timedelta(0),
        'total_break': datetime.timedelta(0),
        'is_open': False,
        'punches': punches_for_day,
    }

    if not punches_for_day:
        return stats

    # We must reverse the list because the default order is descending
    punches_in_order = list(reversed(punches_for_day.all()))
    
    # Find first 'IN'
    first_in_punch = next((p for p in punches_in_order if p.punch_type == 'IN'), None)
    if not first_in_punch:
        return stats # No 'IN' punches, nothing to calculate
        
    stats['first_punch_in'] = first_in_punch.timestamp

    # Find last 'OUT'
    last_out_punch = next((p for p in reversed(punches_in_order) if p.punch_type == 'OUT'), None)
    if last_out_punch:
        stats['last_punch_out'] = last_out_punch.timestamp

    # Calculate Total Time (Req #3)
    if stats['first_punch_in'] and stats['last_punch_out']:
        if stats['last_punch_out'] > stats['first_punch_in']:
            stats['total_time'] = stats['last_punch_out'] - stats['first_punch_in']

    # Calculate Total Worked (Req #4)
    start_work_time = None
    for punch in punches_in_order:
        if punch.punch_type == 'IN':
            if start_work_time is None:
                start_work_time = punch.timestamp
        elif punch.punch_type == 'OUT':
            if start_work_time is not None:
                stats['total_worked'] += (punch.timestamp - start_work_time)
                start_work_time = None # Reset for next work period
    
    # Check if they are still punched in
    if start_work_time is not None:
        stats['is_open'] = True
        # If the day is still today, calculate worked time up to 'now'
        if first_in_punch.timestamp.date() == timezone.now().date():
            stats['total_worked'] += (timezone.now() - start_work_time)

    # Calculate Total Break (Req #5)
    if stats['total_time'] > stats['total_worked']:
        stats['total_break'] = stats['total_time'] - stats['total_worked']
        
    return stats