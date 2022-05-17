from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
from cryptography.fernet import InvalidToken

import time
import datetime
import pandas as pd
import numpy as np
import ast
import pickle
import random
import platform
import os
import boto3
import requests

from insta_modules.user.user import User
from insta_modules.hashtag.hashtag import Hashtag
from insta_modules.post.post import Post
from insta_modules.lead.lead import Lead
from insta_modules.util import find_element
from utils.crypto import *

from insta_modules.util import flat_array
from insta_modules.util import InstagramResponse_Exception,FailedToLogin_Exception
from insta_modules.util import checkEqual
from insta_modules.util import shutdown
from insta_modules.util import timeout_decorator
from pyvirtualdisplay import Display
from selenium.common.exceptions import TimeoutException
from insta_modules.util import ceiling

import threading
import trace
import sys
import pytz

class task(threading.Thread):
    def __init__(self,name, *args, **keywords):
        threading.Thread.__init__(self, *args, **keywords)
        self.name = name
        self.killed = False

    def start(self):
        self.__run_backup = self.run
        self.run = self.__run
        threading.Thread.start(self)
        print(f"Starting {self.name} - {datetime.datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%d/%m/%Y - %H:%M:%S')}")

    def __run(self):
        try:
            sys.settrace(self.globaltrace)
            self.__run_backup()
            self.run = self.__run_backup

        except TimeoutException:
            print("TimeoutException !!!!")
            self.kill()

    def globaltrace(self, frame, event, arg):
        if event == 'call':
            return self.localtrace
        else:
            return None

    def localtrace(self, frame, event, arg):
        if self.killed:
            if event == 'line':
                raise SystemExit()
        return self.localtrace

    def kill(self):
        print(f"Killing: {self.name} - {datetime.datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%d/%m/%Y - %H:%M:%S')}")
        self.killed = True

class InstagramBot:
    def __init__(self,config):

        self.config = config
        self.username = config['username']
        self.password = config['password']

        self.driver = ""
        self.system = platform.system()
        self.lang = ""
        self.male_names_list = []
        self.blacklist = []
        self.hashtags_blacklist = eval(config['hashtags_blacklist'])
        self.lead = Lead(config)
        self.already_analysed_queue = []
        self.already_commited_queue = []

        self.already_analysed = []
        self.already_commited = []

        self.commit_queue = pd.DataFrame(columns=["user","datetime","action"])

        self.schedule_step = datetime.timedelta(**eval(config['schedule_step']))
        self.days_to_unfollow = self.config.getint('days_to_unfollow')

        self.started_at = datetime.datetime.now(pytz.timezone("America/Sao_Paulo"))
        self.last_checkpoint = datetime.datetime.now(pytz.timezone("America/Sao_Paulo"))

        self.since_init = 0
        self.runtime = datetime.timedelta(0)
        self.runtime_resetable = datetime.timedelta(0)

        self.target_step = ""
        self.config_dict = {}
        self.allow_interface = False
        self.bot_started = False

        self.s3 = False

        self.use_proxy = eval(self.config["use_proxy"])
        if self.use_proxy:
            self.proxy = self.config['proxy']

        """
        self.load_general_config()
        self.init_webdriver(self.use_proxy)
        self.load_session()
        self.assert_login()
        self.driver.set_page_load_timeout(10)"""
    def restart(self):
        self.stop()
        print("Restarting in 2 seconds...")
        time.sleep(2)
        print("Restarting...")
        self.init_bot()

    def init_bot(self):
        self.load_general_config()
        self.init_webdriver(self.use_proxy)

        if not self.check_instagram_response():
            print("Failed to Establish Conection with Instagram server!\n")
            raise InstagramResponse_Exception("Failed to Establish Conection with Instagram server!")


        self.load_session()
        print("Login...",end="")
        if not self.assert_login():
            print("FAIL")
            raise FailedToLogin_Exception("Failed to Login!")
        else:
            print("OK")

        self.driver.set_page_load_timeout(5)
        self.test_proxy()
        self.rebalance()
        self.log_task("Robot started\n")
        self.allow_interface = True
        return True

    def init_webdriver(self,proxy=False):

        if self.system == "Windows":
            print("WINDOWS")
            # -----------------------------------------
            if proxy:
                print("Using Proxy")
                chrome_options = webdriver.ChromeOptions()
                chrome_options.add_argument('--proxy-server=%s' % self.proxy)

                self.driver = webdriver.Chrome(executable_path = os.getcwd() + "/drivers/windows/chromedriver",options=chrome_options)
            else:
                self.driver = webdriver.Chrome(executable_path = os.getcwd() + "/drivers/windows/chromedriver")
            # -----------------------------------------
            self.driver.maximize_window()



        elif self.system == "Linux":
            print("LINUX")
            display = Display(visible=0, size=(1366, 768))
            display.start()
            # -----------------------------------------
            if proxy:
                print("Using Proxy")
                chrome_options = webdriver.ChromeOptions()
                chrome_options.add_argument('--proxy-server=%s' % self.proxy)

                self.driver = webdriver.Chrome(options=chrome_options)
            else:
                self.driver = webdriver.Chrome()
                # -----------------------------------------
            self.driver.maximize_window()

    def load_session(self):
        try:
            self.driver.get("https://instagram.com")
            time.sleep(1)
            for cookie in pickle.load(open(f"client_data/{self.username}/session/loginsession.pkl", "rb")):
                self.driver.add_cookie(cookie)

        except:
            print("Creating cookies file...",end="")
            if self.login():
                time.sleep(5)
                pickle.dump(self.driver.get_cookies() , open(f"client_data/{self.username}/session/loginsession.pkl","wb"))
                time.sleep(0.5)
            else:
                self.closeBrowser()
                raise FailedToLogin_Exception("Failed to Login!")




    def login(self,manual=True):
        self.driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(2)
        username_element = self.driver.find_element_by_xpath("//input[@name='username']")
        username_element.clear()
        username_element.send_keys(self.username)

        if manual:
            public_key = self.config["public_key"].encode()
            n_tentativas = 0
            while True:
                try:
                    n_tentativas += 1
                    secret_key = input("\nDigite a Secret Key: ").encode()
                    password = decrypt_fernet(public_key,secret_key)
                    break
                except InvalidToken:
                    print("InvalidToken")
                    if n_tentativas > 3:
                        return False
        else:
            password = self.password

        password_element = self.driver.find_element_by_xpath("//input[@name='password']")
        password_element.clear()
        password_element.send_keys(password)
        password_element.send_keys(Keys.RETURN)
        time.sleep(1)
        self.handle_login_errors()
        self.handle_suspicius_login_attempt()
        return True


    def handle_login_errors(self):
        try:
            error_element = self.driver.find_element_by_id("slfErrorAlert")
            error_msg = error_element.text
            print(error_msg)
            raise FailedToLogin_Exception(error_msg)
            return False
        except NoSuchElementException:
            return True

    def handle_suspicius_login_attempt(self,command_line=True):
        try:
            suspicius_login = self.driver.find_element_by_xpath("//p[text() = 'Suspicious Login Attempt']")
            while True:
                try:
                    if not command_line:
                        print(".",end="",flush=True)
                        try:
                            suspicius_login = self.driver.find_element_by_xpath("//p[text() = 'Suspicious Login Attempt']")
                        except:
                            suspicius_login = self.driver.find_element_by_xpath("//h2[text() = 'Enter Your Security Code']")
                        time.sleep(1)
                    else:
                        try:
                            suspicius_login = self.driver.find_element_by_xpath("//p[text() = 'Suspicious Login Attempt']")
                        except:
                            suspicius_login = self.driver.find_element_by_xpath("//h2[text() = 'Enter Your Security Code']")
                        time.sleep(1)
                except:
                    break
        except:
            pass

    def save_commit_queue(self):
        with open(f'client_data/{self.username}/data/commit_queue.pk','wb+') as file:
            pickle.dump(self.commit_queue, file)

    def load_commit_queue(self):
        try:
            with open(f'client_data/{self.username}/data/commit_queue.pk','rb') as file:
                self.commit_queue = pickle.load(file)
        except:
            print("commit_queue not created yet")


    def set_blacklist(self):
        with open('config/blacklist.txt','r') as file:
            bl = file.read()
            bl = bl.split('\n')
            self.blacklist = self.blacklist + bl
        self.set_followers_blacklist()

    def set_hashtags_blacklist(self):
        try:
            with open("config/hashtags_blacklist.txt",'r') as file:
                htl = file.read().split('\n')
                self.hashtags_blacklist = [ht.strip() for ht in htl]
        except:
            print("hashtags_blacklist.txt não foi encontrado.")

    def save_blacklist(self):
        with open(f"{self.username}_saved/blacklist.txt",'w') as file:
            for person in self.blacklist:
                file.write(f"{person},")

    def load_blacklist(self,filename):
        with open(f"{filename}.txt",'r') as file:
            blacklist = file.read()
            self.blacklist = blacklist.split(',')

    def set_followers_blacklist(self):
        user = User(self.username,self.driver)
        followers = user.get_list_of_followers()
        following = user.get_list_of_following()
        all = list(set(followers+following))
        self.blacklist = self.blacklist + all
        self.blacklist = list(set(self.blacklist))

    def get_language(self):
        self.driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(2)

        html = self.driver.find_element_by_tag_name('html')
        self.lang = html.get_attribute('lang')


    def get_commit_status(self):
        now = datetime.datetime.now(pytz.timezone("America/Sao_Paulo"))
        dtf = self.commit_queue
        like = False
        follow = False
        # ---------------------------------
        unlike = False
        unfollow = False
        # ---------------------------------

        mask_hour = now - dtf.datetime < datetime.timedelta(hours = 1)
        mask_day = now - dtf.datetime < datetime.timedelta(days = 1)

        mask_likes = dtf.action == "like"
        mask_follows = dtf.action == "follow"
        # ---------------------------------
        mask_unlikes = dtf.action == "unlike"
        mask_unfollows = dtf.action == "unfollow"
        # ---------------------------------

        likes_hour = dtf.loc[mask_hour & mask_likes,:]
        likes_day = dtf.loc[mask_day & mask_likes,:]
        follows_hour = dtf.loc[mask_hour & mask_follows,:]
        follows_day = dtf.loc[mask_day & mask_follows,:]

        # ---------------------------------
        unlikes_hour = dtf.loc[mask_hour & mask_unlikes,:]
        unlikes_day = dtf.loc[mask_day & mask_unlikes,:]
        unfollows_hour = dtf.loc[mask_hour & mask_unfollows,:]
        unfollows_day = dtf.loc[mask_day & mask_unfollows,:]
        # ---------------------------------


        print(f"likes_hour: {len(likes_hour)}\nlikes_day: {len(likes_day)}\nfollows_hour: {len(follows_hour)}\nfollows_day: {len(follows_day)}\nunlikes_hour: {len(unlikes_hour)}\nunfollows_hour: {len(unfollows_hour)}")

    def check_commit_availability(self,kind = "like"):

        now = datetime.datetime.now(pytz.timezone("America/Sao_Paulo"))
        dtf = self.commit_queue

        mask_hour = now - dtf.datetime < datetime.timedelta(hours = 1)
        mask_day = now - dtf.datetime < datetime.timedelta(days = 1)

        mask_action = dtf.action == kind

        action_hour = dtf.loc[mask_hour & mask_action,:]
        action_day = dtf.loc[mask_day & mask_action,:]

        if len(action_hour) < self.config_dict[f'{kind + "s"}_per_hour'] and len(action_day) < self.config_dict[f'{kind + "s"}_per_day']:
            b = self.config_dict[f'{kind + "s"}_per_hour']
            return True
        else:
            b = self.config_dict[f'{kind + "s"}_per_hour']
            return False




    def check_commit_availability_old(self,kind = "like"):
        now = datetime.datetime.now(pytz.timezone("America/Sao_Paulo"))
        dtf = self.commit_queue

        like = False
        follow = False
        unlike = False
        unfollow = False

        mask_hour = now - dtf.datetime < datetime.timedelta(hours = 1)
        mask_day = now - dtf.datetime < datetime.timedelta(days = 1)

        mask_likes = dtf.action == "like"
        mask_follows = dtf.action == "follow"
        # ----- NEW ------
        if kind == "dislike":
            mask_unlikes = dtf.action == "unlike"
            mask_unfollows = dtf.action == "unfollow"
        # ---------------

        likes_hour = dtf.loc[mask_hour & mask_likes,:]
        likes_day = dtf.loc[mask_day & mask_likes,:]
        follows_hour = dtf.loc[mask_hour & mask_follows,:]
        follows_day = dtf.loc[mask_day & mask_follows,:]

        # ------- NEW --------
        if kind == "dislike":
            unlikes_hour = dtf.loc[mask_hour & mask_unlikes,:]
            unlikes_day = dtf.loc[mask_day & mask_unlikes,:]
            unfollows_hour = dtf.loc[mask_hour & mask_unfollows,:]
            unfollows_day = dtf.loc[mask_day & mask_unfollows,:]
        # --------------------


        if len(likes_day) >= self.info_likes_per_day:
            print("Max likes_day")

        if len(follows_day) >= self.info_follows_per_day:
            print("Max_follows_day")

        # ----------- NEW ------------
        if kind == "dislike":
            if len(unlikes_day) >= self.info_unlikes_per_day:
                print("Max unlikes_day")

            if len(unfollows_day) >= self.info_unfollows_per_day:
                print("Max_unfollows_day")
        # ---------------------------


        if len(likes_hour) < self.info_likes_per_hour and len(likes_day) < self.info_likes_per_day:
            like = True
        else:
            like = False

        if len(follows_hour) < self.info_follows_per_hour and len(follows_day) < self.info_follows_per_day:
            follow = True
        else:
            follow = False

        # --------------- NEW --------------
        if kind == "dislike":
            if len(unlikes_hour) < self.info_unlikes_per_hour and len(unlikes_day) < self.info_unlikes_per_day:
                unlike = True
            else:
                unlike = False
            if len(unfollows_hour) < self.info_unfollows_per_hour and len(unfollows_day) < self.info_unfollows_per_day:
                unfollow = True
            else:
                unfollow = False
        # ----------------------------------
        if kind == "like":
            return (like,follow)
        elif kind == "dislike":
            return (unlike,unfollow)




    def save_user_test(self,user):
        with open("data/testeuser.txt",'a+') as file:
            file.write(f"{user},")

    def farm_leads(self,hashtags,hashtags_amount):
        if not isinstance(hashtags,list):
            hashtags = [hashtags]

        for tag in hashtags:
            hashtag = Hashtag(tag,self.driver)
            ht_urls = hashtag.get_pics_urls(hashtags_amount)['top_posts']
            random.shuffle(ht_urls)

            likers_list = []
            for url in ht_urls:
                self.load_data()
                post = Post(url,self.driver)
                likers_list = post.get_picture_likers(30)
                for liker in likers_list:
                    self.save_user_test(liker)



    def log(self,text):
        with open(f"client_data/{self.username}/data/log.txt",'a+') as file:
            file.write(f"{text}\n")

    def log_task(self,text):
        with open(f"client_data/{self.username}/data/task_logs.txt",'a+') as file:
            file.write(f"{datetime.datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%Y-%m-%d %H:%M:%S')} - {text}")

    def set_lead_profile(self,lead):
        self.lead = lead

    def filter_lead(self,user):
        filter = all([(user.gender == "Female"),
        (0.5 < user.ff_ratio < 4),
        (200 < user.followers < 5000),
        (150 < user.following < 5000),
        (user.posts > 10),
        (user.comments_mean > 0),
        (len([ht for ht in user.hashtags if ht in self.hashtags_blacklist]) == 0),
        ])

        if filter:
            print(f"{user.first_name}: APROVADA !")
            return True
        else:
            return False

    def load_data(self):
        try:
            with open(f"client_data/{self.username}/data/analysed_users.txt",'r') as file:
                analysed = file.read()
                self.already_analysed = analysed.split(',')

        except:
            print("Empty")

        try:
            with open(f"client_data/{self.username}/data/hooked_users.txt",'r') as file:
                hooked = file.read()
                self.already_commited = hooked.split(',')
        except:
            pass

    def save(self):
        if len(self.already_analysed_queue) > 0:
            with open(f"client_data/{self.username}/data/analysed_users.txt",'a+') as file:
                for user in self.already_analysed_queue:
                    file.write(f'{user},')
            self.already_analysed_queue.clear()

        if len(self.already_commited_queue) > 0:
            with open(f"client_data/{self.username}/data/hooked_users.txt",'a+') as file:
                for user in self.already_commited_queue:
                    file.write(f'{user},')
            self.already_commited_queue.clear()

    def save_lead(self,username):
        with open(f"client_data/{self.username}/data/to_hook.txt",'a+') as file:
            file.write(f'{username},')


    def schedule_action(self,username,datetime,posts,action,editable=True):
        try:
            dtf = self.load_schedule()
        except:
            dtf = pd.DataFrame([],columns = ['user','datetime','posts','action','editable'])
            dtf['datetime'] = dtf.datetime.astype(np.datetime64)


        new_row = pd.Series({'user':username,'datetime':datetime,'posts':posts,'action':action,'editable':editable})
        dtf = dtf.append(new_row,ignore_index=True)
        self.save_schedule(dtf)


    def load_general_config(self):
        try:
            with open(f'client_data/{self.username}/data/general_config.pk','rb') as file:
                self.general_config = pickle.load(file)

        except:
            print("General config not created yet, Creating...")
            self.general_config = {}

            with open(f'client_data/{self.username}/data/general_config.pk','wb+') as file:
                pickle.dump(self.general_config, file)

            time.sleep(0.5)

    def save_general_config(self):
        with open(f'client_data/{self.username}/data/general_config.pk','wb+') as file:
            pickle.dump(self.general_config, file)

        time.sleep(0.5)



    def save_total_runtime(self):
        try:
            self.general_config['runtime'] = self.general_config['runtime'] + self.get_resetable_runtime()
        except:
            self.general_config['runtime'] = self.get_resetable_runtime()


        self.save_general_config()
        return self.general_config["runtime"]

    def get_runtime(self):
        return datetime.datetime.now(pytz.timezone("America/Sao_Paulo")) - self.started_at



    def get_resetable_runtime(self):
        rt = datetime.datetime.now(pytz.timezone("America/Sao_Paulo")) - self.last_checkpoint
        self.last_checkpoint = datetime.datetime.now(pytz.timezone("America/Sao_Paulo"))

        return rt


    def closeBrowser(self):
        self.driver.close()

    def analyse_results(self,level=1):
        self.load_data()
        user = User(self.username,self.driver)
        user.get_user_info()

        followers = user.get_list_of_followers()
        source_level1 = [user for user in self.already_commited if user in followers and user != ""] # Que seguiram


        if level > 1:
            user.medium_posts_analysis()
            likers_list = pd.DataFrame(user.all_likers)

            source_level2 = [user for user in source_level1 if user in likers_list.index.values] # Que seguiram e curtiram uma foto
            source_level3 = [user for user in source_level2 if likers_list.loc[user].likes >= 3] # Que seguiram e curtiram mais de 3 fotos

            source_level1 = [user for user in source_level1 if user not in source_level2]
            source_level2 = [user for user in source_level2 if user not in source_level3]

        schedule = self.load_schedule()


        to_schedule = pd.DataFrame([],columns = ['user','datetime','posts','action','editable'])
        to_schedule['datetime'] = to_schedule.datetime.astype(np.datetime64)

        for user in source_level1:
            if user in schedule.user.values:
                tasks = schedule[schedule.user == user]
                droped = False
                for index,row in tasks.iterrows():
                    if row.editable == True:
                        # Drop
                        droped = True
                        print(f"Dropping: {row.user} - {row.action}")
                        schedule.drop(index,inplace = True)
                        """
                        now = datetime.datetime.now(pytz.timezone("America/Sao_Paulo"))
                        when = now + datetime.timedelta(days=10)
                        finish_row = pd.Series({'user':user,'datetime':when,'posts':"",'action':"Unfollow","editable":False})
                        to_schedule = to_schedule.append(finish_row,ignore_index= True)"""
                        # ---------------------------
                if droped:
                    # Independentemente da quantida de ações schedule dropadas ele vai realizar apenas um schedule para o futuro
                    now = datetime.datetime.now(pytz.timezone("America/Sao_Paulo"))
                    when = now + datetime.timedelta(days=self.days_to_unfollow)
                    finish_row = pd.Series({'user':user,'datetime':when,'posts':"",'action':"Unfollow","editable":False})
                    to_schedule = to_schedule.append(finish_row,ignore_index= True)


        schedule = schedule.append(to_schedule,ignore_index = True)

        if level > 1:
            for user in source_level2:
                pass
            for user in source_level3:
                pass


        self.save_schedule(schedule)

        print("Analyse completed!")
        return
        # -------------------------------------------- #

    def save_schedule(self,dtf):
        with open(f'client_data/{self.username}/data/schedule.pk','wb+') as file:
            pickle.dump(dtf, file)


    def load_schedule(self):
        with open(f'client_data/{self.username}/data/schedule.pk','rb') as file:
            return pickle.load(file)


    def assert_login(self):
        """
        self.driver.get("https://www.instagram.com/?__a=1")
        time.sleep(1)
        pre = self.driver.find_element_by_tag_name("pre").text
        if pre == "{}":
            return True
        else:
            return False
        """
        return True

    def get_ip(self):
        response = requests.get("http://httpbin.org/ip")

        if response.status_code == 200:
            return response.json()['origin']
        else:
            return False

    def test_proxy(self):
        return True
        """
        print("Testing proxy...")
        if self.check_internet_connection():
            if self.use_proxy:
                ip = self.get_ip()
                print(f"PROXY: {self.proxy}")
                print(f"Your IP: {ip}")
            else:
                print("Proxy deactivated, getting current ip...")
                ip = self.get_ip()
                print(f"Your IP: {ip}")
        else:
            print("Internet not connected!")"""


    def check_internet_connection(self):
        response = requests.get("http://216.58.192.142")

        if response.status_code == 200:
            return True
        else:
            return False

    def check_instagram_response(self):
        response = requests.get("http://instagram.com")

        if response.status_code == 200:
            return True
        else:
            return False

    def task(self,name,func,inicio,termino,args=None,once=False,msg=False): # Foi inteiramente alterada, ver versões anteriores 7.2

        if once:
            start_hour,start_minute = inicio.split(":")
            end_hour,end_minute = termino.split(":")

            now = datetime.datetime.now(pytz.timezone("America/Sao_Paulo"))
            now = datetime.timedelta(hours=now.hour,minutes = now.minute)

            start = datetime.timedelta(hours=int(start_hour),minutes=int(start_minute))
            end = datetime.timedelta(hours=int(end_hour),minutes=int(end_minute))

            if name not in self.task_status.keys():
                self.task_status[name] = False


            if now >= start and now < end and not self.task_status[name]:

                if args != None:
                    self.tasks[name] = task(name,target=func,args=args,daemon=True)
                else:
                    self.tasks[name] = task(name,target=func,daemon=True)

                self.task_status[name] = True
                self.tasks[name].start()
                self.log_task(f"Starting {name}\n")

            elif now >= end and self.task_status[name]:
                self.task_status[name] = False
                self.tasks[name].kill()
                self.log_task(f"Killing {name}\n")


        else:
            start_hour,start_minute = inicio.split(":")
            end_hour,end_minute = termino.split(":")

            now = datetime.datetime.now(pytz.timezone("America/Sao_Paulo"))
            now = datetime.timedelta(hours=now.hour,minutes = now.minute)

            start = datetime.timedelta(hours=int(start_hour),minutes=int(start_minute))
            end = datetime.timedelta(hours=int(end_hour),minutes=int(end_minute))


            if name in self.tasks.keys():
                if now >= start and now < end and not self.tasks[name].isAlive():

                    if args != None:
                        self.tasks[name] = task(name,target=func,args=args,daemon=True)
                    else:
                        self.tasks[name] = task(name,target=func,daemon=True)

                    self.tasks[name].start()
                    self.log_task(f"Starting {name}\n")

                elif now >= end and self.tasks[name].isAlive():
                    self.tasks[name].kill()
                    self.log_task(f"Killing {name}\n")

            else:
                if now >= start and now < end:

                    if args != None:
                        self.tasks[name] = task(name,target=func,args=args,daemon=True)
                    else:
                        self.tasks[name] = task(name,target=func,daemon=True)

                    self.tasks[name].start()
                    self.log_task(f"Starting {name}\n")



    def stop(self):
        for task in self.tasks.keys():
            if self.tasks[task].isAlive():
                self.tasks[task].kill()
                self.task_status[task] = False

        time.sleep(3)
        self.closeBrowser()
        self.log_task("Robot shutdown\n")
        return

    def sleep(self,time_minutes):
        print(f"Robot going to sleep for {time_minutes}min ...")
        self.sleeping = True
        time.sleep(time_minutes*60)
        print("Robot waking up!")
        self.sleeping = False

    ## -------------- AWS S3 -----------------

    def s3_backup(self):
        print("Making backup... dont shutdown the bot")
        id,sk = self.load_credentials()
        self.s3 = self.S3Login(id,sk)
        folder = f"client_data/{self.username}/data"

        self.uploadDirectory(folder,"instabucket1",folder)
        print("Backup finished!")
        return True

    def load_credentials(self):
        with open("config/accessKeys.csv","r") as file:
            raw = file.read()
        dct = ast.literal_eval(raw)
        return dct["Access key ID"],dct["Secret access key"]

    def S3Login(self,Key_id,Secret_key):
        s3 = boto3.client(
        's3',
        aws_access_key_id=Key_id,
        aws_secret_access_key=Secret_key)
        try:
            s3.list_buckets()
            return s3
        except:
            return False


    def uploadDirectory(self,path,bucketname,s3path):
        if self.s3:
            for root,dirs,files in os.walk(path):
                for file in files:
                    self.s3.upload_file(os.path.join(root,file),bucketname,f"{s3path}/{file}")
        else:
            print("Amazon s3 not logged in")


    def get_config_balanced(self,key):
        actual_action = self.config.getint(key)
        target_action = self.config.getint(f'{key}_target')

        action_inc = (target_action - actual_action) / self.target_step
        action_total_inc = round(action_inc * (self.total_runtime.days))
        balanced_action = ceiling(actual_action + action_total_inc,target_action)
        print(f"{key}: {balanced_action}")

        return balanced_action

    def rebalance(self):

        print("Balanceando limites...")

        self.target_step = self.config.getint('target_step')
        self.total_runtime = self.save_total_runtime()

        if self.target_step == "":
            print("Erro na função instabot.py/rebalance(linha 828) - Não foi possível carregar o target_step!!!")
            self.tartget_step = 90

        """
        self.info_likes_per_hour     =  self.get_config_balanced('likes_per_hour')
        self.info_likes_per_day      =  self.get_config_balanced('likes_per_day')
        self.info_follows_per_hour   =  self.get_config_balanced('follows_per_hour')
        self.info_follows_per_day    =  self.get_config_balanced('follows_per_day')

        self.info_likes_per_hour     =  self.get_config_balanced('unlikes_per_hour')
        self.info_likes_per_day      =  self.get_config_balanced('unlikes_per_day')
        self.info_follows_per_hour   =  self.get_config_balanced('unfollows_per_hour')
        self.info_follows_per_day    =  self.get_config_balanced('unfollows_per_day')"""


        self.config_dict['likes_per_hour'] =  self.get_config_balanced('likes_per_hour')
        self.config_dict['likes_per_day'] =  self.get_config_balanced('likes_per_day')
        self.config_dict['follows_per_hour'] =  self.get_config_balanced('follows_per_hour')
        self.config_dict['follows_per_day'] =  self.get_config_balanced('follows_per_day')

        self.config_dict['unlikes_per_hour'] =  self.get_config_balanced('unlikes_per_hour')
        self.config_dict['unlikes_per_day'] =  self.get_config_balanced('unlikes_per_day')
        self.config_dict['unfollows_per_hour'] =  self.get_config_balanced('unfollows_per_hour')
        self.config_dict['unfollows_per_day'] =  self.get_config_balanced('unfollows_per_day')

        print("Balanceamento finalizado...")
        #self.info_unlikes_per_hour   =  self.config.getint("unlikes_per_hour")
        #self.info_unlikes_per_day    =  self.config.getint("unlikes_per_day")
        #self.info_unfollows_per_hour =  self.config.getint("unfollows_per_hour")
        #self.info_unfollows_per_day  =  self.config.getint("unfollows_per_day")


        """
        print("\nBEGGINING")
        print(f"likes_per_hour: {self.config.getint('likes_per_hour')}\nlikes_per_day: {self.config.getint('likes_per_day')}\nfollows_per_hour: {self.config.getint('follows_per_hour')}\nfollows_per_day: {self.config.getint('follows_per_day')}")

        print("\nTARGETS")
        print(f"likes_per_hour: {self.config.getint('likes_per_hour_target')}\nlikes_per_day: {self.config.getint('likes_per_day_target')}\nfollows_per_hour: {self.config.getint('follows_per_hour_target')}\nfollows_per_day: {self.config.getint('follows_per_day_target')}")

        print("\nAFTER BALANCE")
        print(f"likes_per_hour TARGET: {likes_per_hour}\nlikes_per_day TARGET: {likes_per_day}\nfollows_per_hour TARGET: {follows_per_hour}\nfollows_per_day TARGET: {follows_per_day}")"""


    def check_page_not_available(self):
        elements = self.driver.find_elements_by_tag_name("h2")
        for element in elements:
            if element.text == "Sorry, this page isn't available.":
                return True
        return False

    def analyse_effiency(self):
        while1 = np.array(self.while1_timer).mean()
        while2 = np.array(self.while2_timer).mean()

        analyse_user_timer = np.array(self.analyse_user_timer).mean()
        commit_timer = np.array(self.commit_timer).mean()

        users_t = [] # List of users to test
        for user in users_t:
            try:
                print(f"Trying {user}")
                us = User(user,self.driver)
                t1 = time.time()
                us.user_root()
                self.user_root_timer.append(round(time.time()-t1,2))
            except:
                print("ERRO")
        self.stop()


        userroot = np.array(self.user_root_timer).mean()
        print(f"\nWhile1: {while1}\nWhile2: {while2}\nUser_root: {userroot}\nAnalyse User: {analyse_user_timer}\nCommit: {commit_timer}")



# -------------------------------------------------------------------------------------------------------------------------------------------

    def action(self,username,type,action,now,when,post,schedule_action = True,schedule_reverse_action = True):

        if self.check_commit_availability(type):
            if type == "like" or type == "unlike":
                print(f"{type[:-1]}ing {username}")
            else:
                print(f"{type}ing {username}")

            if action():
                if schedule_reverse_action:
                    self.schedule_action(username,when,post,f"Un{type}")
                self.commit_queue = self.commit_queue.append({'user':username,'action':type,'datetime':now},ignore_index = True)
                self.save_commit_queue()

                if type == "unfollow" or type == "follow":
                    self.log(f"{username}: {type}ed")
                    print(f"{username}: {type}ed")
                else:
                    self.log(f"{username}: {type}d")
                    print(f"{username}: {type}d")

                return True
            else:
                return False
        else:
            if schedule_action:
                self.schedule_action(username,when,post,f"{type}")
            return False


    def action_schedule(self,username,type,action,now,post):

        if self.check_commit_availability(type):
            if type == "like" or type == "unlike":
                print(f"{type[:-1]}ing {username}")
            else:
                print(f"{type}ing {username}")

            if action():

                self.commit_queue = self.commit_queue.append({'user':username,'action':type,'datetime':now},ignore_index = True)
                self.save_commit_queue()

                if type == "unfollow" or type == "follow":
                    self.log(f"{username}: {type}ed")
                    print(f"{username}: {type}ed")
                else:
                    self.log(f"{username}: {type}d")
                    print(f"{username}: {type}d")

                return True
            else:
                return False
        else:
            return False


    def commit_schedule(self,row):
        now = datetime.datetime.now(pytz.timezone("America/Sao_Paulo"))
        print(f"Commiting:{row.action.lower()} de {row.user}")


        if row.action.lower() == "unfollow":
            user = User(row.user,self.driver)

            try:
                user.get_user_info()
            except:
                print("Não foi possível pegar informações do usuário")
                pre = self.driver.find_element_by_tag_name("pre").text
                if pre == "{}":
                    return True
                else:
                    # Se der isso o user não foi analisado e não tem as características necessárias pra dar continuidade oa schedule, entretanto ele vai tentar executar
                    print("Bug desconhecido no instabot/commit_schedule, linha 1067")

            if not user.followed_by_viewer and not user.requested_by_viewer and not user.has_blocked_viewer:
                print("Já foi unfollowed ou o usuário recusou o request")
                return True

            else:
                return self.action_schedule(username = row.user,
                                     type = "unfollow",
                                     action = user.unfollow,
                                     now = now,
                                     post = "",
                                     )

        elif row.action.lower() == "unlike":
            post = Post(row.posts,self.driver)
            return self.action_schedule(username = row.user,
                                 type = "unlike",
                                 action = post.unlike,
                                 now = now,
                                 post = row.posts,
                                 )

        elif row.action.lower() == "follow":
             user = User(row.user,self.driver)
             try:
                 user.get_user_info()
             except:
                 print("Não foi possível pegar informações do usuário")
                 pre = self.driver.find_element_by_tag_name("pre").text
                 if pre == "{}":
                     return True

             if user.requested_by_viewer or user.has_blocked_viewer or user.followed_by_viewer:
                 return True

             else:
                 return self.action_schedule(username = row.user,
                                             type = "follow",
                                             action = user.follow,
                                             now = now,
                                             post = "",
                                             )

        elif row.action.lower() == "like":
             post = Post(row.posts,self.driver)
             return self.action_schedule(username = row.user,
                                  type = "like",
                                  action = post.like,
                                  now = now,
                                  post = row.posts,
                                  )
        else:
            print("É aqui?")
            return False




    def perform_schedule(self):
        print("Commiting Schedule!!")
        now = datetime.datetime.now(pytz.timezone("America/Sao_Paulo"))
        try:
            schedule = self.load_schedule()
        except:
            print("No scheduled actions to commit")
            return True
        self.load_commit_queue()
        to_commit = schedule.loc[schedule.datetime < now,:]

        commited = False
        for index,row in to_commit.iterrows():
            commited = True
            self.status += 1
            now = datetime.datetime.now(pytz.timezone("America/Sao_Paulo"))

            if self.commit_schedule(row):
                schedule.drop(index,inplace = True)
                self.save_schedule(schedule)


                time.sleep(random.uniform(0.8,5.2))
            else:
                pass
        if commited:
            print("Schedule Finished!")


    def hash_password(self,secret_key,iv):
        secret_key = secret_key.encode()
        public_key = self.load_public_key().encode()

        decoded_text = decrypt(public_key,secret_key,iv).decode("utf-8")

        return decoded_text
