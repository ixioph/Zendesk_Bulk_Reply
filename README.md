# Zendesk_Bulk_Reply
The Zendesk Spike Bulk Reply tool...

## Requirements
To run this tool, the following libraries first need to be installed: 
  * requests
  * pandas


## Usage
To run the tool, simply navigate to ./scripts/ and run the following command: 
  * `python bulk_reply.py file1.csv file2.csv`

In this context, file1.csv refers to a file containing columns (_&_) whereas file2.csv refers to a file containing columns (&). The script pairs the data between the two files to construct a list of tickets and a bulk reply

Usage relies on the file `/src/auth.ini` to run. An example is included with the repo, but here it is as well: 
```
[zendesk]
Domain = "yourZendeskDomain"
Credentials = "YOURZENDESKEMAIL@yourbiz.com/token:YOURZENDESKAPIKEY"
Skipper_Tag = "yourSKIPPERtag"
```

#### Functions 
The `get_macro_data()` function...
```Python
def get_macro_data(macro, assignee_id):
    scenario = None
    # match macro:
    if macro == "EMAILS_MATCHED":
        scenario = ("Text 0")
    elif macro ==  "NEW_ACCOUNT_EXISTS_WITH_PREVIOUS_EMAIL":
        scenario = ("Text 1")
    elif macro == "COMPROMISED_ACCOUNT_NOT_FOUND" or macro == "NOT_COMPROMISED_BECAUSE_EMAILS_MATCHED": 
        scenario = ("Text 2")
    else:
        print("Invalid macro type,", macro)
        exit()

    # TODO: what to do with the author_id? Can we grab it from the ticket audit api?
    formatted = {"ticket": {"comment": { "body": "{}".format(scenario), "author_id": assignee_id }, "additional_tags": TAG}}
    return formatted
```

The `post_comment()` function...
```Python
def post_comment(dom, auth, ticket_num, macro):
    skipper_tag, assignee_id = get_ticket_data(dom, auth, ticket_num)
    if skipper_tag:
        return - 1
    url = 'https://{}.zendesk.com/api/v2/tickets/update_many.json?ids={}'.format(dom, ticket_num)
    print("URL, ", url)
    header = {"Authorization": "Basic {}".format(str(b64encode(auth.encode('utf-8')))[2:-1]), 'Content-type': 'application/json'}
    print("HEADER, ", header)
    dat = get_macro_data(macro, assignee_id)
    print("DATA, ", dat)
    try:
        result = requests.put(url, data=json.dumps(dat), headers=header)
        print(result, "\n","=="*15)
        return result
    except Exception as e:
        print('Error posting comment', str(e))
        exit()
```

The `get_ticket_data()` function...
```Python
def get_ticket_data(dom, auth, ticket_num):
    url = 'https://{}.zendesk.com/api/v2/tickets/{}.json'.format(dom, ticket_num)
    print("URL, ", url)
    header = {"Authorization": "Basic {}".format(str(b64encode(auth.encode('utf-8')))[2:-1])}
    print("HEADER, ", header)
    
    try:
        result = requests.get(url, headers=header)
        ticket_data = json.loads(result.text)
        tags = ticket_data['ticket']['tags']
        skipper_tag = TAG in tags
        assignee_id = ticket_data['ticket']['assignee_id']
        return skipper_tag, assignee_id
    except Exception as e:
        print('Error posting comment', str(e))
        exit()
```

The `generate_worksheet()` function takes...
```Python
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
```
