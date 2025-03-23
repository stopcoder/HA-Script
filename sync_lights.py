@state_trigger("light.kitchen or light.stove")
@state_active("input_boolean.sync_kitchen_lights == 'on'")
def sync_lights(trigger_type=None, var_name=None, value=None):
    log.debug(f"sync light from {var_name} with state {value}");
    if var_name == "light.kitchen":
        if value == "on":
            service.call("light", "turn_on", entity_id="light.stove")
        else:
            service.call("light", "turn_off", entity_id="light.stove")
    elif var_name == "light.stove":
        if value == "on":
            service.call("light", "turn_on", entity_id="light.kitchen")
        else:
            service.call("light", "turn_off", entity_id="light.kitchen")
