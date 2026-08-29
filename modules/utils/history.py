from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.statistics import (
    statistics_during_period,
)

def history_during_period(start_time, end_time, sensor_ids, period, types):
    sensor_history = await get_instance(hass).async_add_executor_job(
        lambda sd=start_time, ed=end_time, sensors=sensor_ids, p=period, t=types: statistics_during_period(
            hass=hass,
            start_time=sd,
            end_time=ed,
            statistic_ids=sensors,
            period=p,
            units=None,
            types=t
        )
    )

    return sensor_history
