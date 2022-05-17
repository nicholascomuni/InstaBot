import configparser
import threading

def req_input(msg,dtype = str):
    while True:
        resp = input(msg)
        try:
            if resp != "" :
                return dtype(resp)
        except:
            print("Formato invalido")

def opt_input(msg,default,dtype = str):
    while True:
        resp = input(msg)
        if resp == "":
            print(default)
            return default
        else:
            try:
                return dtype(resp)
            except:
                print("Formato invalido")

def assert_file(path):
    try:
        with open(path) as file:
            return True
    except FileNotFoundError:
        return False
