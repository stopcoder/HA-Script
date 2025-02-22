from datetime import datetime
from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.statistics import (
    statistics_during_period,
)
from calendar import monthrange

def get_month_statistics(year, month, sensor_names):
    # First day of the given month at 00:00:00
    first_day_of_month = datetime(year, month, 1, 0, 0, 0)

    # Get the last day of the month
    last_day = monthrange(year, month)[1]
    
    # Last moment of the current month
    last_day_of_month = datetime(year, month, last_day, 23, 59, 59)

    sensor_history = await get_instance(hass).async_add_executor_job(
        lambda fd=first_day_of_month, ld=last_day_of_month, sensors=sensor_names: statistics_during_period(
            hass=hass,
            start_time=fd,
            end_time=ld,
            statistic_ids=sensors,
            period="day",
            units=None,
            types={"state"}
        )
    )

    extracted_data = {name: [entry["state"] for entry in values] for name, values in sensor_history.items()}
    return extracted_data

@time_trigger("cron(59 23 * * *)")
def monthly_autarkie():
    now = datetime.now()
    
    # Define the sensor entity ID
    sensor_house_consumption = "sensor.daily_house_consumption_new"
    sensor_grid_import = "sensor.daily_grid_import_new"
    
    data = get_month_statistics(now.year, now.month, {sensor_house_consumption, sensor_grid_import})
    
    consumption_total = sum(data[sensor_house_consumption])
    import_total = sum(data[sensor_grid_import])
    state.set("my.monthly_autarkie", f"{(consumption_total - import_total) / consumption_total:.2%}")
