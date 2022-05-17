from insta_modules.user.user import User
from insta_modules.hashtag.hashtag import Hashtag
from insta_modules.post.post import Post
from insta_modules.lead.lead import Lead
from insta_modules.util import load_lead_profile
from insta_modules.util import ceiling
from insta_modules.util import minimum
from instabot import *
from ast import literal_eval

import configparser
import numpy as np
import threading
import datetime
import random
import trace
import pytz
import sys

from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException

class Bot(InstagramBot):
    def __init__(self,config,mode="full"):
        InstagramBot.__init__(self,config)
        self.mode = mode
        self.goodmorning = False
        self.stop_routine = False
        self.stop_robot = False
        self.tasks = {}
        self.task_status = {}
        self.status = 0
        self.bot_status = "Offline"
        self.sleeping = False

        self.while1_timer = []
        self.while2_timer = []
        self.user_root_timer = []
        self.analyse_user_timer = []
        self.commit_timer = []
        self.routine_timeouts = 0

        dtf = pd.DataFrame([],columns = ['user','datetime','posts','action'])
        self.schedule_dtf = dtf.datetime.astype(np.datetime64)

    def run(self):
        self.init_bot()
        countr1 = 0

        while True:
            countr1 += 1

            if self.mode == "full":
                self.task("Analyse_results",self.analyse_results,"08:32","08:47",   once=True)
                self.task("Schedule1",self.perform_schedule,     "08:48","10:44",   once=True)
                self.task("Routine1",self.routine,               "10:55","15:24",   args=(literal_eval(self.config['hashtags_list']),40,20,eval(self.config['commit_hook'])))
                self.task("Routine2",self.routine,               "16:14","20:03",   args=(literal_eval(self.config['hashtags_list']),40,20,eval(self.config['commit_hook'])))
                self.task("Routine3",self.routine,               "21:14","23:42",   args=(literal_eval(self.config['hashtags_list']),40,20,eval(self.config['commit_hook'])))
                self.task("Schedule3",self.perform_schedule,     "00:21","01:27",   once=True)
                self.task("Backup",self.s3_backup,               "03:21","03:34",   once=True)
                self.task("Rebalance",self.rebalance,            "03:41","03:48",   once=True)

            elif self.mode == "routine":
                self.task("Routine",self.routine,               "00:00","24:00",   args=(literal_eval(self.config['hashtags_list']),40,20,eval(self.config['commit_hook'])))

            elif self.mode == "schedule":
                self.task("Schedule",self.perform_schedule,     "00:00","24:00",   once=True)

            elif self.mode == "analyse_results":
                self.task("Analyse_results",self.analyse_results,"00:00","24:00",   once=True)

            elif self.mode == "analisar_urls":
                self.analisar_urls()
                break

            elif self.mode == "not_following_back":
                self.task("get_non_followers",self.get_unfollowers,"00:00","24:00",   once=True)



            if self.stop_robot:
                self.stop()
                return

            if self.routine_timeouts > 3:
                self.routine_timeouts = 0
                self.restart()

            if countr1 > 2:
                t1 = time.time()

                if self.status > 3:
                    self.bot_status = "Online"
                else:
                    self.bot_status = "Offline"

                self.total_runtime = self.save_total_runtime()
                print(f"\nRuntime: {self.total_runtime} - Bot {self.bot_status}")
                self.get_commit_status()
                self.status = 0
                countr1 = 0

            time.sleep(10)


    def scan(self):
        pass

    def muitos_requests(self):
        elements = self.driver.find_elements_by_xpath("//*[contains(text(), 'Please wait a few minutes before you try again.')]")
        if len(elements) > 0:
            return True
        else:
            return False


    def get_unfollowers(self):
        username = ""
        user = User(username,self.driver)
        not_following_back = user.get_non_followers()

        filename = ""
        with open(f'{filename}.txt','w') as file:
            for person in not_following_back:
                file.write(f"{person}\n")


    def routine(self,hashtags,hashtags_amount,likers_per_picture,tohook=False):

        try:
            self.load_commit_queue()
            # Get Hashtag posts urls
            if not tohook:
                if not isinstance(hashtags,list):
                    hashtags = [hashtags]

                random.shuffle(hashtags)

                for tag in hashtags:

                    self.status += 1
                    hashtag = Hashtag(tag,self.driver)
                    ht_urls = flat_array(hashtag.get_pics_urls(hashtags_amount).values())

                    random.shuffle(ht_urls)
                    likers_list = []

                    for url in ht_urls:

                        self.status += 1
                        self.load_data()
                        post = Post(url,self.driver)
                        likers_list = post.get_picture_likers(likers_per_picture)
                        likers_list = [liker for liker in likers_list if liker not in self.already_analysed and liker not in self.blacklist] ## <<<<<<< NOVO
                        counter = len(likers_list)


                        random.shuffle(likers_list)
                        for liker in likers_list:
                            self.status += 1
                            user = User(liker,self.driver)
                            ok = user.analysis1(self.lead,5)
                            self.already_analysed_queue.append(user.username)

                            if ok:
                                if self.lead.analyse(user) and liker not in self.already_commited:
                                    self.already_commited_queue.append(user.username)
                                    print(f"{user.username.title()} aprovado!")

                                    self.commit(user)
                        self.save()

        except TimeoutException:
            print(f"{datetime.datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%Y-%m-%d %H:%M:%S')} - Timeout!")
            self.routine_timeouts += 1

        except:
            n = datetime.datetime.now(pytz.timezone("America/Sao_Paulo")).strftime("%Y-%m-%d %Hh%Mm%Ss")
            self.driver.save_screenshot(f'errors/Error{n}.png')
            raise




    def commit(self,user):

        commited = False

        now = datetime.datetime.now(pytz.timezone("America/Sao_Paulo"))
        when = now + self.schedule_step


        if user.is_private:
            # FOLLOW
            self.action(username = user.username,
                        type = "follow",
                        action = user.follow,
                        now = now,
                        when = when,
                        post = ""
                        )

        else:
            urls = []
            n_of_posts = np.random.randint(1,4)

            urls = random.sample(user.posts_urls[:ceiling(8,user.posts)], k = n_of_posts)
            print(f"URLS: {urls}")

            # FOLLOW

            self.action(username = user.username,
                        type = "follow",
                        action = user.follow,
                        now = now,
                        when = when,
                        post = ""
                        )

            # LIKE
            for url in urls:
                post = Post(url,self.driver)

                self.action(username = user.username,
                            type = "like",
                            action = post.like,
                            now = now,
                            when = when,
                            post = url,
                            schedule_reverse_action=False,
                            )
