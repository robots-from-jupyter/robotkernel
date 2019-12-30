# -*- coding: utf-8 -*-
from robot.errors import DataError
from robot.libdocpkg import LibraryDocumentation
from robot.libraries.BuiltIn import BuiltIn
import inspect


BUILTIN_VARIABLES = (
    "${TEMPDIR}",
    "${EXECDIR}",
    "${/}",
    "${:}",
    "${\\n}",
    "${SPACE}",
    "${True}",
    "${False}",
    "${None}",
    "${null}",
    "${OUTPUT_DIR}",
    "${OUTPUT_FILE}",
    "${REPORT_FILE}",
    "${LOG_FILE}",
    "${DEBUG_FILE}",
    "${LOG_LEVEL}",
    "${PREV_TEST_NAME}",
    "${PREV_TEST_STATUS}",
    "${PREV_TEST_MESSAGE}",
)


class RobotVariablesListener:
    ROBOT_LISTENER_API_VERSION = 2

    def __init__(self, variables: dict):
        self.variables = variables

    # noinspection PyUnusedLocal,PyProtectedMember
    def end_suite(self, name, attributes):
        builtin = BuiltIn()
        self.variables.update(builtin.get_variables(no_decoration=False))

    # noinspection PyUnusedLocal,PyProtectedMember
    def start_suite(self, name, attributes):
        builtin = BuiltIn()
        output_dir = self.variables.get("${OUTPUT_DIR}") or ""
        for name, value in self.variables.items():
            if name in BUILTIN_VARIABLES:
                continue
            if output_dir and isinstance(value, str) and value.startswith(output_dir):
                continue
            try:
                if name.startswith("&{"):
                    if value and hasattr(value, "items"):
                        value = " ".join([f"{k}={v}" for k, v in value.items()])
                        builtin.set_suite_variable(name, value)
                elif name.startswith("@{"):
                    builtin.set_suite_variable(f"${name[1:]}", value)
                else:
                    builtin.set_suite_variable(name, value)
            except AttributeError:
                # AttributeError: 'slice' object has no attribute 'split'
                pass


class RobotKeywordsIndexerListener:
    ROBOT_LISTENER_API_VERSION = 2

    def __init__(self, catalog):
        self.catalog = catalog

    # noinspection PyUnusedLocal
    def library_import(self, alias, attributes):
        name = attributes.get("originalName") or alias
        if alias not in self.catalog["libraries"]:
            self.catalog["libraries"].append(alias)
            try:
                lib_doc = LibraryDocumentation(name)
                self._library_import(lib_doc, alias)
            except DataError:
                pass

    def _library_import(self, lib_doc, alias):
        if isinstance(lib_doc, list):
            keywords = lib_doc
            doc_format = "REST"
        else:
            keywords = lib_doc.keywords
            doc_format = lib_doc.doc_format
        for keyword in keywords:
            keyword.doc_format = doc_format
            self.catalog["builder"].add(
                {"name": keyword.name, "dottedname": f"{alias}.{keyword.name}"}
            )
            self.catalog["keywords"][f"{alias}.{keyword.name}"] = keyword
        if len(self.catalog["keywords"]):
            self.catalog["index"] = self.catalog["builder"].build()

    # noinspection PyUnusedLocal
    def resource_import(self, name, attributes):
        if name not in self.catalog["libraries"]:
            self.catalog["libraries"].append(name)
            try:
                resource_doc = LibraryDocumentation(name)
                self._resource_import(resource_doc.keywords)
            except DataError:
                pass

    def _resource_import(self, keywords):
        for keyword in keywords:
            keyword.doc_format = "REST"
            self.catalog["builder"].add(
                {"name": keyword.name, "dottedname": keyword.name}
            )
            self.catalog["keywords"][keyword.name] = keyword
        if len(self.catalog["keywords"]):
            self.catalog["index"] = self.catalog["builder"].build()

    def _import_from_suite_data(self, suite):
        self._resource_import(suite.resource.keywords)
        try:
            for import_data in suite.resource.imports:
                attributes = {}
                if import_data.type == "Library":
                    alias = import_data.alias or import_data.name
                    attributes["originalName"] = import_data.name
                    self.library_import(alias, attributes)
                else:
                    name = import_data.name
                    self.resource_import(name, attributes)
        except AttributeError:
            pass


# noinspection PyUnusedLocal
class StatusEventListener:
    ROBOT_LISTENER_API_VERSION = 2

    def __init__(self, callback):
        self.callback = callback

    def start_test(self, name, attributes):
        self.callback({"test": name})

    def start_keyword(self, name, attributes):
        self.callback({"keyword": name})


# noinspection PyUnusedLocal
class ReturnValueListener:
    ROBOT_LISTENER_API_VERSION = 2

    def __init__(self, callback):
        self.callback = callback
        self.return_value = None

    def end_keyword(self, name, attributes):
        if "capture" in name.lower() and "screenshot" in name.lower():
            # Intentional hack to not include screenshot keywords, because we
            # can assume their screenshots be embedded into log file and
            # displayed from that.
            return
        frame = inspect.currentframe()
        while frame is not None:
            if "return_value" in frame.f_locals:
                self.return_value = frame.f_locals.get("return_value")
                break
            frame = frame.f_back

    def start_test(self, name, attributes):
        self.return_value = None

    def end_test(self, name, attributes):
        self.callback(self.return_value)


def clear_drivers(drivers, type_):
    remained = []
    for driver in drivers:
        if driver.get("type") != type_:
            remained.append(driver)
    drivers.clear()
    drivers.extend(remained)


# noinspection PyProtectedMember
def get_webdrivers(cache, type_):
    drivers = []
    for idx in range(len(cache._connections)):
        conn = cache._connections[idx]
        if conn in cache._closed:
            continue
        aliases = []
        for alias, idx_ in cache._aliases.items():
            if (idx + 1) == idx_:
                aliases.append(alias)
        drivers.append(
            dict(
                instance=conn,
                aliases=aliases,
                current=conn == cache.current,
                type=type_,
            )
        )
    return drivers


# noinspection PyProtectedMember
def set_webdrivers(drivers, cache, type_):
    idx = 1
    for driver in drivers:
        if driver["type"] != type_:
            continue
        cache._connections.append(driver["instance"])
        for alias in driver["aliases"]:
            cache._aliases[alias] = idx
        if driver["current"]:
            cache.current = driver["instance"]
        idx += 1


class SeleniumConnectionsListener:
    ROBOT_LISTENER_API_VERSION = 2

    def __init__(self, drivers: list):
        self.drivers = drivers

    # noinspection PyUnusedLocal,PyProtectedMember
    def end_suite(self, name, attributes):
        try:
            builtin = BuiltIn()
            try:
                instance = builtin.get_library_instance("SeleniumLibrary")
            except RuntimeError:
                instance = builtin.get_library_instance("Selenium2Library")
            clear_drivers(self.drivers, "selenium")
            self.drivers.extend(get_webdrivers(instance._drivers, "selenium"))
        except RuntimeError:
            pass

    # noinspection PyUnusedLocal,PyProtectedMember
    def start_suite(self, name, attributes):
        try:
            builtin = BuiltIn()
            try:
                instance = builtin.get_library_instance("SeleniumLibrary")
            except RuntimeError:
                instance = builtin.get_library_instance("Selenium2Library")
            set_webdrivers(self.drivers, instance._drivers, "selenium")
        except RuntimeError:
            pass


class JupyterConnectionsListener:
    ROBOT_LISTENER_API_VERSION = 2

    def __init__(self, drivers: list):
        self.drivers = drivers

    # noinspection PyUnusedLocal,PyProtectedMember
    def end_suite(self, name, attributes):
        try:
            builtin = BuiltIn()
            instance = builtin.get_library_instance("JupyterLibrary")
            clear_drivers(self.drivers, "jupyter")
            self.drivers.extend(get_webdrivers(instance._drivers, "jupyter"))
        except RuntimeError:
            pass

    # noinspection PyUnusedLocal,PyProtectedMember
    def start_suite(self, name, attributes):
        try:
            builtin = BuiltIn()
            instance = builtin.get_library_instance("JupyterLibrary")
            set_webdrivers(self.drivers, instance._drivers, "jupyter")
        except RuntimeError:
            pass


class AppiumConnectionsListener:
    ROBOT_LISTENER_API_VERSION = 2

    def __init__(self, drivers: list):
        self.drivers = drivers

    # noinspection PyUnusedLocal,PyProtectedMember
    def end_suite(self, name, attributes):
        try:
            builtin = BuiltIn()
            instance = builtin.get_library_instance("AppiumLibrary")
            clear_drivers(self.drivers, "appium")
            self.drivers.extend(get_webdrivers(instance._cache, "appium"))
        except RuntimeError:
            pass

    # noinspection PyUnusedLocal,PyProtectedMember
    def start_suite(self, name, attributes):
        try:
            builtin = BuiltIn()
            instance = builtin.get_library_instance("AppiumLibrary")
            set_webdrivers(self.drivers, instance._cache, "appium")
        except RuntimeError:
            pass


class WhiteLibraryListener:
    ROBOT_LISTENER_API_VERSION = 2

    def __init__(self, drivers: list):
        self.drivers = drivers

    # noinspection PyUnusedLocal,PyProtectedMember
    def end_suite(self, name, attributes):
        try:
            builtin = BuiltIn()
            instance = builtin.get_library_instance("WhiteLibrary")
            clear_drivers(self.drivers, "white")
            self.drivers.append(
                dict(
                    instance=(
                        getattr(instance, "app", None),
                        getattr(instance, "window", None),
                        getattr(instance, "screenshotter", None),
                    ),
                    aliases=[],
                    current=True,
                    type="white",
                )
            )
        except RuntimeError:
            pass

    # noinspection PyUnusedLocal,PyProtectedMember
    def start_suite(self, name, attributes):
        try:
            builtin = BuiltIn()
            instance = builtin.get_library_instance("WhiteLibrary")
            for driver in self.drivers:
                if driver.get("type") == "white" and driver.get("current"):
                    setattr(instance, "app", driver["instance"][0])
                    setattr(instance, "window", driver["instance"][1])
                    setattr(instance, "screenshotter", driver["instance"][2])
        except RuntimeError:
            pass
