import requests
import json
import configparser
import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon import functions, types
from telethon.tl.functions.messages import (GetHistoryRequest)
from telethon.tl.types import (
PeerChannel
)



#Creating the client
async def createClient():
    config = configparser.ConfigParser()
    config.read('../config.ini')

    # Setting configuration values
    api_id = config['Telegram']['api_id']
    api_hash = config['Telegram']['api_hash']

    api_hash = str(api_hash)

    phone = config['Telegram']['phone']
    username = config['Telegram']['username']

    client = TelegramClient(username, api_id, api_hash)
    await client.connect()
    # Ensure you're authorized
    if not await client.is_user_authorized():
        await client.send_code_request(phone)
        try:
            await client.sign_in(phone, input('Enter the code: '))
        except SessionPasswordNeededError:
            await client.sign_in(password=input('Password: '))

    print("Client Created")
    return client


loop = asyncio.get_event_loop()
client = loop.run_until_complete(createClient())


        
async def getPayload(channel,count,sess_password=None):
    '''
    config_file: Location of the Telegram Config File
    channel: Channel ID/Number/Link
    Count: Message Limit
    Phone_no: Your number to authenticate the Client
    sess_password = (If Required) For authentication
    '''
    #Getting Group Name

    global client
    try:
        group_name = (await client.get_entity(channel)).title
    except:
        group_name = (await client.get_entity(channel)).first_name
    
    
    #Making the Payload list
    messages_informat = list()
    
    m_list = await client.get_messages(channel,count)
    for x in m_list[::-1]:
        if x.message is not None and len(x.message)!=0:
            #Getting the User Information
            user = await (x.get_sender())
            try:
                messages_informat.append(

                {
                    "duration": {"startTime": str(x.date), "endTime": str(x.date)},
                    # <Optional, object| Duration object containing startTime and/or endTime for the transcript.>, e.g.
                    "payload": {
                        "content": x.message,
                        "contentType": "text/plain"
                    },
                    "from": {"name": str(user.first_name) + " " +str(user.last_name), "userId": str(user.id)}
                    # <Optional, object| Information about the User information i.e. name and/or userId, produced the content of this message.>
                }

                )
            except AttributeError:
                messages_informat.append(

                {
                    "duration": {"startTime": str(x.date), "endTime": str(x.date)},
                    # <Optional, object| Duration object containing startTime and/or endTime for the transcript.>, e.g.
                    "payload": {
                        "content": x.message,
                        "contentType": "text/plain"
                    },
                    "from": {"name": user.title, "userId": str(user.id)}
                    # <Optional, object| Information about the User information i.e. name and/or userId, produced the content of this message.>
                }

                )
            
    #Creating the final payload
    payload = {
    "name": group_name,  # <Optional,String| your_meeting_name by default conversationId>

    "confidenceThreshold": 0.5,
    # <Optional,double| Minimum required confidence for the insight to be recognized. Value ranges between 0.0 to 1.0. Default value is 0.5.>

    "detectPhrases": True,
    # <Optional,boolean| It shows Actionable Phrases in each sentence of conversation. These sentences can be found using the Conversation's Messages API. Default value is false.>

    "messages": messages_informat}

    print(payload,end="\n\n")
    return payload



def getSummary(payload):
    url = "https://api.symbl.ai/oauth2/token:generate"

    appId = "6b454a506830584a3246534a6d6d6b6e4974417a636e3441506b4841624b5270" 
    appSecret = "70694e33646a544e43694c444c5f7135663768726a5045305636313562797a557176426c377952346f57477464566c6a67783758695776464733795071494e72"

    auth_payload = {
        "type": "application",
        "appId": appId,
        "appSecret": appSecret
    }
    headers = {
        'Content-Type': 'application/json'
    }

    responses = {
        400: 'Bad Request! Please refer docs for correct input fields.',
        401: 'Unauthorized. Please generate a new access token.',
        404: 'The conversation and/or it\'s metadata you asked could not be found, please check the input provided',
        429: 'Maximum number of concurrent jobs reached. Please wait for some requests to complete.',
        500: 'Something went wrong! Please contact support@symbl.ai'
    }

    response = requests.request("POST", url, headers=headers, data=json.dumps(auth_payload))
    access_token = response.json()['accessToken']
    
    
    #Getting the conversation ID

    url = "https://api.symbl.ai/v1/process/text"

    # set your access token here. See https://docs.symbl.ai/docs/authentication

    headers = {
        'Authorization': 'Bearer ' + access_token,
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=json.dumps(payload))
    response_json = None
    if response.status_code >= 200 and response.status_code < 400:
        # Successful API execution
        response_json = response.json()

    elif response.status_code in responses.keys():
        print(responses[response.status_code])  # Expected error occurred
    else:
        print("Unexpected error occurred. Please contact support@symbl.ai" + ", Debug Message => " + str(response.text))

    conversationId = response_json['conversationId']
    
    #For getting the member's list and the group title
    baseUrl_mem = "https://api.symbl.ai/v1/conversations/{conversationId}"
    url = baseUrl_mem.format(conversationId=conversationId)


    response = requests.request("GET", url, headers=headers)
    #print("topics => " + str(response.json()))

    title = response.json()['name']

    string_members = "Members:\n"

    for x in response.json()["members"]:
        string_members = string_members + x["name"] + '\n'
    
    
    #For Topics:
    baseUrl_topics = "https://api.symbl.ai/v1/conversations/{conversationId}/topics"
    url = baseUrl_topics.format(conversationId=conversationId)

    params = {
        'sentiment': True,  # <Optional, boolean| Give you sentiment analysis on each topic in conversation.>
        'parentRefs': True,  # <Optional, boolean| Gives you topic hierarchy.>
    }
    response = requests.request("GET", url, headers=headers, params=json.dumps(params))
    #print("topics => " + str(response.json()['topics']))

    string_topics = "Topics:\n"

    for x in response.json()['topics']:
        string_topics = string_topics + x['text'] + '\n'

    #For Action Items
    baseUrl_act = "https://api.symbl.ai/v1/conversations/{conversationId}/action-items"
    url = baseUrl_act.format(conversationId=conversationId)

    headers = {
        'Authorization': 'Bearer ' + access_token,
        'Content-Type': 'application/json'
    }


    response = requests.request("GET", url, headers=headers)
    #print("topics => " + str(response.json()))

    string_actions = "Actions:\n"

    for x in response.json()['actionItems']:
        string_actions = string_actions + x['text'] + '\n'


    return title + "\n\n" + string_members + "\n\n" + string_topics + "\n\n" + string_actions




def callAllFunctions(channel,count,sess_password=None):
    global client
    payload = loop.run_until_complete(getPayload(channel,count,sess_password=None))
    return getSummary(payload)