import atexit, sys
from time import perf_counter

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select


BINDAY_URL = "https://www.westberks.gov.uk/binday"
POSTCODE_ID = "FINDYOURBINDAYS_ADDRESSLOOKUPPOSTCODE"
ADDRESS_ID = "FINDYOURBINDAYS_ADDRESSLOOKUPADDRESS"
RUBBISH_DATE_ID = "FINDYOURBINDAYS_RUBBISHDATE"
RECYCLE_DATE_ID = "FINDYOURBINDAYS_RECYCLINGDATE"

getter = None


def exitHandler():
    if getter is not None:
        getter.close()


class DateGetter(webdriver.Chrome):
    def __init__(self, postcode, address):
        chromeOptions = Options()
        chromeOptions.add_argument("--headless")
        chromeOptions.add_argument('--disable-features=VizDisplayCompositor')
        webdriver.Chrome.__init__(self, options=chromeOptions)

        self.postcode = postcode
        self.address = address

        self.rubbishDate = None
        self.recycleDate = None

    def run(self):
        self.get(BINDAY_URL)
        self.enterPostcode(self.postcode)

        try:
            self.selectAddress(self.address)
        except TimeoutException as e:
            raise(e)

        try:
            self.rubbishDate, self.recycleDate = self.getDates()
        except TimeoutException as e:
            raise(e)

        dates = {
            "rubbish": self.rubbishDate,
            "recycle": self.recycleDate
        }

        sys.exit(dates)
        
    def enterPostcode(self, postcode):
        elem = self.find_element_by_id(POSTCODE_ID)
        elem.clear()
        elem.send_keys(postcode)
        elem.send_keys(Keys.RETURN)

    def selectAddress(self, address, timeout=10):
        elem = Select(self.find_element_by_id(ADDRESS_ID))

        start = perf_counter()

        while not len(elem.options):
            if perf_counter() - start > timeout:
                raise(TimeoutException)

        addressIndex = None

        for idx, option in enumerate(elem.options):
            if address in option.text:
                addressIndex = idx
                break

        elem.select_by_index(addressIndex)

    def getDates(self, timeout=10):
        start = perf_counter()

        rubElem, recElem = None, None

        while True:
            try: 
                rubElem = self.find_element_by_id(RUBBISH_DATE_ID)
                recElem = self.find_element_by_id(RECYCLE_DATE_ID)
            except NoSuchElementException:
                pass

            if "rubbish" in rubElem.text and "recycling" in recElem.text:
                break

            if perf_counter() - start > timeout:
                raise(TimeoutException)

        if rubElem is not None and recElem is not None:
            return (
                rubElem.text.split("Your next rubbish collection day is\n")[1], 
                recElem.text.split("Your next recycling collection day is\n")[1]
            )

        raise(TimeoutException)


if __name__ == "__main__":
    atexit.register(exitHandler)
    getter = DateGetter("POSTCODE", "ADDRESS REGEX").run()



