import psutil

class SystemHealthSkill:
    def match(self, user_input):
        return any(word in user_input.lower() for word in [
            "health", "system status", "cpu usage", 
            "check memory", "how is my system", "resource usage"
        ])

    def execute(self, user_input):
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        return (
            f"🖥️ System Health:\n"
            f"- CPU Usage: {cpu}%\n"
            f"- RAM: {mem.percent}% used of {round(mem.total / 1e9, 2)} GB\n"
            f"- Disk: {disk.percent}% used of {round(disk.total / 1e9, 2)} GB\n"
        )
