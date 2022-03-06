# first merge the two source files to pair ticket # with macro references
# post a comment on a ticket
# given the ticket number and a reference to which macro to use
# some kind of output file to record any potential edge cases/failures
from base64 import b64encode
import pandas as pd
import configparser
import requests
import logging
import json
import sys

config = configparser.RawConfigParser()
config.read('./src/auth.ini')
DOMAIN = config['zendesk']['Domain'].strip('"')
AUTH = config['zendesk']['Credentials'].strip('"')

def main(logger,args): 
    print(args)
    if len(args) != 3:
        print("USAGE: python bulk_reply.py sup.csv eng.csv")
        exit()
    sup_file = args[1]
    eng_file = args[2]
    merge_file = generate_worksheet(sup_file, eng_file)
    for i,request in enumerate(merge_file):
        result = post_comment(DOMAIN, AUTH, ticket_num=request[2], macro=request[1])
        merge_file[i].append(result.status_code) # append the result of the api request
    print(merge_file)
    return 0

def generate_worksheet(sup_csv, eng_csv):
    doc1 = pd.read_csv(eng_csv, header=None) # we want columns 1(email) and 3(output)
    doc2 = pd.read_csv(sup_csv, header=None) # 0(tId) and 1(email)
    doc_lst = [ [row[1],row[3]] for i,row in doc1.iterrows() ] # making doc1 a list with the values we want
    for i,result in enumerate(doc_lst):
        #print((doc2.loc[doc2[1] == result[0]][0]).values)
        # I need to find a row by value of a column, then pull a specific column value from that row
        doc_lst[i].append((doc2.loc[doc2[1] == result[0]][0]).values[0]) # append the ticketid in the df row matching the email column of result
    print(doc_lst)
    return doc_lst

def get_ticket_assignee(dom, auth, ticket_num):
    url = 'https://{}.zendesk.com/api/v2/tickets/{}.json'.format(dom, ticket_num)
    print("URL, ", url)
    header = {"Authorization": "Basic {}".format(str(b64encode(auth.encode('utf-8')))[2:-1])}
    print("HEADER, ", header)
    
    try:
        result = requests.get(url, headers=header)
        assignee_id = json.loads(result.text)['ticket']['assignee_id']
        return assignee_id
    except Exception as e:
        print('Error posting comment', str(e))
        exit()

def post_comment(dom, auth, ticket_num, macro):
    url = 'https://{}.zendesk.com/api/v2/tickets/{}.json'.format(dom, ticket_num)
    print("URL, ", url)
    header = {"Authorization": "Basic {}".format(str(b64encode(auth.encode('utf-8')))[2:-1]), 'Content-type': 'application/json'}
    print("HEADER, ", header)
    dat = get_macro_data(macro, get_ticket_assignee(dom, auth, ticket_num))
    print("DATA, ", dat)
    try:
        result = requests.put(url, data=json.dumps(dat), headers=header)
        print(result, "\n","=="*15)
        return result
    except Exception as e:
        print('Error posting comment', str(e))
        exit()

def get_macro_data(macro, assignee_id):
    scenario = None
    # match macro:
    if macro == "EMAILS_MATCHED":
        scenario = ("Hello,\n"
        "\tWe recently noticed unusual activity associated with your account."  
        "Out of an abundance of caution and for your protection, we have temporarily "
        "locked your account and logged you out of all devices. To regain access to your account, "
        "all you will need to do is reset your password.\n\n" 
        "Please take the following steps to change your account password:\n\n"
        "  * Go to www.funimation.com/log-in\n"
        "  * Select Forgot Password\n"
        "  * Enter the email address associated with your Funimation account\n"
        "  * Select Send\n"
        "Within 15 minutes, you will receive an email with instructions for resetting your password. "
        "Follow the instructions to resume Funimation services.\n\n"
        "If you have any additional questions or concerns please reach out to us at help@funimation.com.")
    elif macro ==  "NEW_ACCOUNT_EXISTS_WITH_PREVIOUS_EMAIL":
        scenario = ("Hello,\n"
        "\tThank you for your patience, and we apologize for any inconvenience you may have experienced."  
        " Upon further review from our Development Team, it appears that you have created a new account with the email address you are writing in from."
        " Due to this, no further action is needed at this time.\n\n"
        "If you ever have issues accessing your account, we recommend trying to reset your password by following these steps:\n" 
        "  * Go to www.funimation.com/log-in\n"
        "  * Select Forgot Password\n"
        "  * Enter the email address associated with your Funimation account\n"
        "  * Select Send\n"
        "If you have any further questions, please reach out to us at help@funimation.com.")
    elif macro ==  "COMPROMISED_ACCOUNT_NOT_FOUND": 
        scenario = (f"Hello,\n\t{macro}\n\nBest,")
    elif macro == "NOT_COMPROMISED_BECAUSE_EMAILS_MATCHED":
        scenario = (f"Hello,\n\t{macro}\n\nBest,")
    else:
        print("Invalid macro type,", macro)
        exit()

    # TODO: what to do with the author_id? Can we grab it from the ticket audit api?
    formatted = {"ticket": {"comment": { "body": "{}".format(scenario), "author_id": assignee_id }}}
    return formatted

if __name__ =="__main__":
    # TODO: set logging level based on input
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    args = sys.argv
    main(logger,args)
