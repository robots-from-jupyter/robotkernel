# -*- coding: utf-8 -*-
from robotkernel.exceptions import BrokenOpenConnection
import os
import pkg_resources
import re
import time


try:
    import WhiteLibrary
    from robotkernel.selectors_white import PickSnipTool
except ImportError:
    WhiteLibrary = None
    PickSnipTool = None

try:
    import pywintypes
    import win32com.client

    try:
        AutoIt = win32com.client.Dispatch("AutoItX3.Control")
    except pywintypes.com_error:
        AutoIt = None
except ImportError:
    AutoIt = None

try:
    from selenium.common.exceptions import WebDriverException
    from selenium.common.exceptions import InvalidSessionIdException
    from selenium.common.exceptions import TimeoutException
except ImportError:

    class WebDriverException(Exception):
        pass

    class TimeoutException(Exception):
        pass


IS_SELENIUM_SELECTOR_NEEDLE = re.compile(
    r"^id=|^id:|"
    r"^name=|^name:|"
    r"^css=|^css:|"
    r"^tag=|^tag:|"
    r"^link=|^link:|"
    r"^partial link=|^partial link:|"
    r"^xpath=|^xpath:"
)
IS_APPIUM_SELECTOR_NEEDLE = re.compile(r"^id=|^id:|^xpath=|^xpath:")
IS_AUTOIT_SELECTOR_NEEDLE = re.compile(r"^strTitle=|^strControl=")
IS_WHITE_SELECTOR_NEEDLE = re.compile(r"^ae=|^ae:|^template=|^template:")
IS_ID_SELECTOR_NEEDLE = re.compile(r"^id=|^id:")
IS_NAME_SELECTOR_NEEDLE = re.compile(r"^name=|^name:")
IS_CSS_SELECTOR_NEEDLE = re.compile(r"^css=|^css:")
IS_TAG_SELECTOR_NEEDLE = re.compile(r"^tag=|^tag:")
IS_LINK_SELECTOR_NEEDLE = re.compile(r"^link=|^link:|" r"^partial link:|^partial link=")
IS_XPATH_SELECTOR_NEEDLE = re.compile(r"^xpath=|^xpath:")
FORM_TAG_NAMES = ["input", "textarea", "select", "button", "datalist"]
IS_TEXT = re.compile(r"^[\w\s]+$", re.U)

SELECTOR_HIGHLIGHT_STYLE_SCRIPT = """
(function() {
  var node = document.createElement('style');
  node.setAttribute('data-name', 'robotkernel');
  node.innerHTML = '' +
    '[data-robotkernel] {' +
      'outline: 2px solid red !important;' +
      'opacity: 1.0 !important;' +
    '}' +
    '#robotkernel-picker { ' +
      'position: fixed;' +
      'top: 0;' +
      'right: 0;' +
      'bottom: 0;' +
      'left: 0;' +
      'z-index: 9999;' +
      'cursor: crosshair;' +
    '}' +
    '#robotkernel-picker::before { ' +
      'display: block;' +
      'content: "";' +
      'position: absolute;' +
      'top: 0;' +
      'right: 0;' +
      'bottom: 0;' +
      'left: 0;' +
      'background: black;' +
      'opacity: 0.25;' +
      'z-index: -1;' +
    '}' +
    '#robotkernel-picker::after { ' +
      'display: block;' +
      'content: "Click element to select it... (before Selenium timeout).";' +
      'font-size: 12px;' +
      'text-align: center;' +
      'top: 3px;' +
      'margin-right: auto;' +
      'width: 50%;' +
      'margin-left: auto;' +
      'padding: 3px;' +
      'background: white;' +
      'opacity: 1.0;' +
      'border: 1px solid black;' +
    '}';
  document.head.appendChild(node);
})();
"""


def is_selenium_selector(needle):
    return bool(IS_SELENIUM_SELECTOR_NEEDLE.match(needle))


def is_appium_selector(needle):
    return bool(IS_APPIUM_SELECTOR_NEEDLE.match(needle))


def is_autoit_selector(needle):
    return bool(IS_AUTOIT_SELECTOR_NEEDLE.match(needle))


def is_white_selector(needle):
    if PickSnipTool is None:
        return False
    else:
        return bool(IS_WHITE_SELECTOR_NEEDLE.match(needle))


def is_selector(needle):
    return is_selenium_selector(needle) or is_appium_selector(needle)


def get_element_highlight_script(results, old_elements):
    script = ""
    counter = 0
    arguments = []
    elements = [r[1] for r in results]
    for element in old_elements:
        if element not in elements:
            script += f'arguments[{counter:d}].removeAttribute("data-robotkernel");'
            arguments.append(element)
            counter += 1
    for completion, element in results:
        if element not in old_elements:
            script += (
                f"arguments[{counter:d}].setAttribute("
                f'"data-robotkernel", "{completion}");'
            )
            arguments.append(element)
            counter += 1
    return script, arguments


def clear_selector_highlights(driver):
    try:
        script, arguments = get_element_highlight_script(
            [], driver.find_elements_by_css_selector("[data-robotkernel]")
        )
    except InvalidSessionIdException:
        raise BrokenOpenConnection(driver)
    except WebDriverException:
        return
    if script:
        driver.execute_script(script, *arguments)


def get_selector_completions(needle, driver):
    if repr(driver).startswith("<appium.webdriver"):
        return get_appium_selector_completions(needle, driver)
    else:
        return get_selenium_selector_completions(needle, driver)


def get_selenium_selector_completions(needle, driver):
    try:
        # Inject supporting JS and CSS
        styles = 'style[data-name="robotkernel"]'
        if not driver.find_elements_by_css_selector(styles):
            with pkg_resources.resource_stream(
                "robotkernel", "resources/simmerjs/simmer.js"
            ) as fp:
                driver.execute_script(
                    fp.read().decode("utf-8") + SELECTOR_HIGHLIGHT_STYLE_SCRIPT
                )
        can_highlight = True
    except WebDriverException:
        can_highlight = False

    # Get results
    try:
        results = _get_selenium_selector_completions(needle, driver)
    except WebDriverException as e:
        return ["Exception (press esc to clear):", str(e)]

    # Highlight
    if can_highlight:
        script, arguments = get_element_highlight_script(
            results, driver.find_elements_by_css_selector("[data-robotkernel]")
        )
        driver.execute_script(script, *arguments)

    # Return
    return [r[0] for r in results]


def get_appium_selector_completions(needle, driver):
    # Get results
    try:
        results = _get_appium_selector_completions(needle, driver)
    except WebDriverException as e:
        return ["Exception (press esc to clear):", str(e)]

    # Return
    return [r[0] for r in results]


def get_autoit_selector_completions(needle, driver=AutoIt):
    if driver:
        results = _get_autoit_selector_completions(needle, driver)
        return [r for r in results if r]
    else:
        return []


def _get_white_selector_completions(needle, driver):
    if needle in ["ae=", "ae:"]:
        result = driver().pick()
        if result:
            return [
                completion
                for completion in [
                    f'id:{result["AutomationIdProperty"]}',
                    f'text:{result["NameProperty"]}',
                    f'help_text:{result["HelpTextProperty"]}',
                    f'class_name:{result["ClassNameProperty"]}',
                    f'control_type:{result["ControlTypeProperty"]}',
                ]
                if completion.split(":", 1)[-1]
            ]
        else:
            return []
    elif needle in ["template=", "template:"]:
        result = driver().pick(snip=True)
        if result and "bytes" in result:
            filename = f"{int(time.time())}.png"
            with open(os.path.join(os.getcwd(), filename), "bw") as fp:
                fp.write(result["bytes"])
            return [f"template=${{EXECDIR}}{os.path.sep * 2}{filename}"]
        else:
            return []

    else:
        return []


def get_white_selector_completions(needle, driver=PickSnipTool):
    # while only picker is implemented, we don't really use the needle
    if driver:
        results = _get_white_selector_completions(needle, driver)
        return [r for r in results if r]
    else:
        return []


def _get_selenium_selector_completions(needle, driver):
    if IS_ID_SELECTOR_NEEDLE.match(needle):
        return get_selenium_id_selector_completions(needle, driver)
    elif IS_NAME_SELECTOR_NEEDLE.match(needle):
        return get_selenium_name_selector_completions(needle, driver)
    elif IS_CSS_SELECTOR_NEEDLE.match(needle):
        return get_selenium_css_selector_completions(needle, driver)
    elif IS_TAG_SELECTOR_NEEDLE.match(needle):
        return get_selenium_tag_selector_completions(needle, driver)
    elif IS_LINK_SELECTOR_NEEDLE.match(needle):
        return get_selenium_link_selector_completions(needle, driver)
    elif IS_XPATH_SELECTOR_NEEDLE.match(needle):
        return get_selenium_xpath_selector_completions(needle, driver)
    else:
        return []


def _get_appium_selector_completions(needle, driver):
    if IS_ID_SELECTOR_NEEDLE.match(needle):
        return get_appium_id_selector_completions(needle, driver)
    elif IS_XPATH_SELECTOR_NEEDLE.match(needle):
        return get_appium_xpath_selector_completions(needle, driver)
    else:
        return []


def _get_autoit_selector_completions(needle, driver):
    if needle.startswith("strTitle="):
        return get_autoit_win_selector_completions(needle, driver)
    elif needle.startswith("strControl="):
        return get_autoit_control_selector_completions(needle, driver)
    else:
        return []


def get_simmer_matches(elements, driver):
    matches = []
    if elements:
        script = "return ["
        script += ", ".join(
            [f"window.Simmer(arguments[{idx:d}])" for idx in range(len(elements))]
        )
        script += "];"
        results = driver.execute_script(script, *elements)
        for idx in range(len(results)):
            if results[idx]:
                matches.append((f"css:{results[idx]}", elements[idx]))
    return matches


def visible_or_all(results):
    return list(filter(lambda e: e.is_displayed(), results)) or results


def get_selenium_id_selector_completions(needle, driver):
    needle = needle[3:]
    matches = []
    if needle:
        results = driver.find_elements_by_css_selector(
            f'[id="{needle}"]'
        ) or driver.find_elements_by_css_selector(f'[id*="{needle}"]')
    else:
        results = driver.find_elements_by_xpath("//*[@id]")
    for result in visible_or_all(results):
        id_ = result.get_attribute("id")
        matches.append((f"id:{id_}", result))
    return matches


def get_appium_id_selector_completions(needle, driver):
    needle = needle[3:]
    matches = []
    if needle:
        results = driver.find_elements_by_xpath(
            f"//*[" f'contains(@resource-id, "{needle}")' f"]"
        )
    else:
        results = driver.find_elements_by_xpath("//*[@resource-id]")
    for result in visible_or_all(results):
        id_ = result.get_attribute("resource-id")
        matches.append((f'xpath=//*[@resource-id="{id_}"]', result))
    return matches


def get_selenium_name_selector_completions(needle, driver):
    needle = needle[5:]
    matches = []
    if needle:
        results = driver.find_elements_by_css_selector(
            f'[name="{needle}"]'
        ) or driver.find_elements_by_css_selector(f'[name*="{needle}"]')
    else:
        results = driver.find_elements_by_xpath("//*[@name]")
    for result in visible_or_all(results):
        name = result.get_attribute("name")
        matches.append((f"name:{name}", result))
    return matches


def get_selenium_needle_from_user(driver):
    try:
        return (
            driver.execute_async_script(
                """\
var node = document.getElementById('robotkernel-picker') ||
       document.createElement('div');
node.callback = arguments[arguments.length - 1];
node.setAttribute('id', 'robotkernel-picker');
node.setAttribute('onClick',
'this.parentNode.removeChild(this);' +
'this.callback(' +
'Simmer(' +
  'document.elementFromPoint(event.clientX, event.clientY)' +
')' +
');'
);
document.body.appendChild(node);
    """
            )
            or ""
        )
    except TimeoutException:
        driver.execute_script(
            """\
var node = document.getElementById('robotkernel-picker');
if (node) { node.parentNode.removeChild(node); }
"""
        )
        return ""


def get_selenium_css_selector_completions(needle, driver):
    needle = needle[4:]
    unresolved = []
    results = []
    matches = []
    if not needle:
        needle = get_selenium_needle_from_user(driver)
    if needle:
        results = driver.find_elements_by_css_selector(needle)
    for result in visible_or_all(results):
        id_ = result.get_attribute("id")
        if " " in needle:  # always include simmer result for complex needles
            unresolved.append(result)
        if id_:
            matches.append((f"id:{id_}", result))
            continue
        if result.tag_name in FORM_TAG_NAMES and result.get_attribute("name"):
            name = result.get_attribute("name")
            matches.append((f"name:{name}", result))
            continue
        if result.tag_name == "a" and result.text:
            matches.append((f"link:{result.text}", result))
            continue
        if " " not in needle:
            unresolved.append(result)
    matches.extend(get_simmer_matches(unresolved, driver))
    return matches


def get_selenium_tag_selector_completions(needle, driver):
    needle = needle[4:]
    unresolved = []
    results = []
    matches = []
    if needle:
        results = driver.find_elements_by_css_selector(needle)
    for result in visible_or_all(results):
        id_ = result.get_attribute("id")
        if id_:
            matches.append((f"id:{id_}", result))
            continue
        if result.tag_name in FORM_TAG_NAMES:
            name = result.get_attribute("name")
            if name:
                matches.append((f"name:{name}", result))
                continue
        unresolved.append(result)
    matches.extend(get_simmer_matches(unresolved, driver))
    return matches


def get_selenium_link_selector_completions(needle, driver):
    needle = needle[5:]
    matches = []
    if needle:
        results = driver.find_elements_by_partial_link_text(needle)
    else:
        results = driver.find_elements_by_xpath("//a")
    for result in visible_or_all(results):
        if result.text:
            matches.append((f"link:{result.text}", result))
    return matches


def get_selenium_xpath_selector_completions(needle, driver):
    needle = needle[6:]
    results = []
    matches = []
    unresolved = []
    if needle:
        results = driver.find_elements_by_xpath(needle)
    for result in visible_or_all(results):
        id_ = result.get_attribute("id")
        if id_:
            matches.append((f"id:{id_}", result))
            continue
        if result.tag_name in FORM_TAG_NAMES:
            name = result.get_attribute("name")
            if name:
                matches.append((f"name:{name}", result))
                continue
        unresolved.append(result)
    matches.extend(get_simmer_matches(unresolved, driver))
    return matches


def get_appium_xpath_selector_completions(needle, driver):
    needle = needle[6:]
    matches = []
    if IS_TEXT.match(needle):
        results = driver.find_elements_by_xpath(
            f"//*[" f'contains(@text, "{needle}")' f"]"
        )
    elif needle:
        results = driver.find_elements_by_xpath(needle)
    else:
        results = driver.find_elements_by_xpath("//*[@resource-id]")
    for result in visible_or_all(results):
        id_ = result.get_attribute("resource-id")
        if id_:
            matches.append((f'xpath=//*[@resource-id="{id_}"]', result))
            continue
        class_ = result.get_attribute("class")
        text = result.get_attribute("text")
        matches.append((f'xpath=//{class_}[@text="{text}"]', result))
        continue

    return matches


def get_autoit_win_selector_completions(needle, driver):
    needle = needle[len("strTitle=") :].strip()
    matches = []
    if needle:
        results = driver.WinList(needle)[0][1:]
        for result in results:
            matches.append(f"strTitle={result}  strText=")
    else:
        title = driver.WinGetTitle("")
        driver.ToolTip("Select window")
        while True:
            time.sleep(1)
            title_ = driver.WinGetTitle("")
            if title_ != title:
                driver.ToolTip("")
                matches.append(f"strTitle={title_}  strText=")
                break
    return matches


def get_autoit_control_selector_completions(needle, driver):  # noqa: C901
    needle = needle[len("strControl=") :].strip()
    if needle:
        return []

    matches = []
    title = driver.WinGetTitle("")
    driver.ToolTip("Select control")

    while True:
        time.sleep(1)
        title_ = driver.WinGetTitle("")
        if title_ != title:
            driver.ToolTip("")

            pointer_x = driver.MouseGetPosX()
            pointer_y = driver.MouseGetPosY()
            counter = {}
            match = None

            time.sleep(1)

            for class_ in driver.WinGetClassList(title_).split():
                counter.setdefault(class_, 0)
                counter[class_] += 1
                ref = f"{class_}{counter[class_]:d}"
                handle = driver.ControlGetHandle(title_, "", ref)

                x = driver.WinGetPosX(f"[HANDLE:{handle}]")
                if x > pointer_x:  # control begins too late x
                    continue

                w = driver.ControlGetPosWidth(title_, "", ref)
                if (x + w) < pointer_x:  # control ends too early x
                    continue

                y = driver.WinGetPosY(f"[HANDLE:{handle}]")
                if y > pointer_y:  # control begins too late y
                    continue

                h = driver.ControlGetPosHeight(title_, "", ref)
                if (y + h) < pointer_y:  # control ends too late y
                    continue

                if match and w * h > match[1]:
                    continue

                match = [ref, w * h]

            driver.ToolTip("")

            if match:
                matches.append(f"strControl={match[0]}")

            break
    return matches
