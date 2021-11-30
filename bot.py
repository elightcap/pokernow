##################################################################################
# Unbelievable Poker Bot                                                         #
# License: GPLv3 (see LICENSE.txt)                                               # 
# Description: A bot that allows money from the Unbelievaboat economy to be used #
#              as chips with the PokerNow system. See Readme.md for more info.   #
##################################################################################


import os
from typing import cast

from requests.models import CaseInsensitiveDict
from discord.utils import get
from discord.ext import tasks, commands

import requests
import discord
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

#set static variables, mostly loaded from .env file
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
unbKey = os.getenv('UNB_KEY')
pokerBotID = os.getenv('POKER_BOT_ID')
unbUrl = 'https://unbelievaboat.com/api/v1/guilds/{}/users/'.format(GUILD)
pokerbotURL = unbUrl + pokerBotID
intents = discord.Intents.default()
intents.members = True
intents.messages=True
client = discord.Client(intents=intents)
headers = {'Authorization': unbKey}


#set up the pokerbot to be called on new messages
@client.event
async def on_message(message):
    botChannel = client.get_channel(int(os.getenv('BOT_CHANNEL')))
    #don't respond to yourself, bot
    if message.author == client.user:
        return
    #string to hold the response
    msg = message.content.lower()
    #if the message is a pokerbot command
    if "!buyin" in msg:
        #grab the user's id
        aID = str(message.author.id)
        #strip the command from the message
        sAmount = msg.replace("!buyin", "")
        #convert the amount to an int
        amount = int(sAmount)

        #if the amount is less than or equal to 1, return
        if amount <= 1:
            await message.channel.send("You can't buy in less than 1")
            return
        
        #set up the request to the Unbelievaboat API
        url = unbUrl + aID
        r = requests.get(url, headers=headers)
        json_data = json.loads(r.text)
        strCash = json_data['cash']
        #convert the cash to an float and set the value of chips
        uMoney = float(strCash)
        cost = float(amount//2.00)
        #if the user doesnt have enough money to buy in return
        if uMoney < cost:
            print("User {} does not have enough money to buy in".format(message.author.name))
            await message.channel.send("You don't have enough money to buy in")
            return
        else:
            #if the user has enough money, send buyin message and subtract the cost from their balance
            print("buyin " + message.author.name + " for " + str(amount))
            mes = "!pac {0.author.mention} {1}".format(message, amount)
            send = await botChannel.send(mes)
            nCost = '-' + str(int(cost))
            builder = {'cash': nCost}
            jsonString = json.dumps(builder, indent=4)
            rp = requests.patch(url, headers=headers, data=jsonString)
    
    if "!cashout" in msg:
        #same as above but for cashout
        aID = str(message.author.id)
        sAmount = msg.replace("!cashout", "")
        amount = int(sAmount)
        url = unbUrl + aID
        #send message
        mes = "!prc {0.author.mention} {1}".format(message, amount)
        send = await botChannel.send(mes)

        #heres the fun part.  since pokernow bot edits its response to the user, we need to grab the response and wait for the actual 
        #response to come back.  this is a bit of a hack, but it works.  the response is then parsed to confirm the user has enough chips
        #to cash out.  if they do, the chips are added to their balance and the user is notified.  if they don't, the user is notified
        @client.event
        async def on_raw_message_edit(edit):
            msgData = edit.data
            editID = str(msgData['author']['id'])
            if editID == pokerBotID:
                if "done! I removed" in str(edit):
                    print("cashout " + message.author.name + " for " + str(amount))
                    payout = str((amount//2)*.9)
                    rake = str((amount//2)*.1)
                    payBuilder = {'cash': payout}
                    rakeBuilder = {'bank': rake}
                    payJson = json.dumps(payBuilder, indent=4)
                    rakeJson = json.dumps(rakeBuilder, indent=4)
                    requestPay = requests.patch(url, headers=headers, data=payJson)
                    requestRake = requests.patch(pokerbotURL, headers=headers, data=rakeJson)
                elif "this user only has" in str(edit):
                    print(message.author.name + " tried to cashout but they only have " + str(amount))
                    await message.channel.send("You can't cashout more than you have")

client.run(TOKEN)