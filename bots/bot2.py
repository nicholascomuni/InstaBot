from insta_modules.user.user import User
from insta_modules.hashtag.hashtag import Hashtag
from insta_modules.post.post import Post
from insta_modules.lead.lead import Lead
from insta_modules.util import load_lead_profile
from insta_modules.util import ceiling
from instabot import *
from ast import literal_eval
import pytz

import configparser
import threading
import trace
import sys

from selenium.common.exceptions import TimeoutException


class Bot(InstagramBot):
    def __init__(self,config):
        InstagramBot.__init__(self,config)
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

    def run(self):
        countr1 = 0

        while True:
            countr1 += 1
            self.task("Analyse_results",self.analyse_results,"08:32","08:47",   once=True)
            self.task("Schedule1",self.perform_schedule,     "08:48","10:44",   once=True)
            self.task("Routine1",self.routine,               "10:55","15:02",   args=(literal_eval(self.config['hashtags_list']),40,20,eval(self.config['commit_hook'])))
            self.task("Schedule2",self.perform_schedule,     "15:19","16:34",   once=True)
            self.task("Routine2",self.routine,               "16:14","20:03",   args=(literal_eval(self.config['hashtags_list']),40,20,eval(self.config['commit_hook'])))
            self.task("Routine3",self.routine,               "21:14","23:42",   args=(literal_eval(self.config['hashtags_list']),40,20,eval(self.config['commit_hook'])))
            self.task("Schedule3",self.perform_schedule,     "00:21","01:27",   once=True)
            self.task("Backup",self.s3_backup,               "03:21","03:34",   once=True)
            self.task("Rebalance",self.rebalance,            "03:41","03:48",   once=True)


            if self.stop_robot:
                self.stop()
                return


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

                                    now = datetime.datetime.now(pytz.timezone("America/Sao_Paulo"))
                                    if all(self.check_commit_availability()):
                                        self.already_commited_queue.append(user.username)
                                        posts = self.commit(user)
                                        when = now + self.schedule_step

                                        if user.is_private:
                                            self.schedule_action(user.username,when,posts,"Unfollow")
                                            self.commit_queue = self.commit_queue.append({'user':user.username,'action':'follow','datetime':now},ignore_index = True)
                                            self.save_commit_queue()
                                        else:
                                            self.schedule_action(user.username,when,posts,"Unlike")
                                            self.schedule_action(user.username,when,posts,"Unfollow")
                                            self.commit_queue = self.commit_queue.append({'user':user.username,'action':'like','datetime':now},ignore_index = True)
                                            self.commit_queue = self.commit_queue.append({'user':user.username,'action':'follow','datetime':now},ignore_index = True)
                                            self.save_commit_queue()
                                    else:
                                        print("Not commited")
                                        self.sleep(30)
                                        self.save_lead(user.username)
                                else:
                                    pass

                        self.save()
            else:
                # -------------------------------------------------- IMPORTANTÍSSIMO REVISAR ------------------------------------------------------
                print("Commiting already hooked")
                # carrega likers list
                cntr = 0
                while True:
                    self.status += 1
                    with open(f"client_data/{self.username}/data/to_hook.txt",'r') as file:
                        plain_text = file.read()

                    likers_list = plain_text.split(",")
                    likers_list = [liker for liker in likers_list if liker != "" and liker != " "]
                    if len(likers_list) < 2:
                        print("To Hook finished")
                        break

                    for liker in likers_list:
                        self.status += 1
                        print(liker)
                        time.sleep(3)
                        user = User(liker,self.driver)


                        now = datetime.datetime.now(pytz.timezone("America/Sao_Paulo"))
                        if all(self.check_commit_availability()) and liker not in self.already_commited :
                            cntr += 1
                            self.already_commited_queue.append(user.username)
                            with open(f"client_data/{self.username}/data/to_hook.txt",'r') as file:
                                plain_text = file.read()

                            plain_text = plain_text.replace(f"{liker},","")

                            with open(f"client_data/{self.username}/data/to_hook.txt",'w') as file:
                                file.write(plain_text)

                            posts = self.commit(user)
                            when = now + self.schedule_step

                            if user.is_private:
                                self.schedule_action(user.username,when,posts,"Unfollow")
                                self.commit_queue = self.commit_queue.append({'user':user.username,'action':'follow','datetime':now},ignore_index = True)
                                self.save_commit_queue()
                            else:

                                self.schedule_action(user.username,when,posts,"Unfollow")
                                self.commit_queue = self.commit_queue.append({'user':user.username,'action':'follow','datetime':now},ignore_index = True)
                                self.save_commit_queue()
                        else:
                            print("Not commited")
                            self.sleep(30)
                            self.save_lead(user.username)

                        if cntr > 10:
                            print("Salvando dados...")
                            self.save()
                            cntr = 0



        except:
            n = datetime.datetime.now(pytz.timezone("America/Sao_Paulo")).strftime("%Y-%m-%d %Hh%Mm%Ss")
            self.driver.save_screenshot(f'Error{n}.png')
            raise


    def perform_schedule(self):
        print("Commiting Schedule!!")
        now = datetime.datetime.now(pytz.timezone("America/Sao_Paulo"))
        schedule = self.load_schedule()
        self.load_commit_queue()
        to_commit = schedule.loc[schedule.datetime < now,:]

        for index,row in to_commit.iterrows():
            self.status += 1
            status = []
            now = datetime.datetime.now(pytz.timezone("America/Sao_Paulo"))

            if all(self.check_commit_availability('dislike')):
                if row.action == "Unfollow":
                    user = User(row.user,self.driver)
                    unf_status = user.unfollow()
                    if unf_status:
                        self.commit_queue = self.commit_queue.append({'user':user.username,'action':'unfollow','datetime':now},ignore_index = True)
                        self.save_commit_queue()
                        self.status += 1
                        time.sleep(0.5)
                        self.log(f"{index}: Unfollowed")

                        self.status += 1
                        schedule.drop(index,inplace = True)
                        self.save_schedule(schedule)
                        time.sleep(0.494)

                elif row.action == "Unlike":
                    post = Post(row.posts,self.driver)
                    unlk_status = post.unlike()
                    if unlk_status:
                        self.commit_queue = self.commit_queue.append({'user':row.user,'action':'unlike','datetime':now},ignore_index = True)
                        self.save_commit_queue()
                        self.status += 1
                        self.log(f"{index}/{row.posts}: Unliked")
                        time.sleep(0.5)
                        self.status += 1
                        schedule.drop(index,inplace = True)
                        self.save_schedule(schedule)
                        time.sleep(0.765)
                        self.status += 1


                else:
                    print(f"Falha ao executar schedule de {row.user}")
            else:
                self.sleep(20)
                print("Schedule Not commited")
