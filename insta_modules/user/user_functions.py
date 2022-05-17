import time
import json
import numpy as np
from insta_modules.util import *
from selenium.webdriver.common.action_chains import ActionChains



def get_user_info_function(user):
    username = user.username
    user_data = {}
    url = f'https://instagram.com/{username}/?__a=1'
    t1 = time.time()

    user.driver.get(url)
    time.sleep(0.1)

    pre = user.driver.find_element_by_tag_name("pre").text
    data = json.loads(pre)['graphql']['user']

    user.id                  =  data['id']
    user.bio                 =  data['biography']
    user.full_name           =  data['full_name']
    user.is_private          =  data['is_private']
    user.following           =  data['edge_follow']['count']
    user.followers           =  data['edge_followed_by']['count']
    user.posts               =  data['edge_owner_to_timeline_media']['count']
    user.external_url        =  data['external_url']
    user.followed_by_viewer  =  data['followed_by_viewer']
    user.follows_viewer      =  data['follows_viewer']
    user.has_blocked_viewer  =  data['has_blocked_viewer']
    user.is_business_account =  data['is_business_account']
    user.profile_pic_url     =  data['profile_pic_url']
    user.requested_by_viewer =  data['requested_by_viewer']

    user.first_name          =  user.full_name.split(" ")[0]
    user.surname             =  " ".join(user.full_name.split(" ")[1:])
    user.gender              =  get_gender(user.first_name,user.driver)


def get_followers_list(self):
    user_data = {}
    all_followers = []

    graphql_url = 'https://www.instagram.com/graphql/query/?query_hash=56066f031e6239f35a904ac20c9f37d9'


    variables = {}
    variables['id'] = self.id
    variables['first'] = 50


    has_next_data = True
    url = f'{graphql_url}&variables={str(json.dumps(variables))}'

    while has_next_data:
        self.driver.get(url)

        time.sleep(0.02)

        pre = self.driver.find_element_by_tag_name("pre").text
        data = json.loads(pre)['data']['user']
        page_info = data['edge_followed_by']['page_info']
        edges = data['edge_followed_by']['edges']



        for edge in edges:
            all_followers.append(edge['node']['username'])

        grabbed = len(set(all_followers))
        has_next_data = page_info['has_next_page']
        if has_next_data:
            variables['after'] = page_info['end_cursor']
            url = f'{graphql_url}&variables={str(json.dumps(variables))}'
        else:
            return all_followers

    return all_followers

def get_following_list(self):
    user_data = {}
    all_following = []

    graphql_url = 'https://www.instagram.com/graphql/query/?query_hash=c56ee0ae1f89cdbd1c89e2bc6b8f3d18'


    variables = {}
    variables['id'] = self.id
    variables['first'] = 50


    has_next_data = True
    url = f'{graphql_url}&variables={str(json.dumps(variables))}'

    while has_next_data:
        self.driver.get(url)

        time.sleep(0.2)

        pre = self.driver.find_element_by_tag_name("pre").text
        data = json.loads(pre)['data']['user']
        page_info = data['edge_follow']['page_info']
        edges = data['edge_follow']['edges']


        for edge in edges:
            all_following.append(edge['node']['username'])

        grabbed = len(set(all_following))
        has_next_data = page_info['has_next_page']
        if has_next_data:
            variables['after'] = page_info['end_cursor']
            url = f'{graphql_url}&variables={str(json.dumps(variables))}'
        else:
            return all_following

    return all_following



def get_gender(first_name,driver):

    try:
        with open("insta_modules/male_names.txt",'r') as file:
            male_names_list = file.read().split(',')
        with open("insta_modules/female_names.txt",'r') as file:
            female_names_list = file.read().split(',')
    except:
        with open("insta_modules/male_names.txt",'r',encoding = "ISO-8859-1") as file:
            male_names_list = file.read().split(',')
        with open("insta_modules/female_names.txt",'r',encoding = "ISO-8859-1") as file:
            female_names_list = file.read().split(',')

    if len(male_names_list) > 1 and len(female_names_list):
        if first_name.lower() in male_names_list and first_name.lower() not in female_names_list:
            return "male"
        elif first_name.lower() in female_names_list and first_name.lower() not in male_names_list:
            return "female"
        else:
            return "unknown"
    else:
        print("Names DB not initialized! use self.init_names_db() first")


def get_pics_urls(user,amount):
    user_data = {}
    all_shortcodes = []

    graphql_url = 'https://www.instagram.com/graphql/query/?query_hash=f2405b236d85e8296cf30347c9f08c2a'


    variables = {}
    variables['id'] = user.id
    variables['first'] = 50


    has_next_data = True
    url = f'{graphql_url}&variables={str(json.dumps(variables))}'
    t1 = time.time()

    while has_next_data:
        user.driver.get(url)
        time.sleep(0.)

        pre = user.driver.find_element_by_tag_name("pre").text
        data = json.loads(pre)['data']['user']
        page_info = data['edge_owner_to_timeline_media']['page_info']
        edges = data['edge_owner_to_timeline_media']['edges']

        for edge in edges:
            all_shortcodes.append(edge['node']['shortcode'])

        grabbed = len(set(all_shortcodes))
        has_next_data = page_info['has_next_page']

        if not has_next_data or grabbed >= amount:
            break
        else:
            variables['after'] = page_info['end_cursor']
            url = f'{graphql_url}&variables={str(json.dumps(variables))}'


    if grabbed > amount:
        all_shortcodes = all_shortcodes[:amount]
        grabbed = len(all_shortcodes)
    return all_shortcodes
