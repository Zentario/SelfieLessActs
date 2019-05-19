"""
Runing Flask server
FLASK_APP=newApp.py flask run
or
python newApp.py

FLASK HTTP STATUS CODES
200 - OK
201 - CREATED
204 - NO_CONTENT
400 - BAD_REQUEST
404 - NOT_FOUND
405 - METHOD_NOT_ALLOWED
"""

from flask import Flask, request, json
import re


API_CALLS = 0

def write_text_file(data):
    with open('userBase.txt', 'w') as db:
        db.write(json.dumps(data))
    db.close()    

def read_text_file():
    with open('userBase.txt', 'r') as db:
        data = db.read()
    db.close()
    
    return json.loads(data)

def is_sha1(password):
    regex = '\w{40}'
    if(len(password) == 40 and re.match(regex, password)):
        return True
    else:
        return False



app = Flask(__name__)


# MODULE 1 ADD USER
# NEW-MODULE LIST ALL USERS
@app.route("/api/v1/users", methods=['POST', 'GET'])
def adduser():
    global API_CALLS
    API_CALLS += 1

    if(request.method == 'POST'):
        
        json_data = request.get_json()
        
        name = json_data['username']
        pwd = json_data['password']
        
        if(not is_sha1(pwd)):
            return json.dumps({}), 400
        
        if(name == "" or pwd == ""):
            return json.dumps({}), 400
        
        data = dict(read_text_file())
        
        if name in data['users'].keys():
            return json.dumps({}), 400
        
        temp = {name : pwd}
        data['users'].update(temp)
    
        write_text_file(data)
        
        return json.dumps({}), 201
    

    elif(request.method == 'GET'):

        data = dict(read_text_file())

        users = [username for username in data['users'].keys()]

        if(len(users) == 0):
            return json.dumps([]), 204

        return json.dumps(users), 200

    
    else:
        return json.dumps({}), 405


# MODULE 2 REMOVE USER    
@app.route('/api/v1/users/<string:username>', methods=['DELETE'])
def delete_user(username):
    global API_CALLS
    API_CALLS += 1

    if(request.method == "DELETE"):
        data = dict(read_text_file())
        for name in data["users"].keys():
            if(username == name):
                data["users"].pop(username)
                
                # Deleting users acts
                act_count_list = []
                
                for actId in data["acts"]:
                    if(data['acts'][actId]["username"] == username):
                        act_count_list.append(actId)
                
                for actId in act_count_list:
                    del data['acts'][actId]
                
                write_text_file(data)
                
                return json.dumps({}), 200
            
        return json.dumps({}), 400
    
    else:
        return json.dumps({}), 405


# NEW MODULE
# RETURN NUMBER OF API CALLS EXCLUDING THIS
@app.route("/api/v1/_count", methods=["GET", "DELETE"])
def count_api_calls():
    global API_CALLS
    if(request.method == 'GET'):
        return json.dumps([API_CALLS]), 200
    elif(request.method == 'DELETE'):
        API_CALLS = 0
        return json.dumps({}), 200
    else:
        return json.dumps({}), 405


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)