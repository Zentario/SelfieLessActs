import docker
import requests
import threading
from flask import Flask, request
import json
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

client = docker.from_env()

ports=[8000,8001,8002]
active_ports=[] # starter 8000
requests_count=0

#ip_addr = '18.213.239.186:'
ip_addr = '3.209.38.245:'


def round_robin():
	global active_ports 
	res=active_ports.pop(0)
	active_ports.append(res)
	return str(res)


@app.route('/')
def func():
    print("Test path")
    return json.dumps({}), 200


@app.route('/api/v1/aws_health', methods=['GET'])
def aws_health():
    return json.dumps({}), 200


# TASK-2 REDIRECTION AND RR ALGO
@app.route('/api/v1/<path:path>', methods=["GET","POST","DELETE"])
def request_routing(path):

    global requests_count
    requests_count = requests_count + 1
    container = round_robin()

    url_called = 'http://'+ ip_addr + container + '/api/v1/' + path
    print('CURRENT CONTAINER PORT :', container)
    print('CURRENT PATH ', url_called)

    if(request.method == 'GET'):
        r = requests.get(url=url_called)
    elif(request.method == 'POST'):
        data = request.get_json()
        r = requests.post(url=url_called, data=data)
    else:
        r = requests.delete(url=url_called)
    
    if(r.status_code == 200):
        return json.dumps({r.json()}), 200
    elif(r.status_code == 400):
        return json.dumps({r.reason}), 400
    else:
        return json.dumps({}), r.status_code



# TASK-3 FAULT TOLERANCE
def fault_tolerance():

    timer1 = threading.Timer(1.0, fault_tolerance)
    timer1.start()

    global active_ports
    for port in active_ports:
        url_called = "http://" + ip_addr + str(port) +"/api/v1/_health"
        r = requests.get(url=url_called)
        if(r.status_code == 500):
            for container in client.containers.list():
                if(client.inspect_container(container.id)['NetworkSettings']['Ports'] == port):
                    container.stop()
                    print("OLD CONTAINER STARTED ON PORT", port)
                    os.popen("sudo docker run -d -v /home/ubuntu/database:/database -p " + str(port) + ":80 acts")
                    print("NEW CONTAINER STARTED ON PORT", port)



# TASK-4 AUTO-SCALING
def auto_scaling():
    global active_ports
    global requests_count
    timer2 = threading.Timer(120.0, auto_scaling)
    timer2.start()

    
    if(requests_count < 20):
        needed = 1
        
    elif(requests_count >= 20 and requests_count < 40):
        needed = 2

    elif(requests_count >= 40 and requests_count < 60):
        needed = 3

    # SCALE-UP
    if(needed > len(active_ports)):
        n = needed - len(active_ports)
        for i in range(0, n):
            for j in ports:
                if(j not in active_ports):
                    os.popen("sudo docker run -d -v /home/ubuntu/database:/database -p " + str(j) + ":80 acts")
                    print("NEW CONTAINER SCALE UP ON PORT : ", j)
                    active_ports.append(j)
                    break

    # SCALE-DOWN
    elif(needed < len(active_ports)):
        n = len(active_ports) - needed
        active_ports.sort(reverse=True)
        for i in range(0, n):
            for container in client.containers.list():
                if(client.inspect_container(container.id)['NetworkSettings']['Ports'] == active_ports[i]):
                    container.stop()
        active_ports.pop(i)

    requests_count = 0



auto_scaling()
fault_tolerance()

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=80)