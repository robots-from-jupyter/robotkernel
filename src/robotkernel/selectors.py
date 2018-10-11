# -*- coding: utf-8 -*-
import re


try:
    from selenium.common.exceptions import WebDriverException
except ImportError:

    class WebDriverException(Exception):
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


def is_webdriver_selector(needle):
    return bool(IS_SELECTOR_NEEDLE.match(needle))


def get_selector_completions(needle, driver):
    try:
        results = _get_selector_completions(needle, driver)
        for completion, element in results[:5]:
            start = 'outline:10px solid red;transition:outline ease-in-out 0s;'
            end = 'outline:10px solid transparent;transition:outline ease-in-out 1s;'  # noqa: E501
            style = element.get_attribute('style') or ''
            style = style and style.split(end)[0] + ';' or ''
            driver.execute_script(
                f'arguments[0].style="{style}{start}";',
                element,
            )
            driver.execute_script(
                f'arguments[0].style="{style}{end}";',
                element,
            )
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


def get_id_selector_completions(needle, driver):
    needle = needle[3:]
    matches = []
    if needle:
        results = driver.find_elements_by_css_selector(f'[id*="{needle}"')
    else:
        results = driver.find_elements_by_xpath('//*[@id]')
    for result in results:
        id_ = result.get_attribute('id')
        matches.append((f'id:{id_}', result))
    return matches


def get_name_selector_completions(needle, driver):
    needle = needle[5:]
    matches = []
    if needle:
        results = driver.find_elements_by_css_selector(f'[name*="{needle}"')
    else:
        results = driver.find_elements_by_xpath('//*[@name]')
    for result in results:
        name = result.get_attribute('name')
        matches.append((f'name:{name}', result))
    return matches


def get_css_selector_completions(needle, driver):
    needle = needle[4:]
    results = []
    matches = []
    if needle:
        results = driver.find_elements_by_css_selector(needle)
    for result in results:
        id_ = result.get_attribute('id')
        if id_:
            matches.append((f'id:{id_}', result))
            continue
        if result.tag_name in FORM_TAG_NAMES:
            name = result.get_attribute('name')
            if name:
                matches.append((f'name:{name}', result))
                continue
        class_ = result.get_attribute('class')
        if class_ and result.parent in results:
            matches.append((
                f'css:{needle} '
                f'{result.tag_name}.{".".join(class_.split())}',
                result,
            ))
            continue
        elif class_:
            matches.append((
                f'css:'
                f'{result.tag_name}.{".".join(class_.split())}',
                result,
            ))
    return matches


def get_tag_selector_completions(needle, driver):
    needle = needle[4:]
    results = []
    matches = []
    if needle:
        results = driver.find_elements_by_css_selector(f'{needle}')
    for result in results:
        id_ = result.get_attribute('id')
        if id_:
            matches.append((f'id:{id_}', result))
            continue
        if result.tag_name in FORM_TAG_NAMES:
            name = result.get_attribute('name')
            if name:
                matches.append((f'name:{name}', result))
                continue
        class_ = result.get_attribute('class')
        if class_:
            matches.append((
                f'css:{result.tag_name}'
                f'.{".".join(class_.split())}',
                result,
            ))
            continue
    return matches


def get_link_selector_completions(needle, driver):
    needle = needle[5:]
    matches = []
    if needle:
        results = driver.find_elements_by_partial_link_text(needle)
    else:
        results = driver.find_elements_by_xpath('//a')
    for result in results:
        if result.text:
            matches.append((f'link:{result.text}', result))
    return matches


def get_xpath_selector_completions(needle, driver):
    needle = needle[6:]
    results = []
    matches = []
    if needle:
        results = driver.find_elements_by_xpath(needle)
    for result in results:
        id_ = result.get_attribute('id')
        if id_:
            matches.append((f'id:{id_}', result))
            continue
        if result.tag_name in FORM_TAG_NAMES:
            name = result.get_attribute('name')
            if name:
                matches.append((f'name:{name}', result))
                continue
        class_ = result.get_attribute('class')
        if class_:
            matches.append((
                f'css:{result.tag_name}'
                f'.{".".join(class_.split())}',
                result,
            ))
    return matches
