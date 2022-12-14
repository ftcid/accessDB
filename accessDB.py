# TheBlackmad
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import time
import re
from configparser import ConfigParser
from redmail import EmailSender

__TIMEOUT__ = 30
__TIMEOUT_SHORT__ = 10
__SLEEP_TIME__ = 3600 * 24

def config(filename='bankcredentials.ini', section='db'):
    '''
        This routine gets reads the config/init file using the
        library ConfigParser

        Args:
            filename (str): from where retrieve the parameters
            section (str): to retrieve parameters from the filename

        Returns:
            A set with the key:values read for the given section in
            the file.

        Raises:
            Exception: Section not found in the file
            Exception: Error in reading file
    '''

    # Create a parser for reading init file
    # and get the section parameters.
    parser = ConfigParser()
    parser.read(filename)
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))

    # check all variables required are in the file
    try:
        a = db["branch"] + db["account"] + db["subaccount"] + db["pin"] + db["conditions"] + db["email_addr"] + db[
            "password"] + db["email_host"]
    except Exception as e:
        raise Exception("Error in reading file. Parameters incomplete.")

    return db

def toNumber(n):
    '''
        This routine transforms a string representing a number
        to a float number

        Args:
            n (str): representing a number

        Returns:
            a float number

        Raises:
            Exception: string does not represent a number
    '''

    try:
        if n == '':
            return 0.0
        # remove blank spaces
        nn = "".join(n.split())
        nn = nn.replace(',', '')
        num = float(nn)
    except Exception as e:
        raise "String does not represent a number"

    return num

def findBalance(source):
    '''
        Routine: findBalance

        This routine finds the balance part of an html document. This html is
        supposed to be the html provided by the bank in a https call.

        Args:
            source (str): html served by the bank server

        Returns:
            a number represented in a string

        Raises:
            Exception: Overall balance not found!
            Exception: Amount not found!
    '''

    assert source is not None, "Error: object is None"

    html = source.replace('"', '')

    # prepare the regular expression
    # find the balance part
    part = "Overall balance"
    p = re.compile(part, re.IGNORECASE)
    result = p.search(html)
    if result is None:
        raise Exception("Overall balance not found!")
    html = html[result.span()[1]:]

    # now find the balance amount
    part = "[0-9]{0,3},{0,1}[0-9]{0,3}.[0-9][0-9]"
    p = re.compile(part, re.IGNORECASE)
    result = p.search(html)

    if result is None:
        raise Exception("Amount not found!")

    return toNumber(html[result.span()[0]:result.span()[1]])

def sendEmail(email_addr="", password="", host="", port=587, balance=0.0, conditions="False"):
    """
    This routine sends an email to the given mail account

    Args:
        email_addr (str): email address to send to
        password (str): password for the email address
        host (str): mail server to use
        balance (float): balance to inform on the email
        conditions (str): tha should fulfill the balance. This is used to define the message os the mail

    Returns:
        None

    Raises:
        Exception: Email could not be sent. Check email data
    """

    try:
        email = EmailSender(
            host=host,
            port=port,
            username=email_addr,
            password=password
        )

        msgAlert = ""
        if eval(conditions):
            msgAlert = "ALERT: " + conditions

        email.send(
            subject=f"Balance Account: {balance} EUR",
            sender=email_addr,
            receivers=[email_addr],
            text=f"Balance Account: {balance}\n{msgAlert}",
            html="<h1>Hi, </h1><p>Balance Account: " + str(balance) + " EUR</p>" + msgAlert
        )
    except Exception as e:
        raise (f"Email to {email_addr} could not be sent. Check email data")

"""
This program is intended to connect to a bank account from the deutsche bank (GE version in english language) via
HTTPS protocol and via web scrapping technique by using Selenium, retrieve the account balance and send back per 
email through the redmail module.

This will serve as an example on how to alert for a condition to occur, as for instance, to inform about a limit
saldo. The example could be modified to permit a certain action to occur when the condition is fulfilled.

Data of the bank account, email and conditions to be satisfied are stored in a configuration file (bankcredentials.ini)
and read through the module ConfigParser.

"""

if __name__ == "__main__":
    # Collecting data from the Bank
    try:
        print(f"\nReading bank credentials . . .", end=" ")
        db = config(filename="bankcredentials.ini", section="db")
        print(f"[ OK ]")
    except Exception as e:
        print("Error reading the credentials")
        exit(0)

    balance = 0.0
    while True:

        # Creating Firefox and retrieving webpage from the bank
        options = FirefoxOptions()
        options.add_argument("--headless")
        driver = webdriver.Firefox(options=options)
        print("Retrieving web . . .", end=" ")
        driver.get("https://meine.deutsche-bank.de/trxm/db/init.do")
        html = driver.page_source
        print("[ OK ]")

        # Accepting cookies
        # <button role="button" data-testid="uc-accept-all-button" style="margin: 0px 6px;" class="sc-gsDKAQ iDMzf">Agree</button>
        # need to wait for the shadow-root to appear, for accepting the cookies.
        time.sleep(__TIMEOUT_SHORT__)
        print("Accepting Cookies . . .", end=" ")
        driver.execute_script(
            '''return document.querySelector('div#usercentrics-root').shadowRoot.querySelector('button[data-testid="uc-accept-all-button"]')''').click()
        print(f"[ OK ]")

        # Find all inputs and clear them
        # select class name where is input box are present
        WebDriverWait(driver, __TIMEOUT__).until(EC.element_to_be_clickable((By.NAME, "branch")))
        WebDriverWait(driver, __TIMEOUT__).until(EC.element_to_be_clickable((By.NAME, "account")))
        WebDriverWait(driver, __TIMEOUT__).until(EC.element_to_be_clickable((By.NAME, "subaccount")))
        WebDriverWait(driver, __TIMEOUT__).until(EC.element_to_be_clickable((By.NAME, "pin")))
        WebDriverWait(driver, __TIMEOUT__).until(EC.element_to_be_clickable((By.XPATH, "//input[@value='Execute Login']")))
        (branch := driver.find_element(By.NAME, "branch")).clear()
        (account := driver.find_element(By.NAME, "account")).clear()
        (subaccount := driver.find_element(By.NAME, "subaccount")).clear()
        (pin := driver.find_element(By.NAME, "pin")).clear()
        button = driver.find_element(By.XPATH, "//input[@value='Execute Login']")

        # find number of input box and ingress in account web
        branch.send_keys(db["branch"])
        account.send_keys(db["account"])
        subaccount.send_keys(db["subaccount"])
        pin.send_keys(db["pin"])
        print("\nEnter in Deutsche Bank with following data:")
        print(
            f"\t--> ACCOUNT: {branch.get_attribute('value')} {account.get_attribute('value')} {subaccount.get_attribute('value')}\n\t--> CONDITIONS: {db['conditions']}\n")  # {pin.get_attribute('value')}")
        button.click()

        # Wait for the balance page to appear and find the balance of the account
        print(f"Waiting for balance page to appear . . . ", end="")
        wait = WebDriverWait(driver, __TIMEOUT__).until(EC.element_to_be_clickable((By.ID, "rollContainer")))
        print(f"[ OK ]")
        try:
            balance = findBalance(driver.page_source)
            print(f"Balance in account is: {balance} EUR")
        except Exception as e:
            print(f"Error finding the balance. Exception: {str(e)}")

        # logout and close driver
        driver.get("https://meine.deutsche-bank.de/trxm/db/gvo/login/logout.do")
        driver.close()

        # send email
        print(f"Sending Email to {db['email_addr']}")
        try:
            sendEmail(email_addr=db["email_addr"], password=db["password"], host=db["email_host"], balance=balance,
                      conditions=db["conditions"])
        except Exception as e:
            print(f"Error sending email {str(e)}")

        print("Going to sleep . . .")
        time.sleep(__SLEEP_TIME__)

    exit(0)
