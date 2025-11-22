from datetime import timedelta, datetime
from tzlocal import get_localzone

@state_trigger("float(sensor.shellypro3em_fce8c0d96704_total_active_power) < 500", state_hold=60)
@time_active("range(02:00:00, 06:00:00)")
def get_time_solcast_sufficient():
    if switch.verdichter_switch_0 == "off":
        return

    if weather.nussweather.temperature < 0:
        log.debug("VerdichterAutomation: temperature below 0°C, skipping turn off")
        return
    
    non_zero_index = -1
    date = None

    for index, entry in enumerate(sensor.solcast_pv_forecast_forecast_today.detailedForecast):
        # find the first entry that has a non zero estimate
        if non_zero_index == -1 and entry["pv_estimate"] > 0:
            non_zero_index = index;
        property_name = "pv_estimate10" if (index - non_zero_index) < 3 else "pv_estimate"
        power = (entry[property_name] + sensor.solcast_pv_forecast_forecast_today.detailedForecast[index + 1][property_name]) / 2
        if power > 2.3:
            date = entry["period_start"]
            log.debug(f"VerdichterAutomation: sufficient power found at {date}")
            break

    if date is not None:
        date = date + timedelta(minutes=30) - timedelta(hours=int(float(input_number.verdichter_sleep_hours)))
        now = datetime.now(get_localzone())

        if now > date:
            service.call("switch", "turn_off", entity_id="switch.verdichter_switch_0")
            log.debug(f"VerdichterAutomation: turned off at {now}")



@state_trigger("float(sensor.solax_pv_power_total) > 2300", state_hold=60, state_hold_false=0)
@time_trigger("cron(0 11 * * *)")
def turn_on_verdichter():
    if switch.verdichter_switch_0 == "off":
        now = datetime.now()
        service.call("switch", "turn_on", entity_id="switch.verdichter_switch_0")
        log.debug(f"VerdichterAutomation: turned on at {now}")
