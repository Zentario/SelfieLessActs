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
import re, ast, collections, requests
import docker
import subprocess

API_CALLS = 0

def write_text_file(data):
    with open('/database/actBase.txt', 'w') as db:
        db.write(json.dumps(data))
    db.close()    

def read_text_file():
    with open('/database/actBase.txt', 'r') as db:
        data = db.read()
    db.close()
    
    return json.loads(data)

def convert_to_dict(list_keys):
    list_dict = {}
    
    for key in list_keys:
        value = count_acts_for_category(key)[0]
        value = ast.literal_eval(value)
        
        if(len(value) == 0):
            list_dict.update({key: 0})
        else:
            count = value[0]
            list_dict.update({key: count})    
    return list_dict



app = Flask(__name__)
client = docker.from_env()


#[TASK-1] HEALTH AND CRASH
# HEALTH CHECK [EVERY 1 SECOND]
@app.route('/api/v1/_health', methods=['GET'])
def health_check():
    if(request.method == 'GET'):
        return json.dumps({}), 200
    else:
        return json.dumps({}), 400


# CRASH SERVER INTENTIONALLY
CRASH_FLAG = False
@app.route('/api/v1/_crash', methods=['POST'])
def crash_server():
    global CRASH_FLAG
    if(CRASH_FLAG == False):
        if(request.method == 'POST'):
            # crash here [kill container]
            CRASH_FLAG = True
            # func = request.environ.get('werkzeug.server.shutdown')
            # func()
            return json.dumps({}), 200
        else:
            return 400
    else:
        return json.dumps({}), 500

# MODULE 3 LIST CATEGORIES
# MODULE 4 ADD CATEGORY
@app.route('/api/v1/categories', methods=['GET', 'POST'])
def list_categories():

    global API_CALLS
    API_CALLS += 1

    if(request.method == "GET"):
        data = dict(read_text_file())
        
        
        list_categories = data["categories"]
        
        if(not bool(list_categories)):
            return json.dumps({}), 204
        
        list_dict = convert_to_dict(list_categories)
        return json.dumps(list_dict), 200
    
    elif(request.method == "POST"):
        json_data = request.get_json()
        
        data = dict(read_text_file())
        category = json_data[0]
        
        if(category in data["categories"]):
            return json.dumps({}), 400
        
        data["categories"].append(category)
        write_text_file(data)
        return json.dumps({}), 201
        
    else:
        return json.dumps({}), 405


# MODULE 5 DELETE CATEGORY
@app.route('/api/v1/categories/<string:category>', methods=['DELETE'])
def delete_category(category):   
    
    global API_CALLS
    API_CALLS += 1

    if(request.method == "DELETE"):
        data = dict(read_text_file())
        
        for i in range(len(data["categories"])):
            if(data["categories"][i] == category):
                data["categories"].pop(i)
                
                # Delete all acts which belong to that category
                actId_list = []
                for actId in data['acts']:
                    if(data['acts'][actId]['categoryName'] == category):
                        actId_list.append(actId)
                for i in actId_list:
                    del data["acts"][i]
                    
                write_text_file(data)
                return json.dumps({}), 200
            
        return json.dumps({}), 400
    
    else:
        return json.dumps({}), 405


    
# MODULE 6 LIST ACTS FOR A CATEGORY WHEN ACTS<100
# MODULE 8 Return number of acts for a given category in a given range (inclusive)
@app.route('/api/v1/categories/<string:category>/acts', methods=["GET"])
def list_acts_for_category(category):
    
    global API_CALLS
    API_CALLS += 1

    if(request.method == "GET"):
        
        start = request.args.get('start')
        end = request.args.get('end')
        
        if(start == '' or end == ''):
            
            data = dict(read_text_file())
            if(category in data["categories"]):
                count = count_acts_for_category(category)[0]
                count = ast.literal_eval(count)

                act_count = 0 if(len(count)==0) else count[0]
                print("NUMBER OF ACTS : ", act_count)

                if(int(act_count) > 100):
                    return json.dumps([]), 413

                if(act_count == 0):
                    return json.dumps([]), 204

                acts_list = []

                for actId in data["acts"]:
                    act_dict = {}

                    if(data["acts"][actId]["categoryName"] == category):
                        act_dict.update({"actId" : int(actId)})
                        act_dict.update(data["acts"][actId])
                        del act_dict["categoryName"]
                        acts_list.append(act_dict)

                return json.dumps(acts_list), 200

            else:
                return json.dumps([]), 400
        
        else:
            # MODULE 8 HERE
            start = int(start)
            end = int(end)
            
            data = dict(read_text_file())
            if(category in data["categories"]):
                count = count_acts_for_category(category)[0]
                count = ast.literal_eval(count)

                act_count = 0 if(len(count)==0) else count[0]
                print("NUMBER OF ACTS : ", act_count)

                if(end - start + 1 > 100):
                    return json.dumps([]), 413

                if(act_count == 0):
                    return json.dumps([]), 204
                
                acts_list = []
                acts_dict = collections.OrderedDict(sorted(data['acts'].items(), reverse=True))
                
                for k,v in acts_dict.items():
                    act = {}
                    del acts_dict[k]["categoryName"]
                    
                    act.update({"actId": int(k)})
                    act.update({"username": v["username"]})
                    act.update({"timestamp": v["timestamp"]})
                    act.update({"caption": v["caption"]})
                    act.update({"upvotes": v["upvotes"]})
                    act.update({"imgB64": v["imgB64"]})
                    
                    acts_list.append(act)
                    
                
                return json.dumps(acts_list[start:end+1]), 200
                
            
            else:
                return json.dumps({}), 400
            
            
    else:
        return json.dumps([]), 405

        
    
# MODULE 7 LIST NUMBER OF ACTS FOR A CATEGORY
@app.route('/api/v1/categories/<string:category>/acts/size', methods=['GET'])
def count_acts_for_category(category):
    
    global API_CALLS
    API_CALLS += 1

    act_count = 0
    
    if(request.method == "GET"):
        
        data = dict(read_text_file())
        
        if(category in data["categories"]):
            
            for actId in data["acts"]:
                if(data["acts"][actId]["categoryName"] == category):
                    act_count += 1
                    
          
            if(act_count == 0):
                return json.dumps([]), 204
            
            return json.dumps([act_count]), 200
    else:
        return json.dumps([]), 405

    
    
# MODULE 9 UPVOTE AN ACT
@app.route('/api/v1/acts/upvote', methods=["POST"])
def upvote_act():

    global API_CALLS
    API_CALLS += 1

    if(request.method == "POST"):
        json_data = request.get_json()
        
        actId = str(json_data[0])
        
        data = read_text_file()
        if(actId not in data["acts"].keys()):
            return json.dumps({}), 400
        
        for act in data["acts"]:
            if(actId == act):
                prev_votes = int(data["acts"][actId]["upvotes"])
                curr_votes = str(prev_votes + 1)
                data["acts"][actId]["upvotes"] = curr_votes
                write_text_file(data)
                return json.dumps({"UPVOTED ACT " + actId : "TOTAL VOTES : " + curr_votes}), 200
        
    else:
        return json.dumps({}), 405     
    


# MODULE 10 REMOVE AN ACT
@app.route('/api/v1/acts/<string:actId>', methods=['DELETE'])
def remove_act(actId): 
    
    global API_CALLS
    API_CALLS += 1

    if(request.method == "DELETE"):
        
        data = dict(read_text_file())
        
        if(actId in data["acts"].keys()):
            del data["acts"][actId]
            write_text_file(data)
            return json.dumps({}), 200
            
        else:
            return json.dumps({}), 400
        
    
    else:
        return json.dumps({}), 405
    


# MODULE 11 UPLOAD AN ACT
@app.route('/api/v1/acts', methods=['POST'])
def upload_act(): 
    
    global API_CALLS
    API_CALLS += 1

    if(request.method == "POST"):
        json_data = request.get_json()
        
        act = {}
        data = dict(read_text_file())
        
        actId = str(json_data["actId"])
        username = json_data["username"]
        timestamp = json_data["timestamp"]
        caption = json_data["caption"]
        categoryName = json_data["categoryName"]
        img = json_data["imgB64"]
        upvotes = "0"
        
        flagTime = False
        flagName = False
        flagCategory = False
        
        for i in data["acts"].keys():
            if(i == actId):
                return json.dumps({}), 400
        
        for i in data["categories"]:
            if(i == categoryName):
                flagCategory = True
                break
        
        users_list = json.loads(requests.get('3.210.111.0/api/v1/users'))

        for i in users_list:
            if(i == username):
                flagName = True
                break
        
        # DD-MM-YYYY:SS-MM-HH
        regex  = '\d{2}-\d{2}-\d{4}:\d{2}-\d{2}-\d{2}'
        flagTime =  re.match(regex, timestamp)
        
        if(flagTime and flagName and flagCategory):
            act.update({"username" : username})
            act.update({"timestamp" : timestamp})
            act.update({"caption" : caption})
            act.update({"categoryName" : categoryName})
            act.update({"imgB64" : img})
            act.update({"upvotes" : upvotes})
            
            data["acts"].update({actId : act})
            write_text_file(data)
            return json.dumps({}), 201
            
        else:
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


@app.route("/api/v1/acts/count", methods=["GET"])
def count_all_acts():
    if(request.method == 'GET'):
        data = dict(read_text_file())
        act_count = len(data['acts'])

        if(act_count == 0):
            return json.dumps([]), 204
        return json.dumps([act_count]), 200

    else:
        return json.dumps([]), 405


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
