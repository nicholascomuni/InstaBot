import time
import re
import json
from insta_modules.util import *
from datetime import datetime
import pytz

def get_pic_info_function(pic,driver,analyse_comments):
    ctr = 0
    while True:
        ctr += 1
        try:
            url = f"https://instagram.com/p/{pic.url}/?__a=1"
            driver.get(url)
            time.sleep(0.1)
            pre = driver.find_element_by_tag_name("pre").text
            break
        except:
            if ctr > 5:
                return False
            print("ERROR: get_pic_info_function")
            time.sleep(1)


    data = json.loads(pre)['graphql']['shortcode_media']

    pic.id = data['id']
    pic.is_video = data['is_video']
    try:
        capt = data['accessibility_caption']
        caption = capt.split(":")[1]
        caption = re.split(',| and ',caption)

        pic.caption =  [capt.strip() for capt in caption]
    except:
        pic.caption = []
    pic.datetime = datetime.utcfromtimestamp(data['taken_at_timestamp']).astimezone(pytz.timezone("America/Sao_Paulo"))

    pic.location = data['location']

    pic.viewer_has_liked = data['viewer_has_liked']
    pic.viewer_in_photo_of_you = data['viewer_in_photo_of_you']
    pic.is_ad = data['is_ad']
    tagged_edges = data['edge_media_to_tagged_user']['edges']
    pic.tagged_users = []
    for edge in tagged_edges:
        pic.tagged_users.append(edge['node']['user']['username'])

    try:
        pic.description = data['edge_media_to_caption']['edges'][0]['node']['text']
    except:
        pic.description = ""
    pic.likes = data['edge_media_preview_like']['count']
    pic.owner = data['owner']['username']

    pic.comments = data['edge_media_preview_comment']['count']

    if analyse_comments:
        if pic.comments > 0:
            pic.comments_list = get_comments(driver,pic.url)

    return True



def get_comments(driver,shortcode):
    all_comments = []

    graphql_url = 'https://www.instagram.com/graphql/query/?query_hash=f0986789a5c5d17c2400faebf16efd0d'

    variables = {}
    variables['shortcode'] = shortcode
    variables['first'] = 50



    has_next_data = True
    url = f'{graphql_url}&variables={str(json.dumps(variables))}'

    while has_next_data:
        driver.get(url)
        time.sleep(1.5)

        pre = driver.find_element_by_tag_name("pre").text
        data = json.loads(pre)['data']['shortcode_media']

        page_info = data['edge_media_to_comment']['page_info']

        edges = data['edge_media_to_comment']['edges']
        for edge in edges:
            all_comments.append({'owner':edge['node']['owner']['username'],'text':edge['node']['text']})

        grabbed = len(all_comments)
        has_next_data = page_info['has_next_page']
        if has_next_data:
            variables['after'] = page_info['end_cursor']
            url = f'{graphql_url}&variables={str(json.dumps(variables))}'
        else:
            break

    return all_comments


def get_likers(self,amount):
    user_data = {}
    all_likers = []

    graphql_url = 'https://www.instagram.com/graphql/query/?query_hash=e0f59e4a1c8d78d0161873bc2ee7ec44'


    variables = {}
    variables['shortcode'] = self.url
    variables['include_reel'] = "true"
    variables['first'] = 50


    has_next_data = True
    url = f'{graphql_url}&variables={str(json.dumps(variables))}'

    while has_next_data:
        self.driver.get(url)
        time.sleep(0.5) # Antes estava 1

        pre = self.driver.find_element_by_tag_name("pre").text
        data = json.loads(pre)['data']['shortcode_media']
        page_info = data['edge_liked_by']['page_info']
        edges = data['edge_liked_by']['edges']
        for edge in edges:
            all_likers.append(edge['node']['username'])

        grabbed = len(set(all_likers))
        has_next_data = page_info['has_next_page']

        if not has_next_data or grabbed >= amount:
            break
        else:
            variables['after'] = page_info['end_cursor']
            url = f'{graphql_url}&variables={str(json.dumps(variables))}'


    if grabbed > amount:
        all_likers = all_likers[:amount]
        grabbed = len(all_likers)

    return all_likers


def like(driver):
    driver.execute_script("window.scrollTo(0,1000)")
    like_button = lambda: driver.find_element_by_xpath("//span[@aria-label='Like']")
    like_button().click()
