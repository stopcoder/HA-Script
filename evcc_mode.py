# using state_hold to delay the execution for 30 seconds to avoid rapid changes
@state_trigger("sensor.solax_pv_power_total", state_hold=30)
def adjust_evcc_mode():
    pv_power = float(sensor.solax_pv_power_total)
    house_load = float(sensor.solax_house_load)
    threshold = float(input_number.excessive_minimal_power_for_minpv)
    zendure_input = float(sensor.solarflow_800_pro_output_pack_power)
    wallbox_power = float(sensor.evcc_solax_evc_charge_power) * 1000  # convert kW to W

    evcc_mode = select.evcc_solax_evc_mode

    if (evcc_mode == "off" or evcc_mode == "now"):
        return

    diff = pv_power - house_load + zendure_input + wallbox_power

    if diff > threshold:
        select.evcc_solax_evc_mode.select_option("minpv")
    else:
        select.evcc_solax_evc_mode.select_option("pv")
