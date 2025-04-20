from django.shortcuts import render
from django.template import RequestContext
from django.contrib import messages
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
import os
from datetime import date
import json
from web3 import Web3, HTTPProvider
import hashlib

global username, usersList, notaryList, contract, web3


#function to call contract
def getContract():
    global contract, web3
    blockchain_address = 'http://127.0.0.1:9545'
    web3 = Web3(HTTPProvider(blockchain_address))
    web3.eth.defaultAccount = web3.eth.accounts[0]
    compiled_contract_path = 'Notary.json' 
    deployed_contract_address = '0x9043FaCab6ff7739c8e7AaE982623405cCC5cae1' 
    with open(compiled_contract_path) as file:
        contract_json = json.load(file)  
        contract_abi = contract_json['abi']  
    file.close()
    contract = web3.eth.contract(address=deployed_contract_address, abi=contract_abi)
getContract()


def getUsersList():
    global usersList, contract
    usersList = []
    count = contract.functions.getUserCount().call()
    for i in range(0, count):
        user = contract.functions.getUsername(i).call()
        password = contract.functions.getPassword(i).call()
        phone = contract.functions.getPhone(i).call()
        email = contract.functions.getEmail(i).call()
        address = contract.functions.getAddress(i).call()
        usersList.append([user, password, phone, email, address])

def getNotary():
    global notaryList, contract
    notaryList = []
    count = contract.functions.getNotaryCount().call()
    for i in range(0, count):
        uname = contract.functions.getOwner(i).call()
        fname = contract.functions.getFilename(i).call()
        hashcode = contract.functions.getHashcode(i).call()
        dd = contract.functions.getDate(i).call()
        signature = contract.functions.getSignature(i).call()
        key = contract.functions.getKey(i).call()
        notaryList.append([uname, fname, hashcode, signature, dd, key])        

getUsersList()
getNotary()

def VerifyNotaryAction(request):
    if request.method == 'POST':
        global username, notaryList
        today = date.today()
        pin = request.POST.get('t1', False)
        filedata = request.FILES['t2'].read()
        filename = request.FILES['t2'].name

        hashcode = hashlib.sha256(filedata).hexdigest()
        key = hashlib.sha256(pin.encode()).hexdigest()
        status = "Verification Failed"
        for i in range(len(notaryList)):
            nl = notaryList[i]
            if nl[2] == hashcode and nl[5] == key:
                status = nl
                break
        if status != "Verification Failed":
            output = '''
            <style>
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                    border-radius: 10px; 
                    overflow: hidden; 
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); 
                }
                th, td {
                    padding: 12px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                    font-family: Arial, sans-serif;
                }
                td{
                color:black;
                }
                th {
                    background-color: #1aa7ec;
                    color: white;
                }
                tr:nth-child(even) {
                    background-color: #f2f2f2;
                }
                tr:hover {
                    background-color: white;
                }
                .notary-text {
                    font-style: italic;
                    color: black;
                    margin-top: 10px;
                }
                .container {
                    width: 80%;
                    margin: 0 auto;
                }
            </style>
            <div class="container">
                <h6>Notary Verification Details</h6>
                <table>
                    <tr>
                        <th>Owner Name</th>
                        <th>eID File Name</th>
                        <th>Hashcode</th>
                        <th>Signature</th>
                        <th>Date</th>
                        <th>Key</th>
                    </tr>
            '''
            arr = status[3].split("$")
            output += f'''
                    <tr>
                        <td>{status[0]}</td>
                        <td>{status[1]}</td>
                        <td>{status[2][0:20]}</td>
                        <td>{arr[0]}</td>
                        <td>{status[4]}</td>
                        <td>{status[5][0:20]}</td>
                    </tr>
                    <tr>
                        <td colspan="6" class="notary-text">Notary Text: {arr[1]}</td>
                    </tr>
                </table>
            </div>
            '''
            status = output
            
        context = {'d': status}
        return render(request, 'VerifierScreen.html', context)

def VerifyNotary(request):
    if request.method == 'GET':
       return render(request, 'VerifyNotary.html', {})

def AddNotary(request):
    if request.method == 'GET':
       return render(request, 'AddNotary.html', {})

def AddNotaryAction(request):
    if request.method == 'POST':
        global username, notaryList
        today = date.today()
        notary = request.POST.get('t1', False)
        pin = request.POST.get('t2', False)
        filedata = request.FILES['t3'].read()
        filename = request.FILES['t3'].name

        hashcode = hashlib.sha256(filedata).hexdigest()
        key = hashlib.sha256(pin.encode()).hexdigest()
        status = "none"
        for i in range(len(notaryList)):
            nl = notaryList[i]
            if nl[2] == hashcode:
                status = "Your eID Card Alread exists"
                break
        if status == "none":
            msg = contract.functions.RegisterHash(username, filename, hashcode, pin+"$"+notary, str(today), key).transact()
            tx_receipt = web3.eth.waitForTransactionReceipt(msg)
            notaryList.append([username, filename, hashcode, pin+"$"+notary, str(today), key])
            status = "Your notary details successfully saved in Blockchain using below details<br/>"+str(tx_receipt)
        else:
            status = "Error in saving Notary details"
        context= {'data': status}
        return render(request, 'AddNotary.html', context)

def DeleteNotaryAction(request):
    if request.method == 'GET':
        global uname, contract, notaryList
        rid = request.GET['file']
        contract.functions.deleteKey(int(rid)).transact()
        nl = notaryList[int(rid)]
        nl[2] = "Delete"
        context= {'data': "Given notary key deleted from Blockchain"}        
        return render(request, 'UserScreen.html', context)

def ViewNotary(request):
    if request.method == 'GET':
        global contract, notaryList, username
        output = '''
        <style>
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
                border-radius: 10px; 
                overflow: hidden; 
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); 
            }
            th, td {
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
                font-family: Arial, sans-serif;
                color: black;
            }
            th {
                background-color: #1aa7ec;
                color: white;
            }
            tr:nth-child(even) {
                background-color: #f2f2f2;
            }
            tr:hover {
                background-color: white;
            }
            .notary-text {
                font-style: italic;
                color: black;
                margin-top: 10px;
            }
            .container {
                width: 80%;
                margin: 0 auto;
            }
        </style>
        <div class="container">
            <h6>Notarized Documents</h6>
            <table>
                <tr>
                    <th>Owner Name</th>
                    <th>eID File Name</th>
                    <th>Hashcode</th>
                    <th>Signature</th>
                    <th>Date</th>
                    <th>Key</th>
                </tr>
        '''
        for nl in notaryList:
            if nl[0] == username:
                arr = nl[3].split("$")
                output += f'''
                <tr>
                    <td>{nl[0]}</td>
                    <td>{nl[1]}</td>
                    <td>{nl[2][:20]}</td>
                    <td>{arr[0]}</td>
                    <td>{nl[4]}</td>
                    <td>{nl[5][:20]}</td>
                </tr>
                <tr>
                    <td colspan="6" class="notary-text">Notary Text: {arr[1]}</td>
                </tr>
                '''
        output += '</table></div>'
        context = {'data': output}
        return render(request, 'UserScreen.html', context)
  

def DeleteNotary(request):
    if request.method == 'GET':
        global contract, notaryList, username
        output = '''
        <style>
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
                border-radius: 10px; 
                overflow: hidden; 
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); 
            }
            th, td {
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
                font-family: Arial, sans-serif;
                color: black;
            }
            th {
                background-color: #e74c3c;
                color: white;
            }
            tr:nth-child(even) {
                background-color: #f2f2f2;
            }
            tr:hover {
                background-color: white;
            }
            a {
                color: #3498db;
                text-decoration: none;
            }
            .notary-text {
                font-style: italic;
                color: black;
                margin-top: 10px;
            }
            .container {
                width: 80%;
                margin: 0 auto;
            }
        </style>
        <div class="container">
            <h6>Delete Notarized Documents</h6>
            <table>
                <tr>
                    <th>Owner Name</th>
                    <th>eID File Name</th>
                    <th>Hashcode</th>
                    <th>Signature</th>
                    <th>Date</th>
                    <th>Key</th>
                    <th>Delete</th>
                </tr>
        '''
        for i, nl in enumerate(notaryList):
            if nl[0] == username and nl[2] != "Delete":
                arr = nl[3].split("$")
                output += f'''
                <tr>
                    <td>{nl[0]}</td>
                    <td>{nl[1]}</td>
                    <td>{nl[2][:20]}</td>
                    <td>{arr[0]}</td>
                    <td>{nl[4]}</td>
                    <td>{nl[5][:20]}</td>
                    <td><a href='DeleteNotaryAction?file={i}'>Click Here</a></td>
                </tr>
                <tr>
                    <td colspan="7" class="notary-text">Notary Text: {arr[1]}</td>
                </tr>
                '''
        output += '</table></div>'
        context = {'data': output}
        return render(request, 'UserScreen.html', context)

def VerifierLoginAction(request):
    if request.method == 'POST':
        global username, usersList
        username = request.POST.get('t1', False)
        password = request.POST.get('t2', False)
        if username == 'admin' and password == 'admin':
            context= {'data':"Welcome "+username}
            return render(request, 'VerifierScreen.html', context)
        else:
            context= {'data':'Invalid login details'}
            return render(request, 'VerifierLogin.html', context)  

def VerifierLogin(request):
    if request.method == 'GET':
       return render(request, 'VerifierLogin.html', {}) 

def index(request):
    if request.method == 'GET':
       return render(request, 'index.html', {})    

def Login(request):
    if request.method == 'GET':
       return render(request, 'Login.html', {})

def Signup(request):
    if request.method == 'GET':
       return render(request, 'Signup.html', {})    
    
def SignupAction(request):
    if request.method == 'POST':
        global contract, usersList
        username = request.POST.get('username', False)
        password = request.POST.get('password', False)
        contact = request.POST.get('contact', False)
        email = request.POST.get('email', False)
        address = request.POST.get('address', False)
        record = 'none'
        for i in range(len(usersList)):
            ul = usersList[i]
            if ul[0] == username:
                record = "exists"
                break
        if record == 'none':
            msg = contract.functions.saveUser(username, password, contact, email, address).transact()
            tx_receipt = web3.eth.waitForTransactionReceipt(msg)
            usersList.append([username, password, contact, email, address])
            context = {'data': 'Signup process completed and record saved in Blockchain<br/>' + str(tx_receipt)}
            return render(request, 'Signup.html', context)
        else:
            context = {'data': username + ' Username already exists'}
            return render(request, 'Signup.html', context)


def LoginAction(request):
    if request.method == 'POST':
        global username, usersList
        username = request.POST.get('t1', False)
        password = request.POST.get('t2', False)
        status = 'none'
        for i in range(len(usersList)):
            ul = usersList[i]
            if ul[0] == username and ul[1] == password:
                status = 'success'
                break
        if status == 'success':
            context= {'data':"Welcome "+username}
            return render(request, 'UserScreen.html', context)
        else:
            context= {'data':'Invalid login details'}
            return render(request, 'Login.html', context)            


        
        



        
            
