import json

@state_trigger("sensor.solax_pv_power_total")
def solar_production(value=None):
    if float(value) > 0:
        data = {
            "text": f"{sensor.solax_pv_power_total}{sensor.solax_pv_power_total.unit_of_measurement}",
            "icon": 49139,
            "duration": 4
        }
        mqtt.publish(topic="awtrix_0b99e4/custom/solar", payload=json.dumps(data))
    else:
        mqtt.publish(topic="awtrix_0b99e4/custom/solar")


@state_trigger("sensor.solax_battery_capacity", state_check_now=True)
def solar_battery():
    capacity = int(sensor.solax_battery_capacity)

    ranges = [30, 50, 70, 90]
    
    index = -1
    for idx, val in enumerate(ranges):
        if val > capacity:
            index = idx
            break
    else:
        index = len(ranges)
    
    data = {
        "text": f"{capacity}%",
        "icon": 6354 + index,
        "duration": 4
    }

    mqtt.publish(topic="awtrix_0b99e4/custom/solar_battery", payload=json.dumps(data))

@state_trigger("sensor.evcc_solax_evc_charge_power", state_check_now=True)
def wallbox():
    power = round(float(sensor.evcc_solax_evc_charge_power), 1);

    if power < 1:
        # delete the custom app
        mqtt.publish(topic="awtrix_0b99e4/custom/wallbox")
    else:
        data = {
            "text": f"{power}kW",
            "icon": 52473,
            "duration": 4
        }
        mqtt.publish(topic="awtrix_0b99e4/custom/wallbox", payload=json.dumps(data))

@state_trigger("sensor.shellypro3em_fce8c0d96704_total_active_power")
def heating_pump_indicator():
    data = None
    if float(sensor.shellypro3em_fce8c0d96704_total_active_power) > 500:
        data = {
            "color": [255, 0, 0]
        }
    else:
        data = {
            "color": [0, 0, 0]
        }
    
    mqtt.publish(topic="awtrix_0b99e4/indicator1", payload=json.dumps(data))
