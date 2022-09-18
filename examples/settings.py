import logging
import os

from dotenv import load_dotenv

logging.basicConfig(level=logging.DEBUG)

ABS_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))  # root  directory

dotenv_path = os.path.join(ABS_PATH, "examples", ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)

remote_script_name = os.environ.get("TEST_REMOTE_SCRIPT_NAME", "TestRemoteControlV2")
remote_script_user = os.environ.get("TEST_REMOTE_SCRIPT_USER")
remote_script_password = os.environ.get("TEST_REMOTE_SCRIPT_PASSWORD")
working_dir = os.path.join(ABS_PATH, ".bas-remote-app-{script_name}".format(script_name=remote_script_name.lower()))
