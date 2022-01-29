import sys,os
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from getfilelistpy import getfilelist

def makeThumb(fromm,too):
  os.system('convert '+fromm+' -resize 800x  '+too+" 2>/dev/null")

def getN(fil):
  #print('getN ',fil)
  os.system('exiftool -overwrite_original  -all= '+fil)
  with open('google.txt','r') as f:
    lines=f.readlines()
    for line in lines: 
      ll=line.strip().split()
      if(len(ll)!=2):
        continue
      if(ll[0]==fil):
        return ll[1].split('/')[-2]
  return 'ERROR'

glinks={}

def processGfiles():
  global glinks
  if(os.path.exists('google.txt')):
    with open('google.txt','r') as f:
       lista=f.readlines()
       for linia in lista:
         ll=linia.split()
         if(len(ll)==2):
            glinks[ll[0].strip()]=ll[1].strip()

processGfiles()


def procImg(line):
 if(line[:6]=='IMGIMG'):
   imgfile=line.split()[1].strip()
   numer=getN(imgfile)
   im=imgfile.split('.')
   im[-2]=im[-2]+'_small'
   thumbf='.'.join(im)
   if(not(os.path.exists(thumbf))):
     makeThumb(imgfile,thumbf)
   numers=getN(thumbf)
   return '[URL=https://drive.google.com/file/d/'+numer+'/preview][IMG]http://drive.google.com/uc?export=view&id='+numers+'[/IMG][/URL]'
 else:
  return line

def set_permission(service, file_id):
    print('set permission', file_id)
    try:
        permission = {'type': 'anyone',
                      'value': 'anyone',
                      'role': 'reader'}
        return service.permissions().create(fileId=file_id,body=permission).execute()
    except errors.HttpError as error:
        return print('Error while setting permission:', error)

def processFile(fil):
  with open(fil,'r') as f:
    lines=f.readlines()
    with open(fil.replace('.txt','_compiled.txt'),'w') as g:
      for line in lines:
         g.write(procImg(line))

SCOPES = ['https://www.googleapis.com/auth/drive']
rootDir=os.path.dirname(os.path.realpath(__file__))

if(not(os.path.exists(rootDir+'/credentials.json'))):
    print("credentials.json file needed. Follow https://developers.google.com/drive/api/v3/quickstart/python to generate it")
    sys.exit(0)

def main():
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    creds = None
    
    if os.path.exists(rootDir+'/token.json'):
        creds = Credentials.from_authorized_user_file(rootDir+'/token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                rootDir+'/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(rootDir+'/token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('drive', 'v3', credentials=creds)

        # Call the Drive v3 API
        cwd=os.getcwd().split('/')[-1]
        results = service.files().list(q="fullText contains '"+cwd+"'",
            pageSize=5, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])

        if not items:
            print(cwd+' not found.')
            return
        if (len(items)>1):
            print('more than one '+cwd+' found.')
            return            
        item=items[0]
        print(u'{0} ({1})'.format(item['name'], item['id']))
        relacjaDirId=item['id']+''
        
        results = service.files().list(q="'"+relacjaDirId+"' in parents ",
            pageSize=500, fields="nextPageToken, files(id, name, webViewLink, permissions)").execute()
        items = results.get('files', [])

        if not items:
            print('No files found.')
            return
        
        for item in items:
          ok=None
          #print(u'{0} ({1}, {2}, {3})'.format(item['name'], item['id'], item['webViewLink'], item['permissions']))
          
          if(item['name'] not in glinks.keys()):
            ok='nie ma'
            if('.jpg' in item['name'] or '.png' in item['name'] or '.JPG' in item['name'] or '.PNG' in item['name']):
              ok='generate'
          if(ok==None):
            print(item['name'],'  exists as shareable link')
          if(ok=='generate'):
            #print(item['webViewLink'])
            print(item['name'],' generating')
            set_permission(service,item['id'])
            glinks[item['name']]=item['webViewLink'].replace('view?usp=drivesdk','preview')
          
    except HttpError as error:
        print(f'An error occurred: {error}')

main()

with open('google.txt','w') as f:
  for k,v in glinks.items():
    vv=v.replace('view?usp=sharing','preview')
    f.write(k+' '+vv+"\n")

processFile(sys.argv[1])
       
       
       
