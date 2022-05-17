from pathlib import Path
import os,sys
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import datetime
import pandas as pd
from cryptography.fernet import Fernet
from insta_modules.post.post import Post
from insta_modules.util import *
from insta_modules.user.user_functions import *
import pandas as pd
import numpy as np
import random
import pytz


class User:
    def __init__(self,username,driver):
        self.username = username
        self.id = ""
        self.full_name = ""
        self.first_name = ""
        self.surname = ""
        self.gender = ""
        self.bio = ""
        self.external_url = ""
        self.posts = 0
        self.followers = 0
        self.following = 0
        self.gender = ""
        self.is_business_account = False
        self.follows_viewer = False
        self.followed_by_viewer = False
        self.has_blocked_viewer = False
        self.profile_pic_url = ""

        self.ff_ratio = 0
        self.is_private = False
        self.analysed = 0
        self.likes_mean = 0
        self.comments_mean = 0
        self.posts_urls = []
        self.followers_list = []
        self.following_list = []
        self.likers = []
        self.hashtags = []
        self.captions = []
        self.top_likers = []
        self.all_likers = []
        self.posts_dates = []
        self.most_liked = 0
        self.follow_status = ""
        self.first_post_datetime = datetime.timedelta(days=7588)
        self.last_post_datetime = datetime.timedelta(days=7588)

        self.driver = driver


    def user_root(self):
        self.driver.get(f"https://www.instagram.com/{self.username}")
        time.sleep(1)

    def get_user_info(self):
        get_user_info_function(self)

    def medium_analysis(self):
        self.user_root()
        self.light_analysis()
        self.light_posts_analysis(100)
        self.analysed = 2

    def get_non_followers(self):
        t1 = time.time()
        get_user_info_function(self)
        followers = get_followers_list(self)
        following = get_following_list(self)
        print(f"Process took: {round(time.time()-t1,2)} seconds...")

        return [user for user in following if user not in followers]

    def heavy_analysis(self,depth = None):
        self.user_root()
        self.light_analysis()
        depth = self.posts if depth is None else depth
        self.medium_posts_analysis(depth)

    def full_analysis(self):
        pass

    def analise_c(self):
        get_user_info_function(self)
        if not self.is_private:
            self.get_user_pic_urls(8)


    def analysis1(self,lead,photos_amount = 8):
        get_user_info_function(self)
        try:
            self.ff_ratio = round(self.followers/self.following,3)
        except:
            self.ff_ratio = 0

        if lead.pre_analysis(self):
            if not self.is_private:
                self.get_user_pic_urls(8)
                hashtags,captions,datetimes = [],[],[]
                amount = len(self.posts_urls)
                for post_url in self.posts_urls:
                    post = Post(post_url,self.driver)
                    post.get_post_info(False)
                    captions.append(post.caption)
                    self.posts_dates.append(post.datetime)
                    amount -= 1

                self.last_post_datetime = datetime.datetime.now(pytz.timezone("America/Sao_Paulo")) - np.max(self.posts_dates)
                return True
            else:
                self.posts_dates = []
                self.posts_urls = []
                self.hashtags = []
                self.caption = []
                return True
        else:
            return False


    def get_user_pic_urls(self,amount = None):
        amount = self.posts if amount is None else amount
        self.posts_urls =  get_pics_urls(self,amount)
        return True

    def light_posts_analysis_old(self,amount = None):
        amount = self.posts if amount is None else amount
        arr =  get_pics_urls_LC(self.driver,amount,self.posts)
        urls = arr[:,0]

        likes_array = arr[:,1].astype(np.int32)
        comments_array = arr[:,2].astype(np.int32)

        self.posts_urls = urls
        self.likes_mean = likes_array.mean()
        self.comments_mean = comments_array.mean()
        self.most_liked = likes_array.max()

    def light_posts_analysis(self,amount = None):
        amount = self.posts if amount is None else amount
        arr =  get_pics_urls_LC(self.driver,amount,self.posts)
        urls = arr[:,0]

        likes_array = arr[:,1].astype(np.int32)
        comments_array = arr[:,2].astype(np.int32)

        self.posts_urls = urls
        self.likes_mean = likes_array.mean()
        self.comments_mean = comments_array.mean()
        self.most_liked = likes_array.max()


    def medium_posts_analysis(self,amount = None):
        amount = self.posts if amount is None else amount
        self.get_user_pic_urls(amount)
        likers,hashtags,captions = [],[],[]
        status = 0

        for post_url in self.posts_urls:
            status += 1
            print(f"          Total: {round(status/amount*100,2)}%",end='\r')
            post = Post(post_url,self.driver)
            post.medium_analysis()
            likers.append(post.likers)
            hashtags.append(post.hashtags)
            captions.append(post.caption)

        likers_list = [liker for likers_list in likers for liker in likers_list]
        hashtags_list = [hashtag for hashtag_list in hashtags for hashtag in hashtag_list]
        captions_list = [caption for caption_list in captions for caption in caption_list]

        self.top_likers = pd.Series(likers_list).value_counts().head(5)
        self.all_likers = pd.Series(likers_list,name='likes').value_counts()
        self.likers = likers_list
        self.hashtags = hashtags_list
        self.captions = captions_list

    def get_pic_urls(self,amount = None,sensibility = 15):
        amount = self.posts if amount is None else amount
        self.user_root()

        print(get_pics_urls(self.driver,amount,self.posts,sensibility))

    def followed_by_user(self):
        self.user_root()
        follow_button = find_element(self.driver,"//button[text() = 'Follow']")
        follow_requested = find_element(self.driver,"//button[text() = 'Requested']")
        unfollow_button = find_element(self.driver,"//button[text() = 'Unfollow']")

        if follow_button:
            return "Not Following"
        elif follow_request:
            return "Requested"
        elif unfollow_button:
            return "Following"

    def get_list_of_followers_old(self,amount = None):
        self.user_root()
        self.followers = get_followers(0,self.driver)
        amount = self.followers if amount is None else amount

        self.followers_list = get_followers_list(self.driver,self.user_root,amount)
        return self.followers_list

    def get_list_of_followers(self):
        self.user_root()
        self.followers_list = get_followers_list(self)
        return self.followers_list

    def get_list_of_following2(self):
        get_user_info_function(self)
        self.following_list = get_following_list(self)

        return self.following_list

    def get_list_of_following(self,amount = None):
        self.user_root()
        print(self.following)
        amount = self.following if amount is None else amount

        self.following_list = get_following_list(self.driver,self.user_root,amount)
        return self.following_list

    def following_not_followback(self,filename):
        get_user_info_function(self)
        self.get_list_of_followers()
        self.get_list_of_following()

        not_following_back = [person for person in self.following_list if person not in self.followers_list]
        with open(f'{filename}.txt','w') as file:
            for person in not_following_back:
                file.write(f"{person}\n")

    def like_random_of_3_first_posts(self):
        url = random.choice(self.posts_urls[:3])
        post = Post(url,self.driver)
        post.like()
        return url

    def like_random_of_x_first_posts(self,x):
        url = random.choice(self.posts_urls[:x])
        post = Post(url,self.driver)
        post.like()
        return url


    def follow(self):
        self.user_root()
        time.sleep(0.8)

        follow_button = find_element(self.driver,"//button[text() = 'Follow']")
        if follow_button:
            follow_button = self.driver.find_element_by_xpath("//button[text() = 'Follow']")
            follow_button.click()
            time.sleep(0.15)
            return True
        else:
            return False

    def unfollow(self):
        self.user_root()
        time.sleep(0.8)

        follow_button = find_element(self.driver,"//button[text() = 'Follow']")
        followback_button = find_element(self.driver,"//button[text() = 'Follow Back']")
        following_button = find_element(self.driver,"//button[text() = 'Following']")
        following_button_requested = find_element(self.driver,"//button[text() = 'Requested']")

        if following_button:
            print("Following button")
            following_button = self.driver.find_element_by_xpath("//button[text() = 'Following']")
            following_button.click()

            time.sleep(1)
            unfollow_button = find_element(self.driver,"//button[text() = 'Unfollow']")
            if unfollow_button:
                unfollow_button = self.driver.find_element_by_xpath("//button[text() = 'Unfollow']")
                unfollow_button.click()
                return True
            else:
                return False
        elif following_button_requested:
            print("Requested")
            following_button = self.driver.find_element_by_xpath("//button[text() = 'Requested']")
            following_button.click()

            time.sleep(1)
            unfollow_button = find_element(self.driver,"//button[text() = 'Unfollow']")
            if unfollow_button:
                unfollow_button = self.driver.find_element_by_xpath("//button[text() = 'Unfollow']")
                unfollow_button.click()
                return True
            else:
                return False
        elif follow_button or followback_button:
            print("Opção 3")
            return True

        else:
            print("False")
            return False

    def check_page_not_available(self):
        elements = self.driver.find_elements_by_tag_name("h2")
        for element in elements:
            if element.text == "Sorry, this page isn't available.":
                return True
        return False
