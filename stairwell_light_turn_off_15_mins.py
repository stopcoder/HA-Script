STAIRWELL_LIGHT = "light.stairwell"
TIMEOUT = 15 * 60  # 15 minutes in seconds

@state_trigger(f"{STAIRWELL_LIGHT} == 'on' and sun.sun == 'above_horizon'", state_hold=TIMEOUT)
def trigger_light_off():
	service.call("light", "turn_off", entity_id=STAIRWELL_LIGHT)
