class CommandSafetyChecker:
    """
    Analyze a command string and return:
    - safe: True/False
    - message: explanation or warning
    """

    dangerous_keywords = [
        "rm -rf", "dd if=", ":(){ :|: & };:", "mkfs", ">: /dev/sda", "shutdown", "reboot", "curl | sh", "wget | sh"
    ]

    def analyze(self, command):
        lower = command.lower()
        for keyword in self.dangerous_keywords:
            if keyword in lower:
                return False, f"⚠️ WARNING: Command contains potentially dangerous operation: `{keyword}`"
        return True, "✅ Command appears safe."
