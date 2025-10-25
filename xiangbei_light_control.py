@event_trigger("zha_event")
def handle_xiangbei_button_event(**kwargs):
    device_ieee = kwargs.get("device_ieee")
    command = kwargs.get("command")

    # Only react to your button
    if device_ieee != "00:15:8d:00:8b:7e:2e:cd":
        return

    if command == "single":
        light.light_buchregal_light.toggle()
