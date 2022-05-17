import time
import numpy as np

from insta_modules.util import checkEqual
from insta_modules.util import parse_data
from selenium.webdriver.common.action_chains import ActionChains

from insta_modules.post.post import Post
import json

class Hashtag:
    def __init__(self,tag,driver):

      self.driver = driver
      self.tag = tag
      self.posts = 0
      self.likes_mean_top_posts = 0
      self.likes_mean_most_recent = 0
      self.comments_mean_top_posts = 0
      self.comments_mean_most_recent = 0
      self.sentiment = []
      self.top_posts = []
      self.most_recent = []

    def get_posts(self):

        self.driver.get(f"https://www.instagram.com/explore/tags/{self.tag}/")
        time.sleep(2)

        posts_raw = self.driver.find_element_by_class_name('-nal3').get_attribute('textContent')
        posts_raw = posts_raw.split(' ')[0]
        posts = int(posts_raw.replace(",",""))
        self.posts = posts
        return posts

    def simple_analysis(self,depth = 200,amount_per_photo = 100):
        print(f"Starting simple hashtag anaylsis   Depth: {depth}")
        self.get_pics_urls(depth)

        for shortcode in self.most_recent:
            post = Post(shortcode,self.driver)
            post.medium_analysis(amount_per_photo)

    def get_likers(self,depth,amount):
        self.get_pics_urls(depth)

        for shortcode in self.most_recent:
            post = Post(shortcode,self.driver)
            post.medium_analysis(amount)


    def get_pics_urls(self,amount):

        user_data = {}
        all_shortcodes = {'media':[],'top_posts':[]}

        graphql_url = 'https://www.instagram.com/graphql/query/?query_hash=f92f56d47dc7a55b606908374b43a314'


        variables = {}
        variables['tag_name'] = self.tag
        variables['first'] = 50


        has_next_data = True
        url = f'{graphql_url}&variables={str(json.dumps(variables))}'
        t1 = time.time()

        while has_next_data:
            self.driver.get(url)
            time.sleep(0.1)

            pre = self.driver.find_element_by_tag_name("pre").text
            data = json.loads(pre)['data']['hashtag']
            page_info = data['edge_hashtag_to_media']['page_info']
            edges = data['edge_hashtag_to_media']['edges']

            # Top Posts
            if all_shortcodes['top_posts'] == []:
                edges_top_posts = data['edge_hashtag_to_top_posts']['edges']
                for edge in edges_top_posts:
                    all_shortcodes['top_posts'].append(edge['node']['shortcode'])
            # --------------------------------------------------------------


            for edge in edges:
                all_shortcodes['media'].append(edge['node']['shortcode'])

            grabbed = len(set(all_shortcodes['media'])) + len(set(all_shortcodes['top_posts']))
            has_next_data = page_info['has_next_page']

            if not has_next_data or grabbed >= amount:
                break
            else:
                variables['after'] = page_info['end_cursor']
                url = f'{graphql_url}&variables={str(json.dumps(variables))}'


        return all_shortcodes
