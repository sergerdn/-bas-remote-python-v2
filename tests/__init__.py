import logging
import os
import platform
import unittest

from dotenv import load_dotenv

logging.basicConfig(level=logging.DEBUG)

ABS_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))  # root project directory
dotenv_path = os.path.join(ABS_PATH, "tests", ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)

test_remote_script_name = os.environ.get("TEST_REMOTE_SCRIPT_NAME", "TestRemoteControl")
test_remote_script_user = os.environ.get("TEST_REMOTE_SCRIPT_USER", None)
test_remote_script_password = os.environ.get("TEST_REMOTE_SCRIPT_PASSWORD", None)

test_app_working_dir = os.path.join(
    ABS_PATH, ".bas-remote-app-{script_name}".format(script_name=test_remote_script_name.lower())
)

is_windows = platform.system().lower() != "windows"
windows_test = unittest.skipIf(is_windows, "OS not supported: %s" % platform.system())
