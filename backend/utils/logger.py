import sys
from loguru import logger
import os

os.makedirs("logs", exist_ok=True)

logger.remove()
logger.add(sys.stdout, colorize=True, format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan> - {message}")
logger.add("logs/instaguard.log", rotation="10 MB", retention="7 days", compression="gz")
