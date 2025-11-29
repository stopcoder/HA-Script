@time_trigger("cron(0 21 * * *)")
def turn_on_night_lights():
    light.turn_on(entity_id="light.nachtlicht_mia_light", brightness=64, rgb_color=(255, 255, 197))
    light.turn_on(entity_id="light.nachtlicht_xiangbei_light", brightness=64, rgb_color=(255, 255, 197))

@time_trigger("cron(50 23 * * *)")
def turn_off_night_lights():
    light.turn_off(entity_id="light.nachtlicht_mia_light")
    light.turn_off(entity_id="light.nachtlicht_xiangbei_light")
