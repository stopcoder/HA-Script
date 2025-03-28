import json

@state_trigger("sensor.solax_pv_power_total")
def solar_production():
    data = {
        "text": f"{sensor.solax_pv_power_total}{sensor.solax_pv_power_total.unit_of_measurement}",
        "icon": 49139,
        "duration": 4
    }

    mqtt.publish(topic="awtrix_0b99e4/custom/solar", payload=json.dumps(data))


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
    power = float(sensor.evcc_solax_evc_charge_power) * 1000;

    if power < 1000:
        # delete the custom app
        mqtt.publish(topic="awtrix_0b99e4/custom/wallbox")
    else:
        data = {
            "text": f"{power}W",
            "icon": 52473,
            "duration": 4
        }
        mqtt.publish(topic="awtrix_0b99e4/custom/wallbox", payload=json.dumps(data))
