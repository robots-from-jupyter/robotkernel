# -*- coding: utf-8 -*-
from robot.libraries.BuiltIn import BuiltIn

import inspect


class StatusEventListener:
    ROBOT_LISTENER_API_VERSION = 2

    def __init__(self, callback):
        self.callback = callback

    # noinspection PyUnusedLocal
    def end_keyword(self, name, attributes):
        self.callback(attributes['status'])


class ReturnValueListener:
    ROBOT_LISTENER_API_VERSION = 2

    def __init__(self, callback):
        self.callback = callback
        self.return_value = None

    # noinspection PyUnusedLocal
    def end_keyword(self, name, attributes):
        frame = inspect.currentframe()
        while frame is not None:
            if 'return_value' in frame.f_locals:
                self.return_value = frame.f_locals.get('return_value')
                break
            frame = frame.f_back

    # noinspection PyUnusedLocal
    def start_test(self, name, attributes):
        self.return_value = None

    # noinspection PyUnusedLocal
    def end_test(self, name, attributes):
        self.callback(self.return_value)


# noinspection PyProtectedMember
def get_webdrivers(selenium_library):
    drivers = []
    for idx in range(len(selenium_library._drivers._connections)):
        conn = selenium_library._drivers._connections[idx]
        if conn in selenium_library._drivers._closed:
            continue
        aliases = []
        for alias, idx_ in selenium_library._drivers._aliases.items():
            if (idx + 1) == idx_:
                aliases.append(alias)
        drivers.append(
            dict(
                instance=conn,
                aliases=aliases,
                current=conn == selenium_library._drivers.current,
            ),
        )
    return drivers


# noinspection PyProtectedMember
def set_webdrivers(drivers, selenium_library):
    idx = 1
    for driver in drivers:
        selenium_library._drivers._connections.append(driver['instance'])
        for alias in driver['aliases']:
            selenium_library._drivers._aliases[alias] = idx
        if driver['current']:
            selenium_library._drivers.current = driver['instance']
        idx += 1


class WebdriverConnectionsListener:
    ROBOT_LISTENER_API_VERSION = 2

    def __init__(self, drivers: list):
        self.drivers = drivers

    # noinspection PyUnusedLocal,PyProtectedMember
    def end_suite(self, name, attributes):
        try:
            builtin = BuiltIn()
            try:
                instance = builtin.get_library_instance('SeleniumLibrary')
            except RuntimeError:
                instance = builtin.get_library_instance('Selenium2Library')
            self.drivers.clear()
            self.drivers.extend(get_webdrivers(instance))
            builtin.log(str(self.drivers))
        except RuntimeError:
            pass

    # noinspection PyUnusedLocal
    def start_suite(self, name, attributes):
        try:
            builtin = BuiltIn()
            try:
                instance = builtin.get_library_instance('SeleniumLibrary')
            except RuntimeError:
                instance = builtin.get_library_instance('Selenium2Library')
            set_webdrivers(self.drivers, instance)
            builtin.log(str(self.drivers))
        except RuntimeError:
            pass
