# using state_hold to delay the execution for 60 seconds to avoid rapid changes
@state_trigger("sensor.solax_pv_power_total", state_hold=30)
def adjust_zendure_charging():
    pv_power = float(sensor.solax_pv_power_total)
    house_load = float(sensor.solax_house_load)
    zendure_input = float(sensor.solarflow_800_pro_output_pack_power)
    solar_predict = float(sensor.solcast_pv_forecast_forecast_today)

    diff = pv_power - house_load + zendure_input

    if diff < 100 or solar_predict < 20 or binary_sensor.evcc_solax_evc_charging == "on":
        # stop charging
        number.solarflow_800_pro_input_limit.set_value(0)
    else:
        select.solarflow_800_pro_ac_mode.select_option("input")
        number.solarflow_800_pro_input_limit.set_value(min(diff, 1000))
