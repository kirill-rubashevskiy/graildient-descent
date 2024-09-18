import pandas as pd
import streamlit as st


def display_data_collection_scraper():

    # df with sample scraped listings
    df = pd.read_csv(
        "https://storage.yandexcloud.net/graildient-descent-assets/data_collection/sample_scraped_listings.csv"
    )
    df.drop(columns=["parsing_date"], inplace=True)
    df["id"] = df["id"].astype(str)
    df["cover_image"] = [
        f"https://storage.yandexcloud.net/graildient-descent-assets/data_collection/sample_scraped_image_{i}.webp"
        for i in range(10)
    ]
    cols = df.columns.tolist()
    cols = cols[-1:] + cols[:-1]
    df = df[cols]

    st.markdown(
        """
        ## Building the Grailed Scraper

        > **TL;DR:** You can find the full code for the Grailed Scraper on the projects'
          [GitHub](https://github.com/kirill-rubashevskiy/graildient-descent/blob/main/data_collection/scraper.py).
          It scrapes sold listings data and cover photos.

        First things first — let’s gather some data!

        ### No API? No Problem

        Grailed doesn't offer a public API, and its [Terms of Service](https://www.grailed.com/about/terms) explicitly forbid scraping data.
        However, we plan to use the scraped data solely for educational purposes, focus only on sold listings (where Grailed has already earned its commission), and minimize the negative impact of scraping on their site by:

        - Limiting scraping to small batches.
        - Keeping scraped data private.

        ### Which Listings to Scrape?
        """
    )

    st.image(
        "https://storage.yandexcloud.net/graildient-descent-assets/data_collection/sold_listings_feed.png",
        caption="Grailed sold listings feed",
    )

    st.markdown(
        """
        To train models, we need sold listings data (so we get our sold price targets),
        and the fresher the data, the better. Older listings may reflect outdated
        trends, so we focus on recent sales.

        The best source is Grailed's [sold listings feed](https://www.grailed.com/sold/),
        which allows sorting sold listings by the date of sale. Unfortunately, access to
        this feed requires a log in. To solve this, we used Selenium to automate the log
        in process and gather links to sold listings.

        ### Automating Grailed Log in
        """
    )

    images = [
        "https://storage.yandexcloud.net/graildient-descent-assets/data_collection/login_privacy_policy.png",
        "https://storage.yandexcloud.net/graildient-descent-assets/data_collection/login_log_in_link.png",
        "https://storage.yandexcloud.net/graildient-descent-assets/data_collection/login_login_email_button.png",
        "https://storage.yandexcloud.net/graildient-descent-assets/data_collection/login_credentials.png",
    ]
    captions = [
        "1. Accept or decline the privacy policy",
        '2. Click "Log in" link',
        '3. Click "Login with email" button',
        '4. Enter credentials and click "Log in" button',
    ]
    for col, image, caption in zip(st.columns(2) + st.columns(2), images, captions):
        with col:
            st.image(image, caption=caption)

    st.markdown(
        """
        To log in, several steps are required:

        1. Accept or decline the website privacy policy in the pop-up block at the end
        of the page.
        2. Click the "Log in" link to open the login popup.
        3. Click the "Login with email" button.
        4. Enter credentials and click the "Log in" button.

        We created the `GrailedLoginManager` class to automate this process.
        """
    )

    with st.expander("GrailedLoginManager class"):  # GrailedLoginManager class
        code = '''
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
        '''
        st.code(code, language="python")

    st.markdown(
        """
        ### Scraping Infinite Listings

        The sold feed is infinite, loading more listings as you scroll, but it caps at
        around 800 listings. We wrote:

        - `_collect_links` function to scroll the feed, gather links to listings, and
        stop either when the desired number of links is reached or after a fixed number
        of scrolls.
        """
    )

    with st.expander("_collect_links function"):  # _collect_links function
        code = '''
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
        '''
        st.code(code, language="python")

    st.markdown("- `_collect_cover_images` function to collect cover image links.")

    with st.expander(
        "_collect_cover_images function"
    ):  # _collect_cover_images function
        code = '''
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
        '''
        st.code(code, language="python")

    st.markdown("- `get_links` function to unify both processes.")

    with st.expander("get_links function"):  # get_links function
        code = '''
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
        '''
        st.code(code, language="python")

    st.markdown("### What Data to Scrape?")

    st.image(
        [
            "https://storage.yandexcloud.net/graildient-descent-assets/data_collection/sold_listing_top.png",
            "https://storage.yandexcloud.net/graildient-descent-assets/data_collection/sold_listing_middle.png",
            "https://storage.yandexcloud.net/graildient-descent-assets/data_collection/sold_listing_bottom.png",
        ],
        caption=[None, None, "Sold listing page"],
    )

    st.markdown(
        """
        The good news: sold listing pages don’t require login. We used the `requests`
        library to fetch data.

        We plan to scrape three categories of data:

        1. **Tabular data**: designer, department, category, subcategory, size, color,
        condition, and sold price.

        2. **Text data**: item name, item description, and hashtags.

        3. **Images**: we will scrape only the cover photo and the total number of
        listing photos for simplicity and to save memory.

        We created `_scrape_listing_data` and `get_image` functions to handle scraping
        this data.
        """
    )

    with st.expander("_scrape_listing_data function"):  # scrape_listing_data function
        code = '''
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
        '''

        st.code(code, language="python")

    with st.expander("get_image function"):  # get_image function
        code = '''
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
        '''

        st.code(code, language="python")

    st.markdown(
        """
        *Note: Item measurements couldn’t be scraped due to how Grailed renders them.*

        ### Error Handling and Monitoring

        To ensure that the scraper runs smoothly even when encountering issues (e.g.,
        broken links, missing data), we implemented structured error logging. This
        allows us to track the scraping process and capture details about failed
        listings without stopping the entire process. Logging helps with debugging and
        identifying any patterns in failed scraping attempts.
        """
    )

    with st.expander("_handle_errors function"):  # _handle_errors function
        code = '''
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
        '''

        st.code(code, language="python")

    st.markdown(
        """
        ### Staying Under the Radar

        To avoid getting blocked by Grailed, we:

        - limit the scraper to 800 listings per session and add random uniform pauses
        between actions, simulating human-like behavior.
        """
    )

    code = '''
    @staticmethod
    def uniform_sleep() -> None:
        """Sleep for a random duration between 1 and 10 seconds to mimic human interaction."""
        time.sleep(np.random.uniform(1, 10))
    '''

    st.code(code, language="python")

    st.markdown(
        """
        - use a rotating user agent via the `fake_useragent` library with both Selenium
        and requests. The `WebDriverManager` class handles setting up the Chrome
        WebDriver with the right options, ensuring a different user agent is used each
        time.
        """
    )

    with st.expander("WebDriverManager class"):  # WebDriverManager class
        code = '''
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
        '''

        st.code(code, language="python")

    st.markdown(
        """
        *Note: Occasionally, Grailed still throws captchas at the login stage, so it’s best to
        monitor the scraper at the start.*

        ### Putting It All Together

        The entire scraping process has been combined into a single function, `scrape`, that handles everything from initialization to data collection. The steps include:

        1. Initialize the Selenium driver with the `WebDriverManager`.
        2. Log in to the site using the `GrailedLoginManager`.
        3. Collect links to listings and their cover images.
        4. Scrape listing data and images.
        """
    )

    with st.expander("scrape function"):  # scrape function
        code = '''
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
        '''

        st.code(code, language="python")

    st.markdown(
        """
        Finally, for the ETL pipeline, everything is encapsulated in the
        `GrailedScraper` class to ensure reusability and simplicity.

        ### Let's Take a Look at the Scraper's Results

        Below is a table showing 10 scraped listings:
        """
    )

    st.data_editor(
        df,
        column_config={
            "cover_image": st.column_config.ImageColumn("cover_image"),
        },
        hide_index=True,
    )

    st.markdown(
        """
        ### Further Reading

        These materials were incredibly helpful while building the scraper, and they
        might also be useful to anyone interested in scraping data from Grailed:

        - Albert Frantz's [post](https://medium.com/analytics-vidhya/web-scraping-sold-clothing-on-grailed-with-selenium-2514cbe6855e)
        on Medium introduced me to Grailed’s scraping roadblocks, such as pop-ups and
        endless scrolling. Albert used a different approach by scraping sold listings by
        designer, without cover images.

        - My Master's program Math and Stats teacher co-wrote a hilarious and detailed
        [guide](https://habr.com/ru/companies/ods/articles/346632/) on scraping memes,
        which includes a comprehensive section on avoiding being blocked.
        (Unfortunately, it's only available in Russian.)
        """
    )
