from django.test import TestCase
import os
import time

from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.webdriver import WebDriver


class MySeleniumTests(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        opts = Options()
        if os.environ.get("HEADLESS", "1") == "1":
            opts.add_argument("--headless")
        cls.selenium = WebDriver(options=opts)
        # Superusuario
        user = User.objects.create_user("isard", "isard@isardvdi.com", "pirineus")
        user.is_superuser = True
        user.is_staff = True
        user.save()

    # Para que no queden procesos abiertos
    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    # Método para que la ejecución del navegador sea más lenta
    def pause(self):
        segundos = float(os.environ.get("SLOW", "0"))
        if segundos:
            time.sleep(segundos)

    def login(self, username, password):
        self.selenium.get(f"{self.live_server_url}/admin/login/")
        self.selenium.find_element(By.NAME, "username").send_keys(username)
        self.selenium.find_element(By.NAME, "password").send_keys(password)
        self.pause()
        self.selenium.find_element(By.XPATH, "//input[@value='Log in']").click()
        self.pause()

    def logout(self):
        self.selenium.find_element(By.XPATH, "//button[text()='Log out']").click()
        self.pause()

    #Selenium no tiene método para comprobar que un elemento no existe
    def assert_not_exists(self, xpath, msg):
        self.selenium.implicitly_wait(0)
        try:
            self.selenium.find_element(By.XPATH, xpath)
            assert False, msg
        except NoSuchElementException:
            pass
        finally:
            self.selenium.implicitly_wait(5)

    def test_staff_user_login_and_change_password(self):
        # Login como superusuario
        self.login("isard", "pirineus")
        self.selenium.find_element(By.XPATH, "//h1[text()='Site administration']")

        # Crear el usuario
        self.selenium.get(f"{self.live_server_url}/admin/auth/user/add/")
        self.pause()
        self.selenium.find_element(By.ID, "id_username").send_keys("editor")
        self.selenium.find_element(By.ID, "id_password1").send_keys("ClaveSegura_2026!")
        self.selenium.find_element(By.ID, "id_password2").send_keys("ClaveSegura_2026!")
        self.pause()
        
        self.selenium.find_element(By.NAME, "_continue").click()
        self.pause()

        staff = self.selenium.find_element(By.ID, "id_is_staff")
        if not staff.is_selected():
            staff.click()
        self.pause()
        assert not self.selenium.find_element(By.ID, "id_is_superuser").is_selected(), \
            "El usuario no debería ser superusuario"
        self.selenium.find_element(By.NAME, "_save").click()
        self.pause()
        
        self.selenium.find_element(By.XPATH, "//a[text()='editor']")

        # Cerrar sesión y entrar con el nuevo usuario
        self.logout()
        self.login("editor", "ClaveSegura_2026!")
        # Puede entrar en admin
        self.selenium.find_element(By.XPATH, "//h1[text()='Site administration']")
        self.selenium.find_element(By.XPATH, "//button[text()='Log out']")
        self.pause()

        # No tiene ningún permiso
        self.assert_not_exists("//a[text()='Users']", "No debería ver Users")
        self.assert_not_exists("//a[text()='Questions']", "No debería ver Questions")
        self.assert_not_exists("//a[text()='Choices']", "No debería ver Choices")

        # Cambiar la contraseña
        self.selenium.find_element(By.XPATH, "//a[text()='Change password']").click()
        self.pause()
        self.selenium.find_element(By.ID, "id_old_password").send_keys("ClaveSegura_2026!")
        self.selenium.find_element(By.ID, "id_new_password1").send_keys("NuevaClave_2026!")
        self.selenium.find_element(By.ID, "id_new_password2").send_keys("NuevaClave_2026!")
        self.pause()
        self.selenium.find_element(By.XPATH, "//input[@value='Change my password']").click()
        self.selenium.find_element(By.XPATH, "//h1[text()='Password change successful']")
        self.pause()

        # Comprobar que la nueva contraseña funciona
        self.logout()
        self.login("editor", "NuevaClave_2026!")
        self.selenium.find_element(By.XPATH, "//h1[text()='Site administration']")
        self.pause()
