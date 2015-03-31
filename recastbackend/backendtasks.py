from celery import shared_task
import celery
import zipfile
import os
import shutil
import recastapi.request
import json
import uuid
import importlib
import redis
import emitter
from datetime import datetime

def socketlog(jobguid,msg):
  red = redis.StrictRedis(host = celery.current_app.conf['CELERY_REDIS_HOST'],
                            db = celery.current_app.conf['CELERY_REDIS_DB'], 
                          port = celery.current_app.conf['CELERY_REDIS_PORT'])
  io  = emitter.Emitter({'client': red})

  msg_data = {'date':datetime.now().strftime('%Y-%m-%d %X'),'msg':msg}

  #also print directly
  print "{date} -- {msg}".format(**msg_data)

  io.Of('/monitor').In(str(jobguid)).Emit('room_msg',msg_data)
  
import requests
def download_file(url,download_dir):
    local_filename = url.split('/')[-1]
    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    download_path = '{}/{}'.format(download_dir,local_filename)
    with open(download_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024): 
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                f.flush()
    return download_path    

@shared_task
def postresults(jobguid,requestId,parameter_point,resultlister):
  workdir = 'workdirs/{}'.format(jobguid)
  resultdir = 'results/{}/{}'.format(requestId,parameter_point)
  
  if(os.path.exists(resultdir)):
    shutil.rmtree(resultdir)
    
  os.makedirs(resultdir)  

  for result,resultpath in ((r,os.path.abspath('{}/{}'.format(workdir,r))) for r in resultlister()):
    if os.path.isfile(resultpath):
      shutil.copyfile(resultpath,'{}/{}'.format(resultdir,result))
    if os.path.isdir(resultpath):
      shutil.copytree(resultpath,'{}/{}'.format(resultdir,result))

  socketlog(jobguid,'uploading resuls')

  #also copy to server
  subprocess.call('''ssh {user}@{host} "mkdir -p {base}/results/{requestId}/{point} && rm -rf {base}/results/{requestId}/{point}/dedicated"'''.format(
    user = BACKENDUSER,
    host = BACKENDHOST,
    base = BACKENDBASEPATH,
    requestId = requestId,
    point = parameter_point)
  ,shell = True)
  subprocess.call(['scp', '-r', resultdir,'{user}@{host}:{base}/results/{requestId}/{point}/dedicated'.format(
    user = BACKENDUSER,
    host = BACKENDHOST,
    base = BACKENDBASEPATH,
    requestId = requestId,
    point = parameter_point
  )])
  
  socketlog(jobguid,'done')
  return requestId

    
@shared_task
def prepare_job(jobguid,jobinfo):
  print "job info is {}".format(jobinfo)
  print "job uuid is {}".format(jobguid)
  workdir = 'workdirs/{}'.format(jobguid)

  input_url = jobinfo['run-condition'][0]['lhe-file']
  socketlog(jobguid,'downloading input files')

  filepath = download_file(input_url,workdir)

  print "downloaded file to: {}".format(filepath)
  socketlog(jobguid,'downloaded input files')


  with zipfile.ZipFile(filepath)as f:
    f.extractall('{}/inputs'.format(workdir)) 
  
  return jobguid

@shared_task
def prepare_workdir(fileguid,jobguid):
  uploaddir = 'uploads/{}'.format(fileguid)
  workdir = 'workdirs/{}'.format(jobguid)
  
  os.makedirs(workdir)

  socketlog(jobguid,'prepared workdir')

  return jobguid
  
def prechain(request_uuid,point,jobguid,queuename):
  request_info = recastapi.request.request(request_uuid)
  jobinfo = request_info['parameter-points'][point]

  pre = (   prepare_workdir.subtask((request_uuid,jobguid),queue=queuename) |
            prepare_job.subtask((jobinfo,),queue=queuename)
        )
  return pre

def postchain(request_uuid,point,queuename,resultlist):           
  post = ( postresults.subtask((request_uuid,point,resultlist),queue=queuename) )
  return post
  
def wrapped_chain(request_uuid,point,queuename,modulename):
  analysis_module = importlib.import_module(modulename)
  
  jobguid = uuid.uuid1()
  
  pre  =  prechain(request_uuid,point,jobguid,queuename)
  post =  postchain(request_uuid,point,queuename,analysis_module.resultlist)

  chain = (pre | analysis_module.get_chain(queuename) | post)
  return (jobguid,chain)
