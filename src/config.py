import json
import os

class Config:
    """Application configuration."""
    def __init__(self):
        self.load_config()
        self.REPO_NAME = "bitscon/billy"
        self.REPO_URL = f"https://{self.GITHUB_TOKEN}@github.com/{self.REPO_NAME}.git"
        self.LOCAL_REPO_PATH = "/home/billybs/Projects/billy-local-repo"

    def load_config(self):
        """Load configuration from config.json."""
        with open("src/config.json", "r") as config_file:
            config = json.load(config_file)
        self.TONE = config["tone"]
        self.load_connectors()

    def load_connectors(self):
        """Load connectors from the database."""
        from database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM connectors")
        rows = cursor.fetchall()
        conn.close()
        self.connectors = {row["name"]: dict(row) for row in rows}
        self.NEXTCLOUD_URL = self.connectors.get("nextcloud", {}).get("url", "")
        self.NEXTCLOUD_USERNAME = self.connectors.get("nextcloud", {}).get("username", "")
        self.NEXTCLOUD_PASSWORD = self.connectors.get("nextcloud", {}).get("password", "")
        self.GITHUB_TOKEN = self.connectors.get("github", {}).get("api_key", "")

    def save_config(self):
        """Save configuration to config.json."""
        config = {"tone": self.TONE}
        with open("src/config.json", "w") as config_file:
            json.dump(config, config_file, indent=4)
