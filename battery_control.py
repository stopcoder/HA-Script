from datetime import datetime, timedelta
from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.statistics import (
    statistics_during_period,
)

from tzlocal import get_localzone

def get_consumption_in_last_week(start_time):
    sensor_name = "sensor.daily_house_consumption_new"
    a_week_ago = start_time - timedelta(days=7)

    sensor_history = await get_instance(hass).async_add_executor_job(
        lambda fd=a_week_ago, ld=start_time, sensor=sensor_name: statistics_during_period(
            hass=hass,
            start_time=fd,
            end_time=ld,
            statistic_ids={sensor},
            period="hour",
            units=None,
            types={"state"}
        )
    )

    return sensor_history[sensor_name]

def get_solar_performance_ratio(time):
    sensor_name = "sensor.solax_pv_power_total"
    hours_ago = time - timedelta(hours=3)

    sensor_history = await get_instance(hass).async_add_executor_job(
        lambda fd=hours_ago, ld=time, sensor=sensor_name: statistics_during_period(
            hass=hass,
            start_time=fd,
            end_time=ld,
            statistic_ids={sensor},
            period="hour",
            units=None,
            types={"mean"}
        )
    )

    filtered = [entry for entry in sensor_history[sensor_name] if entry["mean"] > 0]

    if len(filtered) == 0:
        return 1
    else:
        percentages = []
        for entry in filtered:
            date = datetime.fromtimestamp(entry["start"])
            forecast = get_solarforecast(date)
            log.debug(f"date: {date}, forecast: {forecast}")
            if forecast > 0:
                percent = 1 + (entry["mean"] / 1000 - forecast) / forecast
                percentages.append(percent)

        return sum(percentages) / len(percentages)

def get_solarforecast(start_time):
    first_entry_date = sensor.solcast_pv_forecast_forecast_today.detailedForecast[0]["period_start"]
    non_zero_index = -1
    if start_time.date() == first_entry_date.date():
        for index, entry in enumerate(sensor.solcast_pv_forecast_forecast_today.detailedForecast):
            # find the first entry that has a non zero estimate
            if non_zero_index == -1 and entry["pv_estimate"] > 0:
                non_zero_index = index
            property_name = "pv_estimate10" if (index - non_zero_index) < 3 else "pv_estimate"
            if entry["period_start"].timestamp() == start_time.timestamp():
                return (entry[property_name] + sensor.solcast_pv_forecast_forecast_today.detailedForecast[index + 1][property_name]) / 2
    elif start_time.date() == (first_entry_date.date() + timedelta(days=1)):
        for index, entry in enumerate(sensor.solcast_pv_forecast_forecast_tomorrow.detailedForecast):
             # find the first entry that has a non zero estimate
            if non_zero_index == -1 and entry["pv_estimate"] > 0:
                non_zero_index = index
            property_name = "pv_estimate10" if (index - non_zero_index) < 3 else "pv_estimate"
            if entry["period_start"].timestamp() == start_time.timestamp():
                return (entry[property_name] + sensor.solcast_pv_forecast_forecast_tomorrow.detailedForecast[index + 1][property_name]) / 2
    else:
        return 0

def get_consumption_predict(dt, data):
    isWeekend = dt.weekday() > 4
    timestamp = dt.timestamp()
    values = []
    for index, entry in enumerate(data):
        if (timestamp - entry["start"]) % (3600 * 24) == 0 and (datetime.fromtimestamp(entry["start"]).weekday() > 4) == isWeekend:
            # the hourly data is set to 0 at 00:00, it's handled in the 'else' case
            if entry["state"] > data[index - 1]["state"]:
                hour_consumption = entry["state"] - data[index - 1]["state"]
            else:
                hour_consumption = entry["state"]
            values.append(hour_consumption)

    return sum(values) / len(values)

@time_trigger("cron(1 * * * *)")
def determine_battery_mode():
    now = datetime.now(get_localzone())
    entries_to_check = []
    
    # get the price of the current hour in the epex data
    for index, entry in enumerate(sensor.epex_spot_data_net_price.data):
        if datetime.fromisoformat(entry['start_time']) <= now < datetime.fromisoformat(entry['end_time']):
            matching_entry = entry
            entry_index = index
    
    log.debug(f"entry index: {entry_index}")
    log.debug(f"entry: {matching_entry}")

    stop_entry = None
    
    # get the time peroid where the price is cheaper than the price of the current hour
    # for all the hours in between, check whether a potential calculation based on consumption and solar generation needs to be done
    for index, entry in enumerate(sensor.epex_spot_data_net_price.data[entry_index+1:], start=entry_index+1):
        if entry["price_per_kwh"] < matching_entry["price_per_kwh"]:
            stop_entry = entry
            break
        elif entry["price_per_kwh"] > (matching_entry["price_per_kwh"] * 1.2):
            entries_to_check.append(entry)
    
    log.debug(f"stop entry: {stop_entry}")
    
    # it's only needed to determine the battery control mode for the current hour
    # based on the prediction for the next hours before a cheaper price than the
    # current hour appears.
    
    # for hours in entries_to_check
    #  * it should use energy from battery
    #  * check whether there's need to charge => "charge: amount"
    # for the rest including the current hour (current hour is the one that needs to be determined)
    #  * when extra energy needs to be charged: it should not use energy from battery => freeze_discharge
    #  * otherwise, if the energy in battery covers all of the hours => standard
    #  * else => freeze_discharge
    
    start_time = now.replace(minute=0, second=0, microsecond=0)
    if stop_entry:
        end_time = datetime.fromisoformat(stop_entry["start_time"])
    else:
        end_time = datetime.fromisoformat(sensor.epex_spot_data_net_price.data[-1]["end_time"])
    consumption_data = get_consumption_in_last_week(start_time - timedelta(hours=1))
    entry_start_times = [datetime.fromisoformat(entry["start_time"]) for entry in entries_to_check]
    solar_ratio = get_solar_performance_ratio(now)
       
    # Step size of 1 hour
    step = timedelta(hours=1)
    
    battery_capatity = int(sensor.solax_bms_battery_capacity) / 1000 * 0.85
    battery = int(sensor.solax_bms_battery_capacity) / 1000 * (int(sensor.solax_battery_capacity) - 10) / 100
    battery_start = battery
    # track the max level that the battery has been charged to during the timeline
    battery_current_max = battery
    
    # dict structure for record in "records"
    # {
    #    start_time: datetime
    #.   charge_candidate: boolean
    #    battery_before: number (kwh)
    #    battery_after: number (kwh)
    #    house_load: number (kwh)
    #.   solar: number (kwh)
    #.   charge: number (kwh)
    #. }
    
    records = []
    energy_diffs = []
    
    current_time = start_time
    while current_time < end_time:
        average = get_consumption_predict(current_time, consumption_data)
        solar = get_solarforecast(current_time) * solar_ratio
        net_consumption = average - solar
    
        should_check = current_time in entry_start_times
    
        record = {
            "start_time": current_time,
            "charge_candidate": should_check,
            "battery_before": battery,
            "house_load": average,
            "solar": solar
        }
        
        if net_consumption < 0: # battery will be charged
            battery = min(battery - net_consumption, battery_capatity)
            battery_current_max = battery
        elif should_check:
            diff = net_consumption - battery
            if diff > 0:
                can_charge = min(diff, battery_capatity - battery_current_max)
                if can_charge > 0:
                    record["charge"] = can_charge
                    energy_diffs.append(can_charge) # this should be charged into battery at the current hour
                    battery = 0
                    battery_current_max = min(battery_current_max + can_charge, battery_capatity)
            else:
                battery = battery - net_consumption
            
    
        record["battery_after"] = battery
        records.append(record)
        current_time += step

    total_diff = sum(energy_diffs)
    battery_target = min(battery_capatity, total_diff)
    charge_amount = battery_target - battery_start

    if charge_amount > 0:
        mode = f"'charge': {charge_amount} then 'freeze_discharge'"
    elif total_diff > battery_capatity:
        mode = "freeze_discharge"
    else:
        rest = battery_start - total_diff
        needed = sum([record["house_load"] - record["solar"] for record in records[1:] if (not record["charge_candidate"]) and record["house_load"] > record["solar"]])
        current_hour_need = max(0, records[0]["house_load"] - records[0]["solar"])
        if needed == 0:
            mode = f"standard (r: {rest}, n: {needed}), c: {current_hour_need}"
        else:
            mode = f"standard (r: {rest}, n: {needed}), c: {current_hour_need}" if rest >= (needed + current_hour_need) else f"freeze_discharge (r: {rest}, n: {needed}, c: {current_hour_need})"

    state.set("my.battery_control_mode", mode, { "detail": records })
