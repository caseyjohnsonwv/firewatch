import uuid
from .postgres import Park, Ride, CrudUtils


def alert_creation_flow(ride:Ride, park:Park, phone_number:str, wait_time:int, expiration:int) -> str:
    alert_id = str(uuid.uuid4())
    
    active_alerts = CrudUtils.read_alerts(phone_number=phone_number, ride_id=ride.id)
    # don't create alert if ride is not open
    if not ride.is_open:
        return f"Whoops, our data source says {ride.name} is not open right now. Try again later."

    # don't create alert if wait is already short enough
    elif ride.wait_time <= wait_time:
        return f"The wait time for {ride.name} is currently {ride.wait_time} minutes."

    # update alert if user already has one open for this ride
    elif len(active_alerts) > 0:
        CrudUtils.update_alerts(
            phone_number=phone_number, 
            ride_id=ride.id, 
            updates={
                'wait_time': wait_time, 
                'expiration': expiration
            }
        )
        return f"Updated your alert for {ride.name} to a wait under {wait_time} minutes (currently {ride.wait_time})."

    # otherwise write alert to database
    else:
        CrudUtils.create_alert(
            id=alert_id,
            park_id=park.id,
            ride_id=ride.id,
            phone_number=phone_number,
            wait_time=wait_time,
            expiration=expiration,
        )
        return f"Watching {ride.name} at {park.name} for a wait under {wait_time} minutes (currently {ride.wait_time} minutes). Powered by https://queue-times.com/"


def alert_deletion_flow(ride:Ride, park:Park, phone_number:str) -> str:
    alerts = CrudUtils.delete_alerts(phone_number=phone_number, ride_id=ride.id)
    if len(alerts) > 0:
        return f"Your alert for {ride.name} at {park.name} has been deleted."
    else:
        return f"Whoops, you don't have any active alerts for {ride.name} at {park.name}!"