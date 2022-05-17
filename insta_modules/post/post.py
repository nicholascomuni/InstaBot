import time
import re
from insta_modules.util import checkEqual
from insta_modules.util import find_element
from datetime import datetime
from insta_modules.post.post_functions import *
import urllib.request

class Post:
    def __init__(self,url,driver):
      self.driver = driver
      self.url = url

      self.likes = 0
      self.views = 0
      self.followers = 0
      self.following = 0
      self.comments = 0
      self.analysed = 0
      self.datetime = 0

      self.hashtags = []
      self.usertags = []
      self.likers = []
      self.caption = []

      self.poster = ""
      self.location = ""
      self.text = ""
      self.postType = ""


    def post_root(self):
        self.driver.get(f"https://www.instagram.com/p/{self.url}/")
        time.sleep(0.8)

    def light_analysis(self):
        self.post_root()

        self.driver.execute_script("window.scrollTo(0,1000)")

        self.poster = get_poster("",self.driver)
        self.likes = get_likes(0,self.driver)
        self.location = get_location(None,self.driver)
        self.datetime = get_post_time(None,self.driver)
        self.postType = get_post_type("Picture",self.driver)

        if self.postType == "Picture":
            self.caption = get_caption([],self.driver)
            self.views = None
        else:
            self.likes,self.views = get_video_views_likes(self.driver)
            self.caption = []

        self.text,self.hashtags,self.usertags = get_text_and_tags(self.driver)
        self.analysed = 1

    def get_post_info(self,comments):
        return get_pic_info_function(self,self.driver,comments)

    def medium_analysis(self,amount = None):
        self.get_post_info(False)
        amount = self.likes if amount is None else amount
        if not self.is_video:
            if self.likes > 0:
                try:
                    self.likers = get_likers(self,amount)
                    self.analysed = 2
                except KeyError:
                    print("Sleeping")
                    time.sleep(180)


    def get_picture_likers(self,amount = 100):
        response = self.get_post_info(False)

        if response:
            if not self.is_video:
                self.likers = get_likers(self,amount)
            else:
                self.likers = []
        else:
            self.likers = []

        return self.likers

    def get_post_post_type(self):
        self.postType = get_post_type("Picture",self.driver)
        return True

    def like(self):
        self.driver.get(f"https://www.instagram.com/p/{self.url}/")
        time.sleep(2)

        try:
            try:
                self.driver.execute_script("window.scrollTo(0,1000)")

                like_button = lambda: self.driver.find_element_by_xpath("//span[@aria-label='Like']")
                like_button().click()
                return True
            except:
                self.driver.execute_script("window.scrollTo(0,0)")

                like_button = lambda: self.driver.find_element_by_xpath("//span[@aria-label='Like']")
                like_button().click()
                return True
        except:
            print("LIKE FAILLED")
            return False

    def unlike(self):
        self.driver.get(f"https://www.instagram.com/p/{self.url}/")
        time.sleep(2)

        try:
            try:
                self.driver.execute_script("window.scrollTo(0,1000)")

                unlike_button = lambda: self.driver.find_element_by_xpath("//span[@aria-label='Unlike']")
                unlike_button().click()
                return True
            except:
                self.driver.execute_script("window.scrollTo(0,0)")

                unlike_button = lambda: self.driver.find_element_by_xpath("//span[@aria-label='Unlike']")
                unlike_button().click()
                return True
        except:
            self.driver.execute_script("window.scrollTo(0,1000)")
            like_button = find_element(self.driver,"//span[@aria-label='Like']")
            if like_button:
                return True
            else:
                self.driver.execute_script("window.scrollTo(0,0)")
                like_button = find_element(self.driver,"//span[@aria-label='Like']")
                if like_button:
                    return True
                else:
                    return False


    def download_pic(self):
        img = self.driver.find_element_by_xpath("//div[@class='KL4Bh']/img")
        src = img.get_attribute('src')
        print(self.url)
        urllib.request.urlretrieve(src, f"testedownload/{str(self.url)}.jpg")

    def check_page_not_available(self):
        elements = self.driver.find_elements_by_tag_name("h2")
        for element in elements:
            if element.text == "Sorry, this page isn't available.":
                return True
        return False
