"""Selenium-style fixture test with By locators (AST-edit demo target)."""

from selenium.webdriver.common.by import By


class TestLogin:
    def test_submit(self, driver):
        driver.find_element(By.ID, "login-submit").click()

    def test_cancel(self, driver):
        driver.find_element(By.ID, "login-cancel").click()
