# using state_hold to delay the execution for 30 seconds to avoid rapid changes
@state_trigger("sensor.solax_pv_power_total", state_hold=30)
def adjust_zendure_charging():
    if float(sensor.solax_pv_power_total) < 500:
        number.solarflow_800_pro_input_limit.set_value(0)
        return

    pv_power = float(sensor.solax_pv_power_total)
    house_load = float(sensor.solax_house_load)
    zendure_input = float(sensor.solarflow_800_pro_output_pack_power)
    solar_predict = float(sensor.solcast_pv_forecast_forecast_today)
    power_export = float(sensor.solax_grid_export)
    power_import = float(sensor.solax_grid_import)
    solax_battery_discharge = min(0, float(sensor.solax_battery_power_charge))

    diff = pv_power - house_load + zendure_input

    if diff < 100 or binary_sensor.evcc_solax_evc_charging == "on":
        # stop charging
        number.solarflow_800_pro_input_limit.set_value(0)
    elif solar_predict < 20:
        select.solarflow_800_pro_ac_mode.select_option("input")
        if power_export > 50:
            zendure_input = zendure_input + power_export
            number.solarflow_800_pro_input_limit.set_value(min(zendure_input, 1000))
        elif sensor.solax_inverter_bdc_status == "Charge":
            number.solarflow_800_pro_input_limit.set_value(0)
        else:
            zendure_input = zendure_input - power_import + solax_battery_discharge
            number.solarflow_800_pro_input_limit.set_value(max(0, zendure_input))
    else:
        select.solarflow_800_pro_ac_mode.select_option("input")
        number.solarflow_800_pro_input_limit.set_value(min(diff, 1000))


@state_trigger("float(sensor.solax_pv_power_total) < 300", state_hold=30)
def adjust_zendure_discharging():
    house_load = float(sensor.solax_house_load)
    pv_power = float(sensor.solax_pv_power_total)
    zendure_output = float(sensor.solarflow_800_pro_pack_input_power)

    diff = house_load - pv_power + zendure_output

    if diff < 0: 
        # stop discharging
        number.solarflow_800_pro_output_limit.set_value(0)
    else:
        select.solarflow_800_pro_ac_mode.select_option("output")
        number.solarflow_800_pro_output_limit.set_value(min(diff, 300))


@state_trigger("sensor.shellypro3em_fce8c0d96704_total_active_power")
def adjust_ac_2400_discharing():
    if float(sensor.solax_pv_power_total) > 300 or float(sensor.shellypro3em_fce8c0d96704_total_active_power) < 600:
        number.solarflow_2400_ac_output_limit.set_value(0)
    else:
        output_power = int(float(sensor.shellypro3em_fce8c0d96704_total_active_power) / 500) * 500
        select.solarflow_2400_ac_ac_mode.select_option("output")
        number.solarflow_2400_ac_output_limit.set_value(min(output_power, 2000))
