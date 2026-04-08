import os


# Keep configuration simple and dependency-free.
APP_NAME: str = os.getenv("APP_NAME", "Alzheimer Assistant Backend")
APP_VERSION: str = os.getenv("APP_VERSION", "0.1.0")

