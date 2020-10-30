from secrets import linkedInUser, linkedInPW

from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException, NoSuchElementException
from time import sleep


class Scraper:
    def __init__(self, keywords, deal_breakers):
        self.driver = webdriver.Chrome()
        self.keywords = keywords
        self.deal_breakers = deal_breakers

    def login(self):
        self.driver.get('https://www.linkedin.com/jobs/')
        sleep(2)

        login_input = self.driver.find_element_by_xpath('//*[@id="session_key"]')
        login_input.send_keys(linkedInUser)

        pw_input = self.driver.find_element_by_xpath('//*[@id="session_password"]')
        pw_input.send_keys(linkedInPW)

        sign_in_btn = self.driver.find_element_by_xpath('/html/body/nav/section/form/div[2]/button')
        sign_in_btn.click()
        sleep(2)
        # the first div number changes between 7 and 8 for no apparent reason, so we must check both on most calls
        jobs_list = self.driver.find_elements_by_xpath('/html/body/div[8]/div[3]/div/section/section[3]/div/div/ul/li')
        if len(jobs_list) == 0 or jobs_list is None:
            jobs_list = self.driver.find_elements_by_xpath(
                '/html/body/div[7]/div[3]/div/section/section[3]/div/div/ul/li')
        jobs_list[0].click()
        sleep(1)
        # Lower chat so it doesn't get in the way
        chat_btn = self.driver.find_element_by_xpath('//*[@id="ember191"]')
        chat_btn.click()

    def parse_jobs(self):
        # LinkedIn only loads jobs when you scroll down
        left = self.driver.find_element_by_class_name("jobs-search-results")
        for i in range(10):
            y = 250 + i * 250
            self.driver.execute_script("arguments[0].scrollTo(0," + str(y) + ");", left)
            sleep(0.1)

        div_num = 8
        jobs = self.driver.find_elements_by_xpath(
            '/html/body/div[8]/div[3]/div[3]/div/div/div/div/section/div/ul/li')
        if len(jobs) == 0 or jobs is None:
            jobs = self.driver.find_elements_by_xpath(
                '/html/body/div[7]/div[3]/div[3]/div/div/div/div/section/div/ul/li')
            div_num = 7
        for i in range(len(jobs)):
            job_link = None
            try:
                job_link = jobs[i].find_elements_by_tag_name('a')[1]
            except IndexError:
                links = jobs[i].find_elements_by_tag_name('a')
                for l in range(len(links)):
                    if any(word in links[l].text for word in (['Dev', 'Engineer', 'Software'] + self.keywords)):
                        job_link = links[l]
                if job_link is None:
                    continue
            try:
                job_link.click()
            except ElementClickInterceptedException:
                x_popup = self.driver.find_element_by_xpath('/html/body/div[1]/section/ul/li/button/li-icon')
                x_popup.click()
                sleep(1)
                job_link.click()
            sleep(1)
            try:
                save = self.driver.find_element_by_xpath(
                    '/html/body/div[' + str(div_num) +
                    ']/div[3]/div[3]/div/div/div/section/div/div/div[1]/div/div[1]/div/div/div[2]/div[2]/div[1]/button')
                if self.check_job() and 'Unsave' not in save.text:
                    save.click()
                    sleep(1)
            except ElementClickInterceptedException:
                sleep(2)
                save.click()
            except NoSuchElementException:
                continue
        self.update_page()

    def update_page(self):
        pages = self.driver.find_elements_by_xpath(
            '/html/body/div[7]/div[3]/div[3]/div/div/div/div/section/div/section/div/ul/li')
        if len(pages) == 0 or pages is None:
            pages = self.driver.find_elements_by_xpath(
                '/html/body/div[8]/div[3]/div[3]/div/div/div/div/section/div/section/div/ul/li')
        for i in range(len(pages)):
            if pages[i].text.isdigit() and \
                    int(pages[i].text) < 6 and \
                    len(pages[i].find_elements_by_tag_name('span')) > 1:
                current_page = pages[i + 1]
                current_page.click()
                self.parse_jobs()

    def check_job(self):
        count = 0
        details = self.driver.find_element_by_xpath('//*[@id="job-details"]').text
        words = details.lower().split(' ')
        for keyword in self.keywords.keys():
            if keyword in words:
                count += self.keywords[keyword]
        if count > 7 and not any(word in words for word in self.deal_breakers) \
                and not any(
            (words[i + 1] == 'years' and ((words[i].isdigit() and int(words[i]) > 1) or not words[i].isdigit())) \
            for i in range(len(words) - 1)):
            return True
        return False


deal_breaks = ['intern', 'stage', 'part-time', 'senior']
keys = {'java': 5, 'python': 3.5, 'junior': 4, 'entry-level': 4, 'c#': 4, 'react': 2, 'vue': 2}
s = Scraper(keys, deal_breaks)
s.login()
s.parse_jobs()
