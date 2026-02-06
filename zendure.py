# using state_hold to delay the execution for 30 seconds to avoid rapid changes
@state_trigger("sensor.solax_pv_power_total", state_hold=30)
def adjust_zendure_charging():
    if float(sensor.solax_pv_power_total) < 500:
        number.solarflow_800_pro_input_limit.set_value(0)
        return

    pv_power = float(sensor.solax_pv_power_total)
    house_load = float(sensor.solax_house_load)
    zendure_input = float(sensor.solarflow_800_pro_output_pack_power)
    zendure_2400_input = float(sensor.solarflow_2400_ac_output_pack_power)
    solar_predict = float(sensor.solcast_pv_forecast_forecast_today)
    power_export = float(sensor.solax_grid_export)
    power_import = float(sensor.solax_grid_import)
    solax_battery_discharge = min(0, float(sensor.solax_battery_power_charge))

    diff = pv_power - house_load + zendure_input + zendure_2400_input

    select.solarflow_800_pro_ac_mode.select_option("input")
    select.solarflow_2400_ac_ac_mode.select_option("input")

    if diff < 100 or binary_sensor.evcc_solax_evc_charging == "on":
        # stop charging
        number.solarflow_800_pro_input_limit.set_value(0)
        number.solarflow_2400_ac_input_limit.set_value(0)
    elif solar_predict < 20:
        if sensor.solax_inverter_bdc_status == "Charge":
            number.solarflow_800_pro_input_limit.set_value(0)
            number.solarflow_2400_ac_input_limit.set_value(0)
        else:
            excessive_power = pv_power - house_load + zendure_input + zendure_2400_input
            number.solarflow_800_pro_input_limit.set_value(min(excessive_power, 1000))
            number.solarflow_2400_ac_input_limit.set_value(min(max(excessive_power - 1000, 0), 2000))
    else:
        number.solarflow_800_pro_input_limit.set_value(min(diff, 1000))

        if sensor.solax_inverter_bdc_status == "Charge":
            # provide minimum charging power to solax battery
            solax_battery_power_charge = max(float(sensor.solax_battery_power_charge), 3000)

            excessive_power = pv_power - house_load - solax_battery_power_charge
            zendure_2400_input = zendure_2400_input + excessive_power 
            number.solarflow_2400_ac_input_limit.set_value(min(max(zendure_2400_input, 0), 2000))
        else:
            number.solarflow_2400_ac_input_limit.set_value(min(max(diff - 1000, 0), 2000))


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
