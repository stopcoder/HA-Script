from datetime import datetime
from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.statistics import (
    statistics_during_period
)
from calendar import monthrange

@time_trigger("cron(15 23 * * *)")
def get_full_charge_days():
    # Get current date
    now = datetime.now()

     # First day of the given month at 00:00:00
    first_day_of_month = datetime(now.year, now.month, 1, 0, 0, 0)

    # Get the last day of the month
    last_day = monthrange(now.year, now.month)[1]
    
    # Last moment of the current month
    last_day_of_month = datetime(now.year, now.month, last_day, 23, 59, 59)
    sensor_name = "sensor.solax_battery_capacity"

    sensor_history = await get_instance(hass).async_add_executor_job(
        lambda fd=first_day_of_month, ld=last_day_of_month, sensor=sensor_name: statistics_during_period(
            hass=hass,
            start_time=fd,
            end_time=ld,
            statistic_ids={sensor},
            period="day",
            units=None,
            types={"max"}
        )
    )

    days = [datetime.fromtimestamp(entry["start"]).day for entry in sensor_history[sensor_name] if entry["max"] >= 90]

    state.set("my.battery_full_charge_days", len(days), { "detail": days })
