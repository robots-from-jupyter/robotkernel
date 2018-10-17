# -*- coding: utf-8 -*-
import pkg_resources
import re


try:
    from selenium.common.exceptions import WebDriverException
    from selenium.common.exceptions import TimeoutException
except ImportError:

    class WebDriverException(Exception):
        pass

    class TimeoutException(Exception):
        pass


IS_SELECTOR_NEEDLE = re.compile(
    r'^id=|^id:|'
    r'^name=|^name:|'
    r'^css=|^css:|'
    r'^tag=|^tag:|'
    r'^link=|^link:|'
    r'^partial link=|^partial link:|'
    r'^xpath=|^xpath:',
)
IS_ID_SELECTOR_NEEDLE = re.compile(r'^id=|^id:')
IS_NAME_SELECTOR_NEEDLE = re.compile(r'^name=|^name:')
IS_CSS_SELECTOR_NEEDLE = re.compile(r'^css=|^css:')
IS_TAG_SELECTOR_NEEDLE = re.compile(r'^tag=|^tag:')
IS_LINK_SELECTOR_NEEDLE = re.compile(
    r'^link=|^link:|'
    r'^partial link:|^partial link=',
)
IS_XPATH_SELECTOR_NEEDLE = re.compile(r'^xpath=|^xpath:')
FORM_TAG_NAMES = ['input', 'textarea', 'select', 'button', 'datalist']

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


def is_webdriver_selector(needle):
    return bool(IS_SELECTOR_NEEDLE.match(needle))


def get_element_highlight_script(results, old_elements):
    script = ''
    counter = 0
    arguments = []
    elements = [r[1] for r in results]
    for element in old_elements:
        if element not in elements:
            script += (
                f'arguments[{counter:d}].removeAttribute("data-robotkernel");'
            )
            arguments.append(element)
            counter += 1
    for completion, element in results:
        if element not in old_elements:
            script += (
                f'arguments[{counter:d}].setAttribute('
                f'"data-robotkernel", "{completion}");'
            )
            arguments.append(element)
            counter += 1
    return script, arguments


def clear_selector_highlights(driver):
    script, arguments = get_element_highlight_script(
        [],
        driver.find_elements_by_css_selector('[data-robotkernel]'),
    )
    if script:
        driver.execute_script(script, *arguments)


def get_selector_completions(needle, driver):
    try:
        # Inject supporting JS and CSS
        styles = 'style[data-name="robotkernel"]'
        if not driver.find_elements_by_css_selector(styles):
            with pkg_resources.resource_stream(
                    'robotkernel',
                    'static/simmerjs/simmer.js',
            ) as fp:
                driver.execute_script(
                    fp.read().decode('utf-8') +
                    SELECTOR_HIGHLIGHT_STYLE_SCRIPT,
                )

        # Get results
        results = _get_selector_completions(needle, driver)

        # Highlight
        script, arguments = get_element_highlight_script(
            results,
            driver.find_elements_by_css_selector('[data-robotkernel]'),
        )
        driver.execute_script(script, *arguments)

        # Return
        return [r[0] for r in results]
    except WebDriverException as e:
        return ['Exception (press esc to clear):', str(e)]


def _get_selector_completions(needle, driver):
    if IS_ID_SELECTOR_NEEDLE.match(needle):
        return get_id_selector_completions(needle, driver)
    elif IS_NAME_SELECTOR_NEEDLE.match(needle):
        return get_name_selector_completions(needle, driver)
    elif IS_CSS_SELECTOR_NEEDLE.match(needle):
        return get_css_selector_completions(needle, driver)
    elif IS_TAG_SELECTOR_NEEDLE.match(needle):
        return get_tag_selector_completions(needle, driver)
    elif IS_LINK_SELECTOR_NEEDLE.match(needle):
        return get_link_selector_completions(needle, driver)
    elif IS_XPATH_SELECTOR_NEEDLE.match(needle):
        return get_xpath_selector_completions(needle, driver)
    else:
        return []


def get_simmer_matches(elements, driver):
    matches = []
    if elements:
        script = 'return ['
        script += ', '.join([
            f'window.Simmer(arguments[{idx:d}])'
            for idx in range(len(elements))
        ])
        script += '];'
        results = driver.execute_script(script, *elements)
        for idx in range(len(results)):
            if results[idx]:
                matches.append((f'css:{results[idx]}', elements[idx]))
    return matches


def visible_or_all(results):
    return list(filter(lambda e: e.is_displayed(), results)) or results


def get_id_selector_completions(needle, driver):
    needle = needle[3:]
    matches = []
    if needle:
        results = (
            driver.find_elements_by_css_selector(f'[id="{needle}"]')
            or driver.find_elements_by_css_selector(f'[id*="{needle}"]')
        )
    else:
        results = driver.find_elements_by_xpath('//*[@id]')
    for result in visible_or_all(results):
        id_ = result.get_attribute('id')
        matches.append((f'id:{id_}', result))
    return matches


def get_name_selector_completions(needle, driver):
    needle = needle[5:]
    matches = []
    if needle:
        results = (
            driver.find_elements_by_css_selector(f'[name="{needle}"]')
            or driver.find_elements_by_css_selector(f'[name*="{needle}"]')
        )
    else:
        results = driver.find_elements_by_xpath('//*[@name]')
    for result in visible_or_all(results):
        name = result.get_attribute('name')
        matches.append((f'name:{name}', result))
    return matches


def get_needle_from_user(driver):
    try:
        return driver.execute_async_script(
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
    """,
        ) or ''
    except TimeoutException:
        driver.execute_script(
            """\
var node = document.getElementById('robotkernel-picker');
if (node) { node.parentNode.removeChild(node); }
""",
        )
        return ''


def get_css_selector_completions(needle, driver):
    needle = needle[4:]
    unresolved = []
    results = []
    matches = []
    if not needle:
        needle = get_needle_from_user(driver)
    if needle:
        results = driver.find_elements_by_css_selector(needle)
    for result in visible_or_all(results):
        id_ = result.get_attribute('id')
        if id_:
            matches.append((f'id:{id_}', result))
            continue
        if result.tag_name in FORM_TAG_NAMES:
            name = result.get_attribute('name')
            if name:
                matches.append((f'name:{name}', result))
                continue
        if result.tag_name == 'a' and result.text:
            matches.append((f'link:{result.text}', result))
            continue
        unresolved.append(result)
    matches.extend(get_simmer_matches(unresolved, driver))
    return matches


def get_tag_selector_completions(needle, driver):
    needle = needle[4:]
    unresolved = []
    results = []
    matches = []
    if needle:
        results = driver.find_elements_by_css_selector(needle)
    for result in visible_or_all(results):
        id_ = result.get_attribute('id')
        if id_:
            matches.append((f'id:{id_}', result))
            continue
        if result.tag_name in FORM_TAG_NAMES:
            name = result.get_attribute('name')
            if name:
                matches.append((f'name:{name}', result))
                continue
        unresolved.append(result)
    matches.extend(get_simmer_matches(unresolved, driver))
    return matches


def get_link_selector_completions(needle, driver):
    needle = needle[5:]
    matches = []
    if needle:
        results = driver.find_elements_by_partial_link_text(needle)
    else:
        results = driver.find_elements_by_xpath('//a')
    for result in visible_or_all(results):
        if result.text:
            matches.append((f'link:{result.text}', result))
    return matches


def get_xpath_selector_completions(needle, driver):
    needle = needle[6:]
    results = []
    matches = []
    unresolved = []
    if needle:
        results = driver.find_elements_by_xpath(needle)
    for result in visible_or_all(results):
        id_ = result.get_attribute('id')
        if id_:
            matches.append((f'id:{id_}', result))
            continue
        if result.tag_name in FORM_TAG_NAMES:
            name = result.get_attribute('name')
            if name:
                matches.append((f'name:{name}', result))
                continue
        unresolved.append(result)
    matches.extend(get_simmer_matches(unresolved, driver))
    return matches
