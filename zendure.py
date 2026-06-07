# Constants for Zendure power limits
ZENDURE_800_MAX_INPUT = 1000
ZENDURE_2400_MAX_INPUT = 2300
ZENDURE_2400_MAX_OUTPUT = 2000

# using state_hold to delay the execution for 30 seconds to avoid rapid changes
@state_trigger("sensor.solax_pv_power_total", state_hold=30)
def adjust_zendure_charging():
    if float(sensor.solax_pv_power_total) < 500:
        number.solarflow_800_pro_input_limit.set_value(0)
        return

    pv_power = float(sensor.solax_pv_power_total)
    house_load = float(sensor.solax_house_load)
    zendure_input = float(sensor.solarflow_800_pro_output_pack_power) - float(sensor.solarflow_800_pro_solar_input_power)
    zendure_2400_input = float(sensor.solarflow_2400_ac_output_pack_power)
    solar_predict = float(sensor.solcast_pv_forecast_forecast_today)
    power_export = float(sensor.solax_grid_export)
    power_import = float(sensor.solax_grid_import)
    # this is either 0 or a negative number
    solax_battery_discharge = min(0, float(sensor.solax_battery_power_charge))

    diff = pv_power - house_load + zendure_input + zendure_2400_input

    select.solarflow_800_pro_ac_mode.select_option("input")
    select.solarflow_2400_ac_ac_mode.select_option("input")

    if diff < 100:
        # stop charging - not enough power
        number.solarflow_800_pro_input_limit.set_value(0)
        number.solarflow_2400_ac_input_limit.set_value(0)
    elif binary_sensor.evcc_solax_evc_charging == "on":
        # wallbox is charging - reserve 4200W for it
        # wallbox charging power is already included in house_load, so we need to add it back and reserve 4200W
        evcc_charge_power = float(sensor.evcc_solax_evc_charge_power) * 1000  # convert kW to W
        adjusted_diff = diff + evcc_charge_power  # add back current wallbox power

        if adjusted_diff <= 4200:
            # not enough power, stop both batteries
            number.solarflow_800_pro_input_limit.set_value(0)
            number.solarflow_2400_ac_input_limit.set_value(0)
        else:
            # enough power - reduce battery charging to give wallbox 4200W
            available_for_batteries = adjusted_diff - 4200

            # Reduce 2400 AC first
            zendure_2400_limit = min(available_for_batteries, ZENDURE_2400_MAX_INPUT)
            number.solarflow_2400_ac_input_limit.set_value(zendure_2400_limit)

            # If there's still power left, allocate to 800
            remaining = available_for_batteries - zendure_2400_limit
            zendure_800_limit = min(max(remaining, 0), ZENDURE_800_MAX_INPUT)
            number.solarflow_800_pro_input_limit.set_value(zendure_800_limit)
    elif solar_predict < 20:
        if sensor.solax_inverter_bdc_status == "Charge" and power_export < 100:
            number.solarflow_800_pro_input_limit.set_value(0)
            number.solarflow_2400_ac_input_limit.set_value(0)
        else:
            excessive_power = pv_power - house_load + zendure_input + zendure_2400_input + solax_battery_discharge
            number.solarflow_800_pro_input_limit.set_value(min(excessive_power, ZENDURE_800_MAX_INPUT))

            # 1 means "calibrating" for connection status
            # 1 means "charging" for pack state
            if sensor.solarflow_800_pro_connection_status != "1" and sensor.solarflow_800_pro_pack_state == "1":
                excessive_power = excessive_power - ZENDURE_800_MAX_INPUT

            number.solarflow_2400_ac_input_limit.set_value(min(max(excessive_power, 0), ZENDURE_2400_MAX_INPUT))
    else:
        number.solarflow_800_pro_input_limit.set_value(min(diff, ZENDURE_800_MAX_INPUT))

        if sensor.solax_inverter_bdc_status == "Charge":
            # limit maximum charging power to solax battery
            solax_battery_power_charge = min(float(sensor.solax_battery_power_charge), 3000)

            excessive_power = pv_power - house_load - solax_battery_power_charge
            zendure_2400_input = zendure_2400_input + excessive_power
            number.solarflow_2400_ac_input_limit.set_value(min(max(zendure_2400_input, 0), ZENDURE_2400_MAX_INPUT))
        else:
            # 1 means "calibrating" for connection status
            # 1 means "charging" for pack state
            if sensor.solarflow_800_pro_connection_status != "1" and sensor.solarflow_800_pro_pack_state == "1":
                diff = diff - ZENDURE_800_MAX_INPUT

            number.solarflow_2400_ac_input_limit.set_value(min(max(diff, 0), ZENDURE_2400_MAX_INPUT))


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


@state_trigger("sensor.shellypro3em_fce8c0d96704_total_active_power", "sensor.dishwasher_power", "sensor.stove_power_total", "sensor.ac_scm50_power", "sensor.shellypmminig3_d0cf13d578f4_power", "sensor.solax_house_load", "sensor.solax_pv_power_total", "input_boolean.solarflow2400_full_cover")
def adjust_ac_2400_discharing():
    if input_boolean.solarflow2400_full_cover == "on":
        # Full-cover mode: cover the entire house deficit (house_load - pv_power_total).
        # house_load already reflects 2400 discharge reducing grid draw, so add own
        # output back to compute the true deficit.
        zendure_2400_output = float(sensor.solarflow_2400_ac_pack_input_power)
        diff = float(sensor.solax_house_load) - float(sensor.solax_pv_power_total) + zendure_2400_output
        if diff > 0:
            # Ceiling to nearest 100W without importing math
            output_power = -(-int(diff) // 100) * 100
            select.solarflow_2400_ac_ac_mode.select_option("output")
            number.solarflow_2400_ac_output_limit.set_value(min(output_power, ZENDURE_2400_MAX_OUTPUT))
        else:
            number.solarflow_2400_ac_output_limit.set_value(0)
        return

    stove_power_w = float(sensor.stove_power_total) * 1000  # convert kW to W
    total = float(sensor.shellypro3em_fce8c0d96704_total_active_power) + float(sensor.dishwasher_power) + stove_power_w + float(sensor.ac_scm50_power) + float(sensor.shellypmminig3_d0cf13d578f4_power)
    soc_800 = float(sensor.solarflow_800_pro_electric_level)

    # When solarflow 800 SOC is low, provide baseline 300W output
    baseline_output = 300 if soc_800 <= 10 else 0

    if float(sensor.solax_pv_power_total) > 300:
        number.solarflow_2400_ac_output_limit.set_value(0)
    elif total < 600:
        number.solarflow_2400_ac_output_limit.set_value(baseline_output)
        if baseline_output > 0:
            select.solarflow_2400_ac_ac_mode.select_option("output")
    else:
        output_power = int(total / 500) * 500
        # Use the higher of baseline or calculated power for big consumers
        output_power = max(output_power, baseline_output)
        select.solarflow_2400_ac_ac_mode.select_option("output")
        number.solarflow_2400_ac_output_limit.set_value(min(output_power, ZENDURE_2400_MAX_OUTPUT))
