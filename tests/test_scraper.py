from unittest.mock import MagicMock, patch

import pytest
from requests.exceptions import RequestException
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from data_collection.scraper import (
    GrailedLoginManager,
    GrailedScraper,
    WebDriverManager,
)


# Fixtures to provide mocked instances of Selenium WebDriver
@pytest.fixture
def mock_driver(mocker):
    """Fixture to mock the Selenium Chrome WebDriver."""
    return mocker.patch("selenium.webdriver.Chrome")


@pytest.fixture
def login_manager(mock_driver):
    """Fixture to create an instance of GrailedLoginManager with a mocked WebDriver."""
    mock_instance = mock_driver.return_value
    return GrailedLoginManager(mock_instance, "test@example.com", "password")


class TestWebDriverManager:
    """Test suite for the WebDriverManager class."""

    def test_create_driver(self, mock_driver):
        """Test that WebDriverManager correctly creates a WebDriver instance."""
        manager = WebDriverManager()
        manager.create_driver()

        # Ensure that the Chrome WebDriver is called with the expected options
        mock_driver.assert_called_once_with(options=manager._options)


class TestGrailedLoginManager:
    """Test suite for the GrailedLoginManager class."""

    def test_accept_privacy_policy_success(self, login_manager, mocker):
        """Test successful acceptance of the privacy policy."""
        mock_element = MagicMock()
        mocker.patch(
            "selenium.webdriver.support.ui.WebDriverWait.until",
            return_value=mock_element,
        )
        mocker.patch.object(GrailedScraper, "uniform_sleep")

        assert login_manager._accept_privacy_policy() is True
        mock_element.click.assert_called()

    def test_accept_privacy_policy_timeout(self, login_manager, mocker):
        """Test handling of a TimeoutException when accepting the privacy policy."""
        mocker.patch(
            "selenium.webdriver.support.ui.WebDriverWait.until",
            side_effect=TimeoutException,
        )

        assert login_manager._accept_privacy_policy() is False

    def test_click_login_success(self, login_manager, mocker):
        """Test successful clicking of the login link."""
        mock_element = MagicMock()
        mocker.patch(
            "selenium.webdriver.support.ui.WebDriverWait.until",
            return_value=mock_element,
        )
        mocker.patch.object(GrailedScraper, "uniform_sleep")

        assert login_manager._click_login() is True
        mock_element.click.assert_called()

    def test_click_login_timeout(self, login_manager, mocker):
        """Test handling of a TimeoutException when clicking the login link."""
        mocker.patch(
            "selenium.webdriver.support.ui.WebDriverWait.until",
            side_effect=TimeoutException,
        )

        assert login_manager._click_login() is False

    def test_enter_credentials_and_submit_success(self, login_manager, mocker):
        """Test successful submission of login credentials."""
        mock_element = MagicMock()
        mocker.patch(
            "selenium.webdriver.support.ui.WebDriverWait.until",
            return_value=mock_element,
        )
        mocker.patch.object(GrailedScraper, "uniform_sleep")
        mocker.patch("time.sleep")
        login_manager.driver.find_element.return_value = mock_element
        login_manager.driver.current_url = "https://www.grailed.com/"

        assert login_manager._enter_credentials_and_submit() is True
        mock_element.send_keys.assert_any_call("test@example.com")
        mock_element.send_keys.assert_any_call("password")

    def test_enter_credentials_and_submit_timeout(self, login_manager, mocker):
        """Test handling of a TimeoutException when entering credentials."""
        mocker.patch(
            "selenium.webdriver.support.ui.WebDriverWait.until",
            side_effect=TimeoutException,
        )

        assert login_manager._enter_credentials_and_submit() is False

    def test_enter_credentials_and_submit_element_not_found(
        self, login_manager, mocker
    ):
        """Test handling of NoSuchElementException when entering credentials."""
        mocker.patch(
            "selenium.webdriver.support.ui.WebDriverWait.until",
            side_effect=NoSuchElementException,
        )

        assert login_manager._enter_credentials_and_submit() is False

    @patch.object(GrailedLoginManager, "_accept_privacy_policy", return_value=True)
    @patch.object(GrailedLoginManager, "_click_login", return_value=True)
    @patch.object(
        GrailedLoginManager, "_enter_credentials_and_submit", return_value=True
    )
    @patch.object(GrailedScraper, "uniform_sleep")
    def test_login_success(
        self, mock_accept, mock_click, mock_submit, mock_sleep, login_manager
    ):
        """Test successful login process."""
        login_manager.driver.current_url = "https://www.grailed.com/"
        assert login_manager.login() is True

    @patch.object(GrailedLoginManager, "_accept_privacy_policy", return_value=False)
    @patch.object(GrailedScraper, "uniform_sleep")
    def test_login_failure_accept_privacy_policy(
        self, mock_accept, mock_sleep, login_manager
    ):
        """Test login failure when privacy policy is not accepted."""
        assert login_manager.login() is False

    @patch.object(GrailedLoginManager, "_accept_privacy_policy", return_value=True)
    @patch.object(GrailedLoginManager, "_click_login", return_value=False)
    @patch.object(GrailedScraper, "uniform_sleep")
    def test_login_failure_click_login(
        self, mock_accept, mock_click, mock_sleep, login_manager
    ):
        """Test login failure when login link is not clicked."""
        assert login_manager.login() is False

    @patch.object(GrailedLoginManager, "_accept_privacy_policy", return_value=True)
    @patch.object(GrailedLoginManager, "_click_login", return_value=True)
    @patch.object(
        GrailedLoginManager, "_enter_credentials_and_submit", return_value=False
    )
    @patch.object(GrailedScraper, "uniform_sleep")
    def test_login_failure_enter_credentials_and_submit(
        self, mock_accept, mock_click, mock_submit, mock_sleep, login_manager
    ):
        """Test login failure when credentials submission fails."""
        assert login_manager.login() is False

    @patch.object(GrailedLoginManager, "_accept_privacy_policy", return_value=True)
    @patch.object(GrailedLoginManager, "_click_login", return_value=True)
    @patch.object(
        GrailedLoginManager, "_enter_credentials_and_submit", return_value=True
    )
    @patch.object(GrailedScraper, "uniform_sleep")
    def test_login_failure_current_url(
        self, mock_accept, mock_click, mock_submit, mock_sleep, login_manager
    ):
        """Test login failure due to incorrect final URL."""
        login_manager.driver.current_url = "https://www.grailed.com/signup"
        assert login_manager.login() is False


class TestGrailedScraper:
    """Test suite for the GrailedScraper class."""

    def test_get_image_success(self, mocker):
        """Test successful retrieval of an image."""
        mock_response = MagicMock(ok=True, content=b"image_bytes")
        mocker.patch("requests.get", return_value=mock_response)

        assert (
            GrailedScraper.get_image("http://example.com/image.jpg") == b"image_bytes"
        )

    def test_get_image_failure_http_error(self, mocker):
        """Test handling of HTTP error during image retrieval."""
        mock_response = MagicMock(ok=False, status_code=404)
        mocker.patch("requests.get", return_value=mock_response)

        assert GrailedScraper.get_image("http://example.com/image.jpg") == {
            "error": "HTTPError",
            "status_code": 404,
        }

    def test_get_image_failure_request_error(self, mocker):
        """Test handling of a RequestException during image retrieval."""
        mocker.patch("requests.get", side_effect=RequestException)

        assert GrailedScraper.get_image("http://example.com/image.jpg") == {
            "error": "RequestException",
            "message": "",
        }

    def test_scrape_listing_data_success(self, mocker):
        """Test successful scraping of listing data."""
        mock_select_one = MagicMock(text="0")
        mock_select_one.__getitem__.return_value = "0"
        mock_select = MagicMock()
        mock_select.__getitem__.return_value = mock_select_one
        mock_select.__iter__.return_value = [mock_select_one]
        mock_soup = mocker.Mock()
        mock_soup.select.return_value = mock_select
        mock_soup.select_one.return_value = mock_select_one

        data = GrailedScraper._scrape_listing_data(mock_soup)
        assert isinstance(data, dict)

    def test_scrape_listing_data_success_no_hashtags(self, mocker):
        """Test scraping of listing data with no hashtags present."""

        def side_effect(element):
            if element == 'a[href*="hashtag"]':
                return None
            return mock_select

        mock_select_one = MagicMock(text="0")
        mock_select_one.__getitem__.return_value = "0"
        mock_select = MagicMock()
        mock_select.__getitem__.return_value = mock_select_one
        mock_select.__iter__.return_value = [mock_select_one]
        mock_soup = mocker.Mock()
        mock_soup.select.side_effect = side_effect
        mock_soup.select_one.return_value = mock_select_one

        data = GrailedScraper._scrape_listing_data(mock_soup)
        assert isinstance(data, dict)
        assert data["hashtags"] is None

    def test_scrape_listing_data_failure(self, mocker):
        """Test failure in scraping listing data due to an unexpected error."""
        mock_soup = mocker.Mock()
        mock_soup.select = None
        mock_soup.select_one.return_value = None

        assert GrailedScraper._scrape_listing_data(mock_soup) == "TypeError"

    def test_get_links_success(self, mocker):
        """Test successful retrieval of listing and cover image links."""
        mocker.patch("selenium.webdriver.Chrome")
        mocker.patch.object(GrailedLoginManager, "login", return_value=True)
        mocker.patch.object(
            GrailedScraper, "_collect_links", return_value=["listing_link"]
        )
        mocker.patch.object(
            GrailedScraper, "_collect_cover_images", return_value=["cover_img_link"]
        )

        scraper = GrailedScraper("test@example.com", "password")
        links, images = scraper.get_links(1)

        assert links == ["listing_link"]
        assert images == ["cover_img_link"]

    def test_get_links_login_failure(self, mocker, mock_driver):
        """Test failure to retrieve links due to login failure."""
        mocker.patch.object(GrailedLoginManager, "login", return_value=False)

        scraper = GrailedScraper("test@example.com", "password")
        links, images = scraper.get_links(1)

        assert links == []
        assert images == []

    def test_get_listing_data_success(self, mocker):
        """Test successful retrieval of listing data."""
        mock_response = MagicMock(ok=True, content=b"listing_bytes")
        mocker.patch("requests.get", return_value=mock_response)
        mocker.patch.object(GrailedScraper, "_scrape_listing_data", return_value={})

        scraper = GrailedScraper("test@example.com", "password")
        assert isinstance(
            scraper.get_listing_data("http://example.com/listings.html"), dict
        )

    def test_get_listing_data_failure_http_error(self, mocker):
        """Test handling of HTTP error during listing data retrieval."""
        mock_response = MagicMock(ok=False, status_code=404)
        mocker.patch("requests.get", return_value=mock_response)

        scraper = GrailedScraper("test@example.com", "password")
        assert scraper.get_listing_data("http://example.com/listings.html") == {
            "error": "HTTPError",
            "status_code": 404,
        }

    def test_get_listing_data_failure_type_error(self, mocker):
        """Test handling of TypeError during listing data scraping."""
        mock_response = MagicMock(ok=True, content=b"listing_bytes")
        mocker.patch("requests.get", return_value=mock_response)
        mocker.patch.object(
            GrailedScraper, "_scrape_listing_data", return_value="TypeError"
        )

        scraper = GrailedScraper("test@example.com", "password")
        assert scraper.get_listing_data("http://example.com/listings.html") == {
            "error": "TypeError",
            "message": "Failed to scrape listing data",
        }

    def test_get_listing_data_failure_request_error(self, mocker):
        """Test handling of a RequestException during listing data retrieval."""
        mocker.patch("requests.get", side_effect=RequestException)

        scraper = GrailedScraper("test@example.com", "password")
        assert scraper.get_listing_data("http://example.com/listings.html") == {
            "error": "RequestException",
            "message": "",
        }

    def test_collect_cover_images(self, mock_driver):
        """Test successful collection of cover image links."""
        mock_cover_img_link = MagicMock(
            get_attribute=MagicMock(return_value="cover_img_URL")
        )
        mock_driver.find_elements.return_value = [mock_cover_img_link]

        scraper = GrailedScraper("test@example.com", "password")
        cover_img_links = scraper._collect_cover_images(mock_driver, 1)

        assert cover_img_links == ["cover_img_URL"]

    def test_handle_errors(self, mocker):
        """Test error handling during scraping."""
        errors = []
        scraper = GrailedScraper("test@example.com", "password")
        scraper._handle_errors(errors, "TypeError", 404, "12345", "2024-08-29")

        assert isinstance(errors[0], dict)

    @patch.object(GrailedScraper, "uniform_sleep")
    def test_collect_links(self, mock_driver):
        """Test successful collection of listing links."""
        mock_listing_link = MagicMock(
            get_attribute=MagicMock(return_value="listing_URL")
        )
        mock_driver.find_elements.return_value = [mock_listing_link]

        scraper = GrailedScraper("test@example.com", "password")
        listings_links = scraper._collect_links(mock_driver, 2)

        assert listings_links == ["listing_URL"]

    def test_scrape_success(self, mocker):
        """Test successful scraping of listings and images."""
        mocker.patch.object(
            GrailedScraper,
            "get_links",
            return_value=(
                ["https://www.grailed.com/listings/12345"],
                ["cover_img_link"],
            ),
        )
        mocker.patch.object(
            GrailedScraper,
            "get_listing_data",
            return_value={"listing_feature": "feature_value"},
        )
        mocker.patch.object(GrailedScraper, "get_image", return_value=b"image_bytes")
        mocker.patch.object(GrailedScraper, "uniform_sleep")

        scraper = GrailedScraper("test@example.com", "password")
        listings_data, cover_imgs, errors = scraper.scrape(n_listings=1)

        assert len(listings_data) == 1
        assert listings_data[0]["id"] == "12345"
        assert "listing_feature" in listings_data[0]
        assert cover_imgs == [b"image_bytes"]

    def test_scrape_error(self, mocker):
        """Test error handling during scraping when both listing data and image retrieval fail."""
        mocker.patch.object(
            GrailedScraper,
            "get_links",
            return_value=(
                ["https://www.grailed.com/listings/12345"],
                ["cover_img_link"],
            ),
        )
        mocker.patch.object(
            GrailedScraper,
            "get_listing_data",
            return_value={"error": "HTTPError", "status_code": 404},
        )
        mocker.patch.object(
            GrailedScraper,
            "get_image",
            return_value={"error": "HTTPError", "status_code": 404},
        )
        mocker.patch.object(GrailedScraper, "uniform_sleep")

        scraper = GrailedScraper("test@example.com", "password")
        listings_data, cover_imgs, errors = scraper.scrape(n_listings=1)

        assert listings_data == []
        assert cover_imgs == []
        assert len(errors) == 2
