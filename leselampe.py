@state_trigger("int(sensor.leselampe_power_2) < 2")
def turn_off_lampe():
    switch.leselampe_switch_2.turn_off()


@state_trigger("event.7c_c6_b6_64_a0_aa_a0aa_button")
def toggle_lampe():
    attr = state.getattr("event.7c_c6_b6_64_a0_aa_a0aa_button")
    if attr["event_type"] == "double_press":
        switch.leselampe_switch_2.toggle()
