from datetime import datetime

@state_trigger("binary_sensor.nuki_eingang_locked == 'off'")
def turn_lights_off():
    now = datetime.now().time()
    
    if (datetime.strptime("14:10:00", "%H:%M:%S").time() <= now <= datetime.strptime("22:58:00", "%H:%M:%S").time()) or \
       (now <= datetime.strptime("14:05:00", "%H:%M:%S").time()):
        
        light.turn_off(entity_id="light.all_lights")
