# first merge the two source files to pair ticket # with macro references
# post a comment on a ticket
# given the ticket number and a reference to which macro to use
# some kind of output file to record any potential edge cases/failures
from base64 import b64encode
import pandas as pd
import configparser
import requests
import argparse
import logging
import json

config = configparser.RawConfigParser()
config.read('./src/auth.ini')
DOMAIN = config['zendesk']['Domain'].strip('"')
AUTH = config['zendesk']['Credentials'].strip('"')

def main(logger,args): 
    print(args)
    sup_file = "./sup.csv" # args[0]
    eng_file = "./eng.csv" # args[1]
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

def post_comment(dom, auth, ticket_num, macro):
    url = 'https://{}.zendesk.com/api/v2/tickets/{}.json'.format(dom, ticket_num)
    print("URL, ", url)
    header = {"Authorization": "Basic {}".format(str(b64encode(auth.encode('utf-8')))[2:-1]), 'Content-type': 'application/json'}
    print("HEADER, ", header)
    dat = get_macro_data(macro)
    print("DATA, ", dat)
    try:
        result = requests.put(url, data=json.dumps(dat), headers=header)
        print(result, "\n","=="*15)
        return result
    except Exception as e:
        print('Error posting comment', str(e))
        exit()

def get_macro_data(macro):
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
        scenario = (f"Hello,\n\t{macro}\n\nBest,")
    elif macro ==  "COMPROMISED_ACCOUNT_NOT_FOUND": 
        scenario = (f"Hello,\n\t{macro}\n\nBest,")
    elif macro == "NOT_COMPROMISED_BECAUSE_EMAILS_MATCHED":
        scenario = (f"Hello,\n\t{macro}\n\nBest,")
    else:
        print("Invalid macro type,", macro)
        exit()

    # TODO: what to do with the author_id? Can we grab it from the ticket audit api?
    formatted = {"ticket": {"comment": { "body": "{}".format(scenario), "author_id": 7519464586 }}}
    return formatted

if __name__ =="__main__":
    # TODO: set logging level based on input
    logger = logging.getLogger()
    parser = argparse.ArgumentParser()
    logger.setLevel(logging.INFO)
    args = parser.parse_args()
    main(logger,args)
