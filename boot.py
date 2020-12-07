from flask import Flask, request, jsonify, send_from_directory, make_response
import requests
from cfenv import AppEnv
import os
import base64
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app1 = Flask(__name__)
env = AppEnv()

if "UAA_SRV" in os.environ:
	UAA_SERVICE = env.get_service(name=os.environ["UAA_SRV"])
else:
	print("Please set User Env variable UAA_SRV.")
	exit(0)
	
if "DESTINATION_SRV" in os.environ:	
	DESTINATION_SERVICE = env.get_service(name=os.environ["DESTINATION_SRV"])
else:
	print("Please set User Env variable DESTINATION_SRV.")
	exit(0)

if "CONNECTIVITY_SRV" in os.environ:
	CONNECTIVITY_SERVICE = env.get_service(name=os.environ["CONNECTIVITY_SRV"])
else:
	print("Please set User Env variable CONNECTIVITY_SRV.")
	exit(0)

if "DESTINATIONS" in os.environ:
	DESTINATIONS = os.environ["DESTINATIONS"]
else:
	print("Please set User Env variable DESTINATIONS (Comma seperated).")
	exit(0)

DESTINATIONS = DESTINATIONS.split(",")

def currentDestination(p_path):
	return p_path.split("/")[0]

def isValidDestination(p_path):
	if currentDestination(p_path) in DESTINATIONS:
		return True
	return False

def getEndPoint(p_path):
	return p_path.replace(currentDestination(p_path), "", 1)

HTTP_METHODS = ['GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH']
CONNECTIVITY_PROXY = CONNECTIVITY_SERVICE.credentials["onpremise_proxy_host"] +":"+ CONNECTIVITY_SERVICE.credentials["onpremise_proxy_port"]
CONNECTIVITY_SECRET = CONNECTIVITY_SERVICE.credentials["clientid"] + ':' + CONNECTIVITY_SERVICE.credentials["clientsecret"]
DESTINATION_SECRET = DESTINATION_SERVICE.credentials["clientid"] + ':' + DESTINATION_SERVICE.credentials["clientsecret"]
CONNECTIVITY_CREDENTIALS = base64.b64encode(CONNECTIVITY_SECRET.encode()).decode('ascii')
DESTINATION_CREDENTIALS = base64.b64encode(DESTINATION_SECRET.encode()).decode('ascii')

def getAccessToken(credentials, serviceName):
	#Getting access token for Connectivity service.
	headers = {'Authorization': 'Basic ' + credentials, 'content-type': 'application/x-www-form-urlencoded'}

	form = [('client_id', serviceName.credentials["clientid"]), ('grant_type', 'client_credentials')]

	r = requests.post( UAA_SERVICE.credentials["url"] + '/oauth/token', data=form, headers=headers)

	token = r.json()['access_token']
	return token


# Helper that Returns the URL of the destination.
def _getDestinationURL(token,p_path):
	headers = {'Authorization': 'Bearer ' + token}

	r = requests.get(DESTINATION_SERVICE.credentials["uri"] + '/destination-configuration/v1/destinations/' + currentDestination(p_path), headers=headers)

	destination = r.json()
	return destination["destinationConfiguration"]["URL"]


def getURL(p_path):
	# Fetch URL of the Destination
	destination_token = getAccessToken( DESTINATION_CREDENTIALS, DESTINATION_SERVICE)
	url = _getDestinationURL(destination_token,p_path)
	return url


def getProxy():
	data = {}
	connectivity_token = getAccessToken(CONNECTIVITY_CREDENTIALS, CONNECTIVITY_SERVICE)

	# Setting proxies and header for the Destination that needs to be called.
	headers = {'Proxy-Authorization': 'Bearer ' + connectivity_token}
	# connection['headers'] = str(headers)
	# proxy
	proxies = { "http": CONNECTIVITY_PROXY }
	# connection['proxies'] = str(proxies)
	data['headers'] = headers
	data['proxies'] = proxies
	return data

def makeRequest(request,endpoint,p_path):
	# Get destination URL
	url = getURL(p_path)
	#Get proxy parameters
	connection = getProxy()
	headers = {}
	newURL = url+endpoint
	
	for h in request.headers:
		if(h[0] != "Content-Length" and h[0] != "Host"):
			headers[h[0]] = h[1] #request.headers.get(h)
	
	headers["Proxy-Authorization"] = connection['headers']["Proxy-Authorization"]
	print("URL : "+newURL)
	print("======================")
	print("Headers : "+str(headers))
	print("======================")
	print("Payload : "+str(request.get_data()))
	print("======================")
	print("Arguments : "+str(request.args))
	print("======================")
	
	r = requests.request(method= request.method, url = newURL, proxies=connection['proxies'], params=request.args, data=request.get_data(), headers=headers, verify=False, timeout=1000)
	r.encoding = 'utf-8'
	print("======================")
	print("ResponseText : "+str(r.text))
	print("======================")
	print("ResponseText.headers : "+str(r.headers))
	print("======================")
	return r

@app1.route('/<path:path>', methods=HTTP_METHODS)
def root(path):
	print("PATH => "+str(path))
	if (isValidDestination(path)):
		endpoint = getEndPoint(path)		
		responseText = makeRequest(request,endpoint,path)
		headers = {}
		for k in responseText.headers:
			if(k != "Content-Encoding" and k!= 'content-encoding'):
				headers[k] = responseText.headers[k]
		return make_response(str(responseText.text), responseText.status_code, headers)
	else:
		response = send_from_directory('webapp', path, cache_timeout=0)
		response.headers['Access-Control-Allow-Origin'] = '*'
		return response
	
@app1.route('/', methods=['GET'])
def index():
	return send_from_directory('webapp', "index.html", cache_timeout=0)	

if __name__ == '__main__':
	app1.run(host='0.0.0.0', port=8080, debug= True)
