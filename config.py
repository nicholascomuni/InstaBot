import configparser,os,sys
from utils.util import *
import shutil
import threading
import ast
import boto3
import pickle
import datetime
import pytz
import time
from utils.crypto import *

def start_bot(username=None,mode="full"):
    username = input("Digite o usuário:") if username == None else username
    config = handle_configfile(username)
    if config:
        return run_bot('bot1',config,mode)

def run_bot(botname,config,mode):
    sys.path.append(os.getcwd()+"/bots")
    global bot
    bot = __import__(botname).Bot(config,mode)
    bot.run()

    """
    global bot_thread
    bot_thread = threading.Thread(target = bot.run,daemon=True) <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    bot_thread.start()"""



def handle_command(command):

    commands_list = {'new'              :   create_config,
                     'start'            :   start_bot,
                     'quit'             :   exit,
                     'commands_list'    :   commandsList,
                     'edit'             :   edit,
                     'del'              :   delete,
                     'get'              :   get_current_option,
                     'stop'             :   stop,
                     'make_backup'      :   s3_backup,
                     'get_commit'       :   get_commit,
                     'recover_data'     :   recover_user_data,
                     'upload_config'    :   upload_config,
                     'download_config'  :   download_config,
                     'get_user_config'  :   get_user_config,
    }


    try:
        return commands_list[command]
    except:
        print("Comando não encontrado - para conferir a lista de comandos: commands_list")
        return print

def runInterface():
    print("----------------- Instabot Running -----------------")
    global bot
    while True:
        try:
            if not bot.allow_interface:
                while True:
                    time.sleep(0.5)
                    if bot.allow_interface:
                        break
        except NameError:
            pass
        command_input = input("botTerminal> ").strip()

        if command_input == "":
            command = "start"
            args = ["nicholascomuni","custom5"]
        else:
            command = command_input.split(' ')[0]
            args = command_input.split(' ')[1:]

        if args:
            handle_command(command)(*args)

        else:
            handle_command(command)()

def commandsList():
    print('\n\ncreate: cria novo usuário\nstart: starta o robo\nquit: desligar\ncommands_list: Lista de comandos\nmake_backup: Faz backup dos arquivos do usuário\nstop: Para o bot\nedit: edita configuração de usuário\nget: retorna atual valor de opções da configuração\nget_commit: retorna ultimas ações\nrecover_data: faz download dos dados do usuário\nupload_config: Faz backup do config.ini\ndownload_config: Faz download do config.ini\n')

def delete(username = None,del_dir=False):
    username = input("Digite o usuário:") if username == None else username
    config = configparser.ConfigParser()
    try:
        config.read('config/config.ini')
    except FileNotFoundError:
        print("Configfile não encontrado!")
        return False
    if username in config.sections():
        config.remove_section(username)
        resp = input(f"Tem certeza que deseja deletar as configurações de {username}? (y/n)")
        if resp.lower() == 'y':
            with open('config/config.ini','w') as file:
                config.write(file)
            shutil.rmtree(f'client_data/{username}')
            print(f"As configurações de {username} foram deletadas com sucesso!")
        else:
            return
    else:
        if os.path.isdir(f'client_data/{username}') and del_dir == '-rmd':
            shutil.rmtree(f'client_data/{username}')
            print(f"Os arquivos de {username} foram deletados com sucesso!")
            return True
        else:
            print("Usuário não encontrado!")
            return False

def edit(username = None,key = None, new_value = None): ## <<<<<< PROX
    username = input("Digite o usuário:").strip() if username == None else username.strip()
    save = False
    config = configparser.ConfigParser()

    try:
        config.read('config/config.ini')
    except FileNotFoundError:
        print("Configfile não encontrado!")
        return False

    if username not in config.sections():
        print("Usuário não encontrado!")
        return False

    while True:
        if key == None and new_value == None:
            option = input("Digite a opção e o novo valor : ")
            try:
                if ',' in option:
                    key,new_value = option.split(',')
                    key = key.strip()
                    new_value = new_value.strip()

                elif ' ' in option:
                    key,new_value = option.split(' ')
                    key = key.strip()
                    new_value = new_value.strip()
                else:
                    print("Valores invalidos")
                    continue
            except:
                print("Valores invalidos")
                continue

        else:
            key = input("Digite a opção: ").strip() if key == None else key.strip()
            new_value = input("Digite o novo valor: ").strip() if new_value == None else new_value.strip()

        if key in config[username].keys() and key != None and new_value != None:
            config[username][key] = new_value
            save = True

        else:
            resp = input("opção não encontrada, tentar novamente (y/n)? ")
            if resp.lower() == 'y':
                option = input("Digite a opção e o novo valor : ")
                try:
                    if ',' in option:
                        key,new_value = option.split(',')
                        key = key.strip()
                        new_value = new_value.strip()

                    elif ' ' in option:
                        key,new_value = option.split(' ')
                        key = key.strip()
                        new_value = new_value.strip()
                    else:
                        print("Valores invalidos")
                        continue
                except:
                    print("Valores invalidos")
                    continue

            else:
                return
        if save:
            with open('config/config.ini','w') as file:
                config.write(file)
                print("Alterações salvas com sucesso!")
            return True


def handle_configfile(username):

    config = configparser.ConfigParser()
    while True:
        try:
            config.read('config/config.ini')
        except:
            print("ERRO: Configfile não encontrado!")
            break

        try:
            return config[username]
        except KeyError:
            resp = req_input("Usuário não encontrado, deseja criar nova configuração? (y/n)")
            if resp.lower() == 'y':
                return create_config()
            elif resp.lower() == 'n':
                return False
            else:
                pass





def get_current_option(username = None, option = None,path = "config/config.ini"):
    username = input("Digite o usuário:") if username == None else username

    config = configparser.ConfigParser()
    config.read(path)
    if username in config.sections():
        while True:
            option = input("Digite a opção:") if option == None else option
            try:
                print(f"{option}: {config[username][option]}")
                resp = input("Consultar outra opção (y/n)? ")
                if resp.lower() == 'y':
                    option = input("Digite a opção:")
                    continue
                else:
                    return True
            except:
                resp2 = input(f"{option} não encontrado, deseja tentar novamente (y/n)? ")
                if resp2.lower() =='y':
                    option = input("Digite a opção:")
                    continue
                else:
                    return False
    else:
        print("Usuário existente!")


def create_config():

    config = configparser.ConfigParser()
    config.read("config/config.ini")
    try:
        default = config['DEFAULT']
    except:
        print("\nDEFAULT CONFIG NÂO ENCONTRADO !!!\n\n\n\n\n\n")
        raise

    ## ----------------------- GENERAL ------------------------
    username = req_input("Usuário:  ")
    #password = req_input("Senha:    ")
    password = opt_input("Senha:    ", "", str)

    if password == "":
        public_key = req_input("Public Key:    ")

    ## ----------------------- BOT SETTINGS ------------------------
    likes_per_hour   = opt_input("Max likes por hora:    ",     default['likes_per_hour'],              int)
    likes_per_day    = opt_input("Max likes por dia:     ",     default['likes_per_day'],               int)
    likes_per_week   = opt_input("Max likes por semana:  ",     default['likes_per_week'],              int)

    likes_per_hour_target = opt_input("Max likes por hora - TARGET:    ",60,int)
    likes_per_day_target =  opt_input("Max likes por dia - TARGET:     ",240,int)
    likes_per_week =        opt_input("Max likes por semana - TARGET:  ",1400,int)

    follows_per_hour = opt_input("Max follows por hora:  ",     default['follows_per_hour'],            int)
    follows_per_day  = opt_input("Max follows por dia:   ",     default['follows_per_day'],             int)
    follows_per_week = opt_input("Max follows por semana:",     default['follows_per_week'],            int)

    follows_per_hour_target = opt_input("Max follows por hora - TARGET:    ",90,int)
    follows_per_day_target =  opt_input("Max follows por dia - TARGET:     ",240,int)
    follows_per_week =        opt_input("Max follows por semana - TARGET:  ",1400,int)

    unfollows_per_hour = opt_input("Max unfollows por hora: ",  default['unfollows_per_hour'],          int)
    unfollows_per_day  = opt_input("Max unfollows por dia:  ",  default['unfollows_per_day'],           int)
    unlikes_per_hour = opt_input("Max unlikes por hora: ",  default['unlikes_per_hour'],          int)
    unlikes_per_day  = opt_input("Max unlikes por dia:  ",  default['unlikes_per_day'],           int)

    hashtags_blacklist = opt_input("Blacklist de hashtags: ",  default['hashtags_blacklist'])
    if hashtags_blacklist != default['hashtags_blacklist']:
        hashtags_blacklist = hashtags_blacklist.split(',')



    user_blacklist = opt_input("Blacklist de usuários:  ",          default['user_blacklist'],          list)
    user_whitelist = opt_input("Whitelist de usuários:  ",          default['user_whitelist'],          list)

    bot_type = opt_input("Tipo de robo: ",default['bot_type'])
    hashtags_list = opt_input("Lista de hashtags:   ",default['hashtags_list'])
    schedule_step = opt_input("Step do unfollow:    ",default['schedule_step'])
    schedule_step = schedule_step.split(' ')
    schedule_step = {schedule_step[1]:int(schedule_step[0])}

    ## ----------------------- LEAD PROFILE ------------------------
    gender = opt_input("Sexo:   ",default['gender'])

    min_followers = opt_input("Min followers:   ",default['min_followers'],         int)
    max_followers = opt_input("Max followers:   ",default['max_followers'],         int)

    min_following = opt_input("Min following:   ",default['min_following'],         int)
    max_following = opt_input("Max following:   ",default['max_following'],         int)

    min_posts = opt_input("Min posts:   ",default['min_posts'],                     int)
    max_posts = opt_input("Max posts:   ",default['max_posts'],                     int)

    last_post_date = opt_input("Tempo desde o ultimo post",default['last_post_date'])

    min_ff_ratio = opt_input("Min ff ratio: ",default['min_ff_ratio'],              float)
    max_ff_ratio = opt_input("Max ff ratio: ",default['max_ff_ratio'],              float)

    privacy = opt_input("Usuário privado ou não:    ",default['privacy'],           bool)


    config[username] =   {
                          'username' : username,
                          'password' : password,
                          'public_key': public_key,
                          "proxy"    : "",
                          "use_proxy": False,

                          'likes_per_hour' : likes_per_hour,
                          'likes_per_day'  : likes_per_day,
                          'likes_per_week' : likes_per_week,

                          'likes_per_hour_target' : likes_per_hour_target,
                          'likes_per_day_target'  : likes_per_day_target,

                          'follows_per_hour': follows_per_hour,
                          'follows_per_day' : follows_per_day,
                          'follows_per_week': follows_per_week,

                          'follows_per_hour_target': follows_per_hour_target,
                          'follows_per_day_target' : follows_per_day_target,

                          "target_step": 90,
                          'days_to_unfollow': 10,

                          'unfollows_per_hour': unfollows_per_hour,
                          'unfollows_per_day' : unfollows_per_day,
                          'unlikes_per_hour' : unlikes_per_hour,
                          'unlikes_per_day'  : unlikes_per_day,

                          'unfollows_per_hour_target': unfollows_per_hour,
                          'unfollows_per_day_target' : unfollows_per_day,
                          'unlikes_per_hour_target' : unlikes_per_hour,
                          'unlikes_per_day_target'  : unlikes_per_day,

                          'hashtags_blacklist' : hashtags_blacklist,

                          'user_blacklist' : user_blacklist,
                          'user_whitelist' : user_whitelist,

                          'bot_type' : bot_type,
                          'hashtags_list' : hashtags_list,
                          'schedule_step' : schedule_step,

                          'gender'        :  gender,
                          'min_followers' :  min_followers,
                          'max_followers' :  max_followers,
                          'min_following' :  min_following,
                          'max_following' :  max_following,
                          'min_posts'     :  min_posts,
                          'max_posts'     :  max_posts,
                          'last_post_date':  last_post_date,
                          'min_ff_ratio'  :  min_ff_ratio,
                          'max_ff_ratio'  :  max_ff_ratio,
                          'privacy'       :  privacy,
                          'commit_hook'   :  False,
    }


    if not os.path.isdir(f'client_data/{username}'):
        os.mkdir(f'client_data/{username}/')
        os.mkdir(f'client_data/{username}/session')
        os.mkdir(f'client_data/{username}/data')
        os.mkdir(f'client_data/{username}/log')
        try:
            with open(f'config/config.ini','w') as file:
                config.write(file)
                print(f"{username} Criado com sucesso!")
                return config[username]

        except:
            print("ALGO DEU ERRADO !")
            return False
    else:
        print("Arquivos de usuários ainda existem, delete os arquivos antes! -use del ou del usuario -rmd")
        return False


def stop():
    print("Stopping Robot...")
    global bot
    global bot_thread
    bot.stop_robot = True
    bot_thread.join()
    print("Robot Stopped!")


def s3_backup(username=None):
    username = input("Digite o usuário:").strip() if username == None else username.strip()

    config = configparser.ConfigParser()
    config.read("config/config.ini")
    if username not in config.sections():
        print("Usuário existente!")
        return False

    print(f"Making backup of {username} data... dont shutdown the bot until finished!")
    log_task(username,f"Making backup of {username} data\n")
    id,sk = load_credentials()
    s3 = S3Login(id,sk)

    folder = f"client_data/{username}/data"

    uploadDirectory(s3,folder,"instabucket1",folder)
    print("Backup finished!")
    log_task(username,f"{username} backup finished!\n")
    return True

def load_credentials():
    with open("config/accessKeys.csv","r") as file:
        raw = file.read()
    dct = ast.literal_eval(raw)
    return dct["Access key ID"],dct["Secret access key"]

def S3Login(Key_id,Secret_key):
    s3 = boto3.client(
    's3',
    aws_access_key_id=Key_id,
    aws_secret_access_key=Secret_key)
    try:
        s3.list_buckets()
        return s3
    except:
        return False


def uploadDirectory(client,path,bucketname,s3path):
    if client:
        for root,dirs,files in os.walk(path):
            for file in files:
                client.upload_file(os.path.join(root,file),bucketname,f"{s3path}/{file}")
    else:
        print("Amazon s3 not logged in")

def download_config(gcinstance=None,configpath="config/"):
    gcinstance = input("Digite o nome da instância do google compute engine:").strip() if gcinstance == None else gcinstance.strip()
    print(f"Downloading {gcinstance} cofig.ini... dont shutdown the bot until finished!")
    log_task_root(f"Downloading {gcinstance} config.ini")
    id,sk = load_credentials()
    s3 = S3Login(id,sk)

    s3configpath = f"gcinstances/{gcinstance}/config/config.ini"
    s3config_logs_path = f"gcinstances/{gcinstance}/config/logs.txt"

    if configpath[-1] != "/":
        configpath = configpath+"/"

    config_logs_path = configpath + "logs.txt"
    configpath = configpath + "config.ini"
    gotit = False

    for obj in s3.list_objects(Bucket='instabucket1')['Contents']:
        key = obj["Key"]
        if key == s3config_logs_path:
            s3.download_file('instabucket1', key, config_logs_path)

    for obj in s3.list_objects(Bucket='instabucket1')['Contents']:
        key = obj["Key"]

        if key == s3configpath:
            gotit = True
            s3.download_file('instabucket1', key, configpath)

            print(f"Download {gcinstance} config.ini succeeded!")
            log_task_root(f"Download {gcinstance} config.ini succeeded!")
            return True




    if not gotit:
        print(f"Failed to download {gcinstance} config.ini! - Instance not found")
        log_task_root(f"Failed to download {gcinstance} config.ini - Instance not found")
        return False


def upload_config(gcinstance=None):
    gcinstance = input("Digite o nome da instância do google compute engine:").strip() if gcinstance == None else gcinstance.strip()
    print(f"Uploading {gcinstance} config.ini... dont shutdown the bot until finished!")
    log_task_root(f"Uploading {gcinstance} config.ini")
    id,sk = load_credentials()
    s3 = S3Login(id,sk)

    s3filepath = f"gcinstances/{gcinstance}/config/config.ini"
    folder = "config/config.ini"

    s3.upload_file(folder,"instabucket1",s3filepath)
    upload_backup_logs(s3,gcinstance)

    print("config.ini upload finished!")
    log_task_root(f"{gcinstance} config.ini upload succeeded!")
    return True


def upload_backup_logs(s3,gcinstance):
    s3filepath = f"gcinstances/{gcinstance}/config/logs.txt"
    folder = "config/logs.txt"
    s3.upload_file(folder,"instabucket1",s3filepath)

def recover_user_data(username=None):
    username = input("Digite o usuário:").strip() if username == None else username.strip()

    config = configparser.ConfigParser()
    config.read("config/config.ini")
    if username not in config.sections():
        print("Usuário existente!")
        return False

    print(f"Downloading {username} data... dont shutdown the bot until finished!")
    log_task(username,f"Recovering {username} data\n")
    id,sk = load_credentials()
    s3 = S3Login(id,sk)

    folder = f"client_data/{username}/data/"
    gotit = False
    for obj in s3.list_objects(Bucket='instabucket1')['Contents']:
        key = obj["Key"]
        if folder in key:
            gotit = True
            s3.download_file('instabucket1', key, folder+key.split("/")[-1])
    if gotit:
        print("Recover Succeeded!")
        log_task(username,f"{username} data recover succeeded!\n")
        return True
    else:
        print("Failed to get {username} data!")
        log_task(username,f"{username} data recover failed!\n")
        return False


def get_commit(username=None):
    username = input("Digite o usuário:").strip() if username == None else username.strip()

    config = configparser.ConfigParser()
    config.read("config/config.ini")
    if username not in config.sections():
        print("Usuário existente!")
        return False

    try:
        with open(f'client_data/{username}/data/commit_queue.pk','rb') as file:
            dtf = pickle.load(file)
    except:
        print("commit_queue not created yet!")
        return False

    now = datetime.datetime.now(pytz.timezone("America/Sao_Paulo"))

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


    print(f"\nlikes_hour: {len(likes_hour)}\nlikes_day: {len(likes_day)}\nfollows_hour: {len(follows_hour)}\nfollows_day: {len(follows_day)}\nunlikes_hour: {len(unlikes_hour)}\nunfollows_hour: {len(unfollows_hour)}")
    return True

def get_user_config(username):
    username = input("Digite o usuário:").strip() if username == None else username.strip()

    config = configparser.ConfigParser()
    config.read("config/config.ini")
    if username not in config.sections():
        print("Usuário existente!")
        return False

    with open(f"config/config.ini",'r') as file:
        start = False
        for line in file.readlines():
            if username in line:
                start = True

            if line == "\n":
                start = False

            if start:
                print(line,end="",flush=True)


def log_task(username,text):
    with open(f"client_data/{username}/data/task_logs.txt",'a+') as file:
        file.write(f"{datetime.datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%Y-%m-%d %H:%M:%S')} - {text}\n")

def log_task_root(text):
    with open(f"config/logs.txt",'a+') as file:
        file.write(f"{datetime.datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%Y-%m-%d %H:%M:%S')} - {text}\n")
