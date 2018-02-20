"""Test fixtures."""
from builtins import super

import pytest
from napalm.base.test import conftest as parent_conftest

from napalm.base.test.double import BaseTestDouble

from napalm_s350 import s350


@pytest.fixture(scope='class')
def set_device_parameters(request):
    """Set up the class."""
    def fin():
        request.cls.device.close()
    request.addfinalizer(fin)

    request.cls.driver = s350.S350Driver
    request.cls.patched_driver = PatchedS350Driver
    request.cls.vendor = 's350'
    parent_conftest.set_device_parameters(request)


def pytest_generate_tests(metafunc):
    """Generate test cases dynamically."""
    parent_conftest.pytest_generate_tests(metafunc, __file__)


class PatchedS350Driver(s350.S350Driver):
    """Patched S350 Driver."""

    def __init__(self, hostname, username, password, timeout=60, optional_args=None):
        """Patched S350 Driver constructor."""
        super().__init__(hostname, username, password, timeout, optional_args)

        self.patched_attrs = ['device']
        self.device = FakeS350Device()


class FakeS350Device(BaseTestDouble):
    """S350 device test double."""

    def run_commands(self, command_list, encoding='json'):
        """Fake run_commands."""
        result = list()

        for command in command_list:
            filename = '{}.{}'.format(self.sanitize_text(command), encoding)
            full_path = self.find_file(filename)

            if encoding == 'json':
                result.append(self.read_json_file(full_path))
            else:
                result.append({'output': self.read_txt_file(full_path)})

        return result
