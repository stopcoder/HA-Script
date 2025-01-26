@state_trigger("light.kitchen or light.stove")
def sync_lights(trigger_var=None):
    # Identify which light triggered the change
    changed_light = trigger_var["entity_id"]

    if changed_light == "light.kitchen":
        # Get the kitchen light state and sync the stove light
        kitchen_state = state.get("light.kitchen")
        if kitchen_state == "on":
            service.call("light", "turn_on", entity_id="light.stove")
        else:
            service.call("light", "turn_off", entity_id="light.stove")
    elif changed_light == "light.stove":
        # Get the stove light state and sync the kitchen light
        stove_state = state.get("light.stove")
        if stove_state == "on":
            service.call("light", "turn_on", entity_id="light.kitchen")
        else:
            service.call("light", "turn_off", entity_id="light.kitchen")
