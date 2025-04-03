@time_trigger("cron(30 2 * * *)")
def reload_solax_modbus():
    homeassistant.reload_config_entry(entry_id="01JK5Z9FNFRH0755Y2YXXXSQRE")
