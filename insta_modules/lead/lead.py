from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import datetime
import datetime
import pandas as pd
from cryptography.fernet import Fernet

from insta_modules.post.post import Post
from insta_modules.util import checkEqual
from insta_modules.util import parse_string
from insta_modules.util import find_element_decorator
from insta_modules.util import find_element
from insta_modules.util import flat_array

from insta_modules.user.user_functions import *
import pandas as pd
import numpy as np
import random


class Lead:
    def __init__(self,config):

        self.gender = config['gender']
        self.min_followers = int(config['min_followers'])
        self.max_followers = int(config['max_followers'])
        self.min_following = int(config['min_following'])
        self.max_following = int(config['max_following'])
        self.min_ff_ratio = float(config['min_ff_ratio'])
        self.max_ff_ratio = float(config['max_ff_ratio'])
        self.min_posts = int(config['min_posts'])
        self.max_posts = int(config['max_posts'])
        #self.min_comments_mean = float(config['min_comments_mean'])
        self.max_last_post_datetime = datetime.timedelta(**eval(config['last_post_date']))
        self.is_private = config['privacy']
        self.hashtags_blacklist = eval(config['hashtags_blacklist'])


    def pre_analysis(self,user):
        filter = all([(user.gender == self.gender),
        (self.min_ff_ratio < user.ff_ratio < self.max_ff_ratio),
        (self.min_followers < user.followers < self.max_followers),
        (self.min_following < user.following < self.max_following),
        (self.min_posts < user.posts < self.max_posts),
        ])

        if filter:
            return True
        else:
            return False

    def analyse(self,user):
        filter = all([(user.gender == self.gender),
        (self.min_ff_ratio < user.ff_ratio < self.max_ff_ratio),
        (self.min_followers < user.followers < self.max_followers),
        (self.min_following < user.following < self.max_following),
        (self.min_posts < user.posts < self.max_posts),
        (user.last_post_datetime < self.max_last_post_datetime or user.last_post_datetime == datetime.timedelta(days=7588))
        ])

        if filter:
            return True
        else:
            return False

    def set_hashtags_blacklist(self):
        try:
            with open("config/hashtags_blacklist.txt",'r') as file:
                htl = file.read().split('\n')
                self.hashtags_blacklist = [ht.strip() for ht in htl]
        except:
            print("hashtags_blacklist.txt não foi encontrado.")
