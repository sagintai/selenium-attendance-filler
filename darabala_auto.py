from __future__ import annotations

import os
import re
import time
import atexit
import traceback
from typing import Iterable

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    ElementClickInterceptedException,
    ElementNotInteractableException,
    NoSuchElementException,
)
from webdriver_manager.chrome import ChromeDriverManager

# timeouts
PAGE_LOAD_TIMEOUT = 60
ELEMENT_TIMEOUT = 30
OFFCANVAS_TIMEOUT = 20

# globals
_DRIVER: webdriver.Chrome | None = None
_WAIT: WebDriverWait | None = None

load_dotenv()


def _creds() -> tuple[str, str]:
    login = os.getenv("DARABALA_LOGIN")
    password = os.getenv("DARABALA_PASSWORD")
    if not login or not password:
        raise RuntimeError("Missing DARABALA_LOGIN / DARABALA_PASSWORD in .env")
    return login, password


def _accept_alerts(max_checks: int = 3, timeout: int = 3) -> None:
    global _DRIVER
    for _ in range(max_checks):
        try:
            WebDriverWait(_DRIVER, timeout).until(EC.alert_is_present())
            _DRIVER.switch_to.alert.accept()
        except TimeoutException:
            break


def _wait_offcanvas_close_or_refresh() -> None:
    global _DRIVER
    try:
        WebDriverWait(_DRIVER, OFFCANVAS_TIMEOUT).until(
            EC.invisibility_of_element_located((By.ID, "offcanvasTop"))
        )
    except TimeoutException:
        _DRIVER.refresh()
        WebDriverWait(_DRIVER, ELEMENT_TIMEOUT).until(
            EC.presence_of_element_located((By.ID, "layout-menu"))
        )


def _login() -> None:
    global _DRIVER, _WAIT
    login, password = _creds()

    _DRIVER.get("https://darabala.kz/Auth/Login")

    role = _WAIT.until(EC.element_to_be_clickable((By.ID, "selectRoleArea")))
    Select(role).select_by_visible_text("Поставщик (доп.образования)")
    _DRIVER.execute_script("selectLoginRole(arguments[0].value);", role)

    selector = "input#iin, input#iinOrBin, input[name='iin'], input[name='iinOrBin']"
    deadline = time.time() + 12
    iin_input = None

    while time.time() < deadline and iin_input is None:
        try:
            iin_input = _DRIVER.find_element(By.CSS_SELECTOR, selector)
        except Exception:
            for fr in _DRIVER.find_elements(By.TAG_NAME, "iframe"):
                _DRIVER.switch_to.frame(fr)
                found = _DRIVER.find_elements(By.CSS_SELECTOR, selector)
                if found:
                    iin_input = found[0]
                    break
                _DRIVER.switch_to.parent_frame()
            time.sleep(0.2)

    if iin_input is None:
        raise TimeoutException("IIN input not found")

    iin_input.send_keys(login)
    _DRIVER.find_element(By.ID, "pas").send_keys(password)
    _DRIVER.find_element(By.CSS_SELECTOR, "#selectECPArea button").click()

    _accept_alerts(3, 5)
    _WAIT.until(EC.presence_of_element_located((By.ID, "layout-menu")))


def _safe_click(elem, extra_scroll: int = -140) -> None:
    global _DRIVER
    try:
        elem.click()
        return
    except (ElementClickInterceptedException, ElementNotInteractableException):
        pass
    _DRIVER.execute_script("arguments[0].scrollIntoView({block:'center'});", elem)
    _DRIVER.execute_script("window.scrollBy(0, arguments[0]);", extra_scroll)
    time.sleep(0.1)
    _DRIVER.execute_script("arguments[0].click();", elem)


def filler(url: str, dates: Iterable[int]) -> None:
    """
    Opens an attendance page and sets value 'З' for given day numbers.
    Keeps the browser open across consecutive calls.
    """
    global _DRIVER, _WAIT

    if _DRIVER is None:
        _DRIVER = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        _DRIVER.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
        _DRIVER.maximize_window()
        _WAIT = WebDriverWait(_DRIVER, ELEMENT_TIMEOUT)
        atexit.register(lambda: _DRIVER.quit())
        _login()

    try:
        print(f"\n[STEP] Attendance → {url}")
        _DRIVER.get(url)
        _accept_alerts(2, 5)
        _WAIT.until(EC.presence_of_element_located((By.ID, "attendancesArea1")))

        dates_set = set(int(d) for d in dates)
        idx = 0

        while True:
            edit_links = _DRIVER.find_elements(By.XPATH, "//a[starts-with(@id,'editBtn-')]")
            if idx >= len(edit_links):
                print("[DONE] Completed.")
                break

            edit_link = edit_links[idx]
            edit_id = edit_link.get_attribute("id")
            print(f"[CHILD] {idx+1}/{len(edit_links)}  id={edit_id}")

            try:
                row = edit_link.find_element(By.XPATH, "./ancestor::tr")
                dropdown = row.find_element(By.CSS_SELECTOR, "button[data-bs-toggle='dropdown']")
                _DRIVER.execute_script("arguments[0].scrollIntoView({block:'center'});", dropdown)
                _safe_click(dropdown)
                _accept_alerts(1, 2)

                menu = _WAIT.until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "div.dropdown-menu.show"))
                )
                _safe_click(menu.find_element(By.ID, edit_id))

                offcanvas = _WAIT.until(
                    EC.visibility_of_element_located((By.ID, "offcanvasTop"))
                )
                _WAIT.until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "#offcanvasTop select.form-select")
                    )
                )

                cells = offcanvas.find_elements(By.XPATH, ".//div[@class='col-lg-1'][.//label]")
                for col in cells:
                    try:
                        label_text = col.find_element(By.TAG_NAME, "label").text.strip()
                        if not label_text:
                            continue
                        day_num = int(label_text.split()[0])
                    except Exception:
                        continue

                    if day_num not in dates_set:
                        continue

                    try:
                        sel = col.find_element(By.TAG_NAME, "select")
                    except NoSuchElementException:
                        continue

                    _DRIVER.execute_script("arguments[0].scrollIntoView({block:'center'});", sel)
                    Select(sel).select_by_value("З")
                    _DRIVER.execute_script(
                        "arguments[0].dispatchEvent(new Event('change',{bubbles:true}))", sel
                    )

                    oninput = sel.get_attribute("oninput") or ""
                    m = re.search(r"tableAdd\((.*)\)", oninput)
                    if m:
                        p = m.group(1).split(",")
                        p[-1] = "'З'"
                        _DRIVER.execute_script(f"tableAdd({','.join(p)})")

                _accept_alerts(1, 2)
                _safe_click(offcanvas.find_element(By.CSS_SELECTOR, "button.btn-close[data-bs-dismiss]"))
                _accept_alerts(1, 2)
                _wait_offcanvas_close_or_refresh()

            except StaleElementReferenceException:
                print("   [RETRY] DOM changed, retrying.")
                continue
            except Exception as e:
                print(f"   [ERROR] {e}")
                traceback.print_exc()
            finally:
                idx += 1

    except Exception as fatal:
        print(f"[FATAL] {fatal}")
        traceback.print_exc()
