#!/usr/local/bin/python3

import os
import io
import subprocess
import requests
import argparse
import xml.etree.ElementTree as ElementTree
import lxml.html

parser = argparse.ArgumentParser()
parser.add_argument('username', type=str)
parser.add_argument('password', type=str)
parser.add_argument('--input', '-i', help='file with foldernames', type=str, required=True)
parser.add_argument('--url', '-u', type=str, default="https://ificloud.xsitepool.tu-freiberg.de")
parser.add_argument('--verbose', action='count', default=0)

args = parser.parse_args()

with open(args.input) as file:
    foldernames = file.readlines()

foldernames = [name.strip() for name in foldernames]

# get the users folder name, this is either the name itself or a uuid (when using ldap)
command_get_html = "curl -s -X GET -u "
command_get_html += args.username + ":" 
command_get_html += args.password + " '" 
command_get_html += args.url 
command_get_html += "/index.php/apps/files'"

html_string = subprocess.check_output(command_get_html, shell=True).decode('utf8').strip('\n')
html = lxml.html.fromstring(html_string)
webdavurls = html.xpath('//*[starts-with(@id, "webdavurl")]')
for url in webdavurls:
    webdavfolder = url.get('value')

webdavfolder = webdavfolder.split("/dav/files/")[1].split("/")[0]

for foldername in foldernames:
    # create folder
    command_create = "curl -s -X MKCOL -u " 
    command_create += args.username + ":" 
    command_create += args.password + " '" 
    command_create += args.url 
    command_create += "/remote.php/dav/files/" 
    command_create += webdavfolder + "/" 
    command_create += foldername + "'"

    if args.verbose:
        print(command_create)

    os.system(command_create)

    # share folder
    command_share = "curl -s -X POST -u "
    command_share += args.username + ":"
    command_share += args.password + " -d "
    command_share += "'path=/" + foldername + "&shareType=3&publicUpload=true&permissions=4' '"
    command_share += args.url + "/ocs/v2.php/apps/files_sharing/api/v1/shares' -H \"OCS-APIRequest: true\""

    if args.verbose:
        print(command_share)

    resp = subprocess.check_output(command_share, shell=True).decode('utf8').strip('\n')

    if args.verbose:
        print(resp)

    root = ElementTree.fromstring(resp)

    for urls in root.iter('url'):
        print(foldername + " - " + urls.text)
        
    for ids in root.iter('id'):
        # udpate perission
        command_perm = "curl -s -o /dev/null -X PUT -u "
        command_perm += args.username + ":"
        command_perm += args.password + " -d "
        command_perm += "'permissions=4' '"
        command_perm += args.url + "/ocs/v2.php/apps/files_sharing/api/v1/shares/" + ids.text + "' -H \"OCS-APIRequest: true\""
        
        if args.verbose:
            print(command_perm)
            
        os.system(command_perm)
