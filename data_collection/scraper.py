import logging
import re
import time
from datetime import date

import numpy as np
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm


# Set up logging configuration
logging.basicConfig(level=logging.INFO)


class WebDriverManager:
    """Manage the Selenium WebDriver and its configurations."""

    def __init__(self):
        """
        Initialize the WebDriverManager with Chrome options.

        Sets up the Chrome options, including maximizing the window and using a random user agent.
        """
        self._options = webdriver.ChromeOptions()
        self._options.add_argument("--start-maximized")
        self._options.add_argument(f"user-agent={UserAgent().chrome}")

    def create_driver(self) -> webdriver.Chrome:
        """
        Create and return a new WebDriver instance.

        :return: A new instance of Chrome WebDriver with predefined options.
        """
        return webdriver.Chrome(options=self._options)


class GrailedLoginManager:
    """Handle the login process to Grailed.com."""

    def __init__(self, driver: webdriver, email: str, password: str, timeout: int = 60):
        """
        Initialize the GrailedLoginManager.

        :param driver: The Selenium WebDriver instance.
        :param email: The email address for logging into Grailed.
        :param password: The password for logging into Grailed.
        :param timeout: Maximum time to wait for elements to be clickable (in seconds).
        """
        self.driver = driver
        self.email = email
        self.password = password
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)

    def login(self) -> bool:
        """
        Perform login to Grailed and return success status.

        :return: True if login is successful, False otherwise.
        """
        self.driver.get("https://www.grailed.com/")
        GrailedScraper.uniform_sleep()

        if not self._accept_privacy_policy():
            return False

        if not self._click_login():
            return False

        if not self._enter_credentials_and_submit():
            return False

        if not self.driver.current_url == "https://www.grailed.com/":
            return False

        self.logger.info("Successfully logged in")
        return True

    def _accept_privacy_policy(self) -> bool:
        """
        Accept the privacy policy if prompted.

        :return: True if the privacy policy is accepted, False otherwise.
        """
        try:
            policy_button = WebDriverWait(self.driver, self.timeout).until(
                ec.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            for _ in range(2):  # Double-click to hide privacy settings window
                policy_button.click()
                GrailedScraper.uniform_sleep()
            return True
        except TimeoutException:
            self.logger.error("Failed to find accept privacy settings button")
            self.driver.close()
            return False

    def _click_login(self) -> bool:
        """
        Click the login link.

        :return: True if the login link is clicked successfully, False otherwise.
        """
        try:
            login_link = WebDriverWait(self.driver, self.timeout).until(
                ec.element_to_be_clickable((By.LINK_TEXT, "Log in"))
            )
            login_link.click()
            GrailedScraper.uniform_sleep()
            return True
        except TimeoutException:
            self.logger.error("Failed to find login link")
            self.driver.close()
            return False

    def _enter_credentials_and_submit(self) -> bool:
        """
        Enter login credentials and submit the login form.

        :return: True if login credentials are submitted successfully, False otherwise.
        """
        try:
            login_with_email_button = WebDriverWait(self.driver, self.timeout).until(
                ec.element_to_be_clickable(
                    (By.CSS_SELECTOR, "[data-cy='login-with-email']")
                )
            )
            login_with_email_button.click()
            GrailedScraper.uniform_sleep()

            credentials = {"email": self.email, "password": self.password}
            for field, value in credentials.items():
                input_field = self.driver.find_element(By.ID, field)
                input_field.clear()  # Clear the field before sending keys
                input_field.send_keys(value)
            GrailedScraper.uniform_sleep()

            login_button = WebDriverWait(self.driver, self.timeout).until(
                ec.element_to_be_clickable(
                    (By.CSS_SELECTOR, "[data-cy='auth-login-submit']")
                )
            )
            login_button.click()
            time.sleep(30)  # Extra time for handling CAPTCHA
            return self.driver.current_url == "https://www.grailed.com/"
        except TimeoutException:
            self.logger.error("Timeout occurred while trying to log in")
            return False
        except NoSuchElementException as e:
            self.logger.error(f"Element not found during login process: {str(e)}")
            return False


class GrailedScraper:
    """Main class for scraping Grailed listings."""

    def __init__(self, email: str, password: str):
        """
        Initialize the GrailedScraper.

        :param email: The email address for logging into Grailed.
        :param password: The password for logging into Grailed.
        """
        self.base_url = "https://www.grailed.com/"
        self.email = email
        self.password = password
        self.ua = UserAgent()  # UserAgent for generating random user agents
        self.logger = logging.getLogger(__name__)
        self.driver_manager = WebDriverManager()  # Get Chrome WebDriver instance

    @staticmethod
    def uniform_sleep() -> None:
        """Sleep for a random duration between 1 and 10 seconds to mimic human interaction."""
        time.sleep(np.random.uniform(1, 10))

    @staticmethod
    def _collect_cover_images(driver, n_listings: int) -> list[str]:
        """
        Collect cover image links.

        :param driver: The Selenium WebDriver instance.
        :param n_listings: The number of listings to collect.
        :return: A list of cover image URLs.
        """
        cover_imgs_links = driver.find_elements(
            By.CLASS_NAME, "Image-module__crop___nWp1j"
        )[:n_listings]
        return [link.get_attribute("srcset").split()[0] for link in cover_imgs_links]

    @staticmethod
    def get_image(image_link: str) -> bytes | dict:
        """
        Retrieve an image from the given link.

        :param image_link: The URL of the image.
        :return: The image content as bytes if successful, or a dictionary with error details.
        """
        try:
            image = requests.get(image_link)
            if not image.ok:
                return {"error": "HTTPError", "status_code": image.status_code}
            return image.content
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to retrieve image from {image_link}: {e}")
            return {"error": e.__class__.__name__, "message": str(e)}

    @staticmethod
    def _handle_errors(errors, listing_data, image, listing_id, parsing_date) -> None:
        """
        Log errors during scraping.

        :param errors: A list to store error details.
        :param listing_data: The scraped listing data or error details.
        :param image: The scraped image data or error details.
        :param listing_id: The ID of the listing.
        :param parsing_date: The date the data was parsed.
        """
        if listing_data is not None:
            errors.append(
                dict(
                    id=listing_id,
                    parsing_date=parsing_date,
                    error_source="listing",
                    error_cause=listing_data,
                )
            )

        if image is not None:
            errors.append(
                dict(
                    id=listing_id,
                    parsing_date=parsing_date,
                    error_source="image",
                    error_cause=image,
                )
            )

    @staticmethod
    def _scrape_listing_data(soup) -> dict | str:
        """
        Extract data from the listing page.

        :param soup: A BeautifulSoup object representing the HTML content of the listing page.
        :return: A dictionary containing the scraped data or a string with the exception name if an error occurs.
        """
        try:
            # Extract listing details using BeautifulSoup
            category = soup.select('[href*="/designers/"]')[2]["href"].split("/")[-1]
            color = soup.select_one(
                'p[class="Body_body__dIg1V Text Details_detail__J0Uny Details_nonMobile__AObqX"]'
                ':-soup-contains("Color")'
            ).text.removeprefix("Color ")
            condition = soup.select_one(
                'p[class="Body_body__dIg1V Text Details_detail__J0Uny Details_nonMobile__AObqX"]'
                ':-soup-contains("Condition")'
            ).text.removeprefix("Condition ")
            department = soup.select('[href*="/designers/"]')[1]["href"].split("/")[-1]
            designer = soup.select('[href*="/designers/"]')[0]["href"].split("/")[-1]
            description = soup.select(
                'p[class="Body_body__dIg1V Text Description_paragraph__Gs7y6"]'
            )
            description = " ".join(
                [paragraph.text for paragraph in description]
            )  # Join all paragraphs in the description
            hashtags = soup.select('a[href*="hashtag"]')
            if hashtags:  # Hashtags are optional
                hashtags = " ".join(
                    [
                        hashtag["href"].removeprefix("/shop?hashtag=")
                        for hashtag in hashtags
                    ]
                )
            else:
                hashtags = None
            item_name = soup.select_one(
                'h1[class="Body_body__dIg1V Text Details_title__PpX5v"]'
            ).text
            n_photos = len(soup.select('button[class="Button_button__30ukX"]'))
            size = soup.select_one(
                'p[class="Body_body__dIg1V Text Details_detail__J0Uny Details_nonMobile__AObqX"]'
                ':-soup-contains("Size")'
            ).text.removeprefix("Size ")
            sold_price = int(
                soup.select('span[class*="SoldPrice"]')[0].text.removeprefix("$")
            )
            subcategory = soup.select('[href*="/designers/"]')[3]["href"].split("/")[-1]
        except Exception as e:
            return (
                e.__class__.__name__
            )  # Return exception name if data extraction fails

        return {
            "designer": designer,
            "department": department,
            "category": category,
            "subcategory": subcategory,
            "n_photos": n_photos,
            "item_name": item_name,
            "size": size,
            "color": color,
            "condition": condition,
            "description": description,
            "hashtags": hashtags,
            "sold_price": sold_price,
        }

    def get_links(self, n_listings: int = 800) -> tuple[list[str], list[str]]:
        """
        Retrieve links to the listings and cover images.

        :param n_listings: The number of listings to retrieve links for.
        :return: A tuple containing lists of listing URLs and cover image URLs.
        """
        assert 0 < n_listings <= 800, "n_listings must be between 1 and 800 (included)"

        driver = self.driver_manager.create_driver()
        login_manager = GrailedLoginManager(driver, self.email, self.password)

        if not login_manager.login():
            return [], []

        driver.get(f"{self.base_url}sold/")
        self.uniform_sleep()

        listings_links = self._collect_links(driver, n_listings)
        cover_imgs_links = self._collect_cover_images(driver, n_listings)

        self.logger.info(
            f"Collected {len(listings_links)} listings and cover images links"
        )

        return listings_links, cover_imgs_links

    def _collect_links(self, driver, n_listings: int) -> list[str]:
        """
        Collect sold listings links.

        :param driver: The Selenium WebDriver instance.
        :param n_listings: The number of listings links to collect.
        :return: A list of listing URLs.
        """
        listings_links = driver.find_elements(By.CLASS_NAME, "listing-item-link")
        scrolls_count = 0

        while len(listings_links) < n_listings and scrolls_count < 11:
            driver.execute_script("window.scrollBy(0, document.body.scrollHeight)")
            self.uniform_sleep()
            listings_links = driver.find_elements(By.CLASS_NAME, "listing-item-link")
            scrolls_count += 1
        listings_links = listings_links[:n_listings]

        return [link.get_attribute("href") for link in listings_links]

    def get_listing_data(self, listing_link: str) -> dict | dict:
        """
        Scrape and return data from a listing.

        :param listing_link: The URL of the listing.
        :return: A dictionary containing the listing data if successful, or a dictionary with error details if the request fails.
        """
        try:
            listing = requests.get(listing_link, headers={"User-Agent": self.ua.random})
            if not listing.ok:
                return {"error": "HTTPError", "status_code": listing.status_code}

            soup = BeautifulSoup(listing.content, features="html.parser")
            data = self._scrape_listing_data(soup)

            if isinstance(data, str):  # If _scrape_listing_data returns an error name
                return {"error": data, "message": "Failed to scrape listing data"}

            return data

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to retrieve listing from {listing_link}: {e}")
            return {"error": e.__class__.__name__, "message": str(e)}

    def scrape(
        self, n_listings: int = 800
    ) -> tuple[list[dict], list[bytes], list[dict]]:
        """
        Perform the main scraping operation for a specified number of listings.

        :param n_listings: The number of listings to scrape.
        :return: A tuple containing lists of listing data, images, and any errors encountered.
        """

        assert 0 < n_listings <= 800, "n_listings must be between 1 and 800 (included)"

        listings_links, cover_imgs_links = self.get_links(n_listings)

        listings_data = []
        cover_imgs = []
        errors = []
        parsing_date = date.today().strftime("%Y-%m-%d")

        for listing_link, cover_imgs_link in tqdm(
            zip(listings_links, cover_imgs_links)
        ):
            listing_id = re.search(r"\d+", listing_link).group(0)
            listing_data = self.get_listing_data(listing_link)
            image = self.get_image(cover_imgs_link)

            if "error" not in listing_data and isinstance(image, bytes):
                listings_data.append(
                    dict(id=listing_id, parsing_date=parsing_date, **listing_data)
                )
                cover_imgs.append(image)
            if "error" in listing_data:
                self.logger.warning(
                    f"Listing data fetch failed for listing ID {listing_id}"
                )
                self._handle_errors(
                    errors, listing_data, None, listing_id, parsing_date
                )
            if isinstance(image, dict):
                self.logger.warning(f"Image fetch failed for listing ID {listing_id}")
                self._handle_errors(errors, None, image, listing_id, parsing_date)

            self.uniform_sleep()

        self.logger.info(f"Collected data over {len(listings_data)} listings")

        return listings_data, cover_imgs, errors
