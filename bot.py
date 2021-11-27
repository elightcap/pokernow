import os
from typing import cast

from requests.models import CaseInsensitiveDict
import requests
import discord
import json
import math
import time
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getnev('DISCORD_GUILD')
unbKey = os.getenv('UNB_KEY')
pokerBotID = os.getenv('POKER_BOT_ID')
unbUrl = 'https://unbelieveaboat.com/ap1/v1/guilds/{}/users/'.format(GUILD)
pokerbotURL = unbUrl + pokerBotID
intents = discord.Intents.default()
intents.members = True
intents.messages=True
client = discord.Client(intents=intents)
headers = {'Authorization': unbKey}

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    msg = message.content.lower()
    if "!buyin" in msg:
        aID = message.author.id
        sAmount = message.replace("!buyin", "")
        amount = int(sAmount)

        if amount <= 1:
            await message.channel.send("You can't buy in less than 1")
            return
        
        url = unbUrl + aID
        r = requests.get(url, headers=headers)
        json_data = json.loads(r.text)
        strCash = json_data['cash']
        uMoney = float(strCash)
        cost = float(amount//2.00)
        if uMoney < cost:
            await message.channel.send("You don't have enough money to buy in")
            return
        else:
            print("buyin" + message.author.name + " for " + str(amount))
            mes = "!pac {0.author.mention} {1}".format(message, amount)
            send = await message.channel.send(mes)
            nCost = '-' + str(int(cost))
            builder = {'cash': nCost}
            jsonString = json.dumps(builder, indent=4)
            rp = requests.patch(url, headers=headers, data=jsonString)
    
    if "!cashout" in msg:
        aID = message.author.id
        sAmount = message.replace("!cashout", "")
        amount = int(sAmount)
        url = unbUrl + aID
        mes = "!prc {0.author.mention} {1}".format(message, amount)
        send = await message.channel.send(mes)

        @client.event
        async def on_raw_message_edit(edit):
            msgData = edit.data
            editID = str(msgData['author']['id'])
            if editID == pokerBotID:
                if "done! I removed" in str(edit):
                    print("cashout" + message.author.name + " for " + str(amount))
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