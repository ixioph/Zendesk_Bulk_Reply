# first merge the two source files to pair ticket # with macro references
# post a comment on a ticket
# given the ticket number and a reference to which macro to use
# some kind of output file to record any potential edge cases/failures
from base64 import b64encode
import configparser
import requests
import logging

config = configparser.RawConfigParser()
config.read('../src/auth.ini')
DOMAIN = config['zendesk']['Domain'].strip('"')
AUTH = config['zendesk']['Credentials'].strip('"')

def main(logger): 
    test_ticket_num = 99999999# TODO: create test ticket, but number here
    result = post_comment(DOMAIN, AUTH, test_ticket_num, macro="A")
    print(result)
    return 0

def post_comment(dom, auth, ticket_num, macro):
    url = 'https://{}.zendesk.com/api/v2/tickets/{}.json'.format(dom, ticket_num)
    header = {"Authorization": "Basic {}".format(str(b64encode(auth.encode('utf-8')))[2:-1])}
    dat = get_macro_data(macro)
    try:
        result = requests.get(url, data=dat, headers=header)
        return result
    except Exception as e:
        print('Error posting comment', str(e))
        exit()

def get_macro_data(macro):
    scenario = None
    match macro:
        case "A":
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
        case "B":
            pass
        case "C": 
            pass
        case _:
            print("Invalid macro type")
            exit()

    # TODO: what to do with the author_id? Can we grab it from the ticket audit api?
    formatted = {"ticket": {"comment": { "body": "{}".format(scenario), "author_id": 99999999 }}}
    return scenario

if __name__ =="__main__":
    # TODO: set logging level based on input
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    main(logger)
