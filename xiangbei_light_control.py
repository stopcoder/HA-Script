@event_trigger("zha_event")
def handle_xiangbei_button_event(**kwargs):
    device_ieee = kwargs.get("device_ieee")
    command = kwargs.get("command")

    # Only react to your button
    if device_ieee != "00:15:8d:00:8b:7e:2e:cd":
        return

    if command == "single":
        light.light_buchregal_light.toggle()

@state_trigger("event.shelly_blu_button1_934a_button")
def toggle_xiangbei_light():
    attr = state.getattr("event.shelly_blu_button1_934a_button")
    if attr["event_type"] == "press":
        light.xiangbei_licht.toggle()
