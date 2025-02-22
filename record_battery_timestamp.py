from datetime import datetime

should_update_empty = False
should_update_full = False

@state_trigger("sensor.solax_battery_capacity")
def record_battery_timestamp(value, old_value):
	global should_update_empty
	global should_update_full
	
	soc = float(value)
	soc_old = float(old_value)
	now = datetime.now()

	if soc == 50:
		if soc_old < 50:
			should_update_full = True
		else:
			should_update_empty = True

	log.debug(f"soc changed: from {soc_old} to {soc}, update_full: {should_update_full}, update_empty: {should_update_empty}")
	
	if soc > 91 and should_update_full:
		input_datetime.set_datetime(entity_id="input_datetime.battery_full_timestamp", datetime=now)
		should_update_full = False
	
	if soc < 11 and should_update_empty:
		input_datetime.set_datetime(entity_id="input_datetime.battery_empty_timestamp", datetime=now)
		should_update_empty = False

