

def checkEqual(iterator):
    iterator = iter(iterator)
    try:
        first = next(iterator)
    except StopIteration:
        return True
    return all(first == rest for rest in iterator)

def parse_data(string):
    return int(string.replace("k","000").replace("m","000000").replace(',',""))

def parse_string(string):
    if '.' in string:
        return string.replace('m','00000').replace('k','00').replace(',',"").replace('.','')
    else:
        return string.replace('m','000000').replace('k','000').replace(',',"")

def find_element_decorator(func):
    def inner(if_except_raised,*args,**kwargs):
        try:
            return func(*args,**kwargs)
        except:
            return if_except_raised
    return inner

def find_element(driver,xpath):
    try:
        driver.find_element_by_xpath(xpath)
        return True
    except:
        return False

def flat_array(array):
    return [i for element in array for i in element]

def shutdown():
    import os
    os.system('shutdown -s')

def load_lead_profile(filename):
    lead_args_list = ['gender',
    'min_followers',
    'max_followers',
    'min_following',
    'max_following',
    'min_ff_ratio',
    'max_ff_ratio',
    'min_posts',
    'max_posts',
    'min_comments_mean',
    'private']

    with open(filename,'r') as file:
        raw_text = file.read()
        args = [arg.strip() for arg in raw_text.split('\n') if arg.strip().split(' ')[0] in lead_args_list]
        parsed_args = {arg.split('=')[0].strip():arg.split('=')[1].strip() for arg in args}
        return parsed_args

def logging_str(tamanho,repetidos):
    s = []
    for i in range(tamanho):
        s.append(" .")

    for i in range(repetidos):
        s[i] = ' !'
    return "".join(s)

def count_equal(array):
    res = 0
    for i in range(1,len(array)+1):
        short = array[-i:]
        if checkEqual(short):
            res+=1
    return res

def transform_stack_log(array):
    return logging_str(len(array),count_equal(array))


from selenium.common.exceptions import TimeoutException
import time

def timeout_decorator(func):
   def func_wrapper(self,*args, **kwargs):
       counter = 0
       while True:
           counter += 1
           if counter > 3:
               raise
           try:
               return func(self,*args, **kwargs)
           except TimeoutException:
               print("Trying to refresh...")
               time.sleep(1.5)
               self.driver.refresh()
               time.sleep(1.5)
               continue
   return func_wrapper


def ceiling(x,maximum):
    if x > maximum:
        return maximum
    else:
        return x

def minimum(x,minim=0.2):
	if x < minim:
		return minim
	else:
		return x


class InstagramResponse_Exception(Exception):
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)

class FailedToLogin_Exception(Exception):
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)
