import boto.ec2
from signl.settings import AWS_ACCESS_KEY_ID,AWS_SECRET_ACCESS_KEY
import time
from models import * 
from datetime import datetime
import requests
from celery import task
from scheduler.views import releaseAllAccounts

SINGLE_WORKER = 'ami-d3701bba'
TWO_WORKERS = 'ami-3b5d3652'

class Ec2(object):
    def __init__(self):
        self.conn = boto.ec2.connect_to_region("us-east-1",aws_access_key_id=AWS_ACCESS_KEY_ID,aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
        self.requests = []
        self.instances = []
        self.ips = []
        releaseAllAccounts()

    @task()
    def shutdown(self):
        time.sleep(300)
        releaseAllAccounts()
        self.stopAllInstances()
        self.cancelAllRequest()
        self.releaseAllIPs()

    def releaseAllIPs(self):
        for item in self.ips:
            item.disassociate()
        for item in self.ips:
            item.release()

    def cancelAllRequest(self):
        print "stop all requests"
        print self.requests
        self.conn.cancel_spot_instance_requests(self.requests)

    def stopAllInstances(self):
        print "stopping all instances"
        print self.instances
        self.conn.terminate_instances(self.instances)
    
    def stopAndBringNewInstance(self,instanceType,needEIP):
        self.launchSpotInstance(1,instanceType,needEIP)
        self.stopCurrentInstance()
        
    def stopCurrentInstance(self):
        current_instance_id = self.getCurrentInstanceId()
        self.conn.terminate_instances(instance_ids=[current_instance_id])

    def getCurrentInstanceId(self):
        url ="http://169.254.169.254/latest/meta-data/instance-id"
        c = requests.get(url)
        return c.content

    def saveRequestsAndInstance(self,requests):
        for item in requests:
            self.requests.append(item.id)
            self.instances.append(item.instance_id)
    
    def allocateAddressToInstance(self):
        for item in self.instances:
            new_address = self.conn.allocate_address()
            self.ips.append(new_address)
            new_address.associate(item)
            #time.sleep(3)

    def _isAllRequestReady(self,requests):
        for item in requests:
            if item.state != 'active':
                return False
        return True
    
    def _isAllInstanceReady(self,reservation):
        allInstance = 0
        running = 0
        for item in reservation:
            for instance in item.instances:
                allInstance +=1
                if instance.update() == 'running':
                    running +=1
        print "all instances %s" % allInstance
        print "running %s " % running
        if float(running)/float(allInstance) > 0.5:
            return True
        else:
            return False
    
    def _checkSpotRequestReady(self,requests):
        ids = [o.id for o in requests]
        updated_requests = self.conn.get_all_spot_instance_requests(request_ids=ids)
        isReady = self._isAllRequestReady(updated_requests) 
        while isReady == False:
            print "request not ready waiting 30s"
            time.sleep(30)
            updated_requests = self.conn.get_all_spot_instance_requests(request_ids=ids)
            isReady = self._isAllRequestReady(updated_requests) 
        return True


    def _checkSpotInstanceReady(self,requests):
        ids = [o.id for o in requests]
        updated_requests = self.conn.get_all_spot_instance_requests(request_ids=ids)     
        self.saveRequestsAndInstance(updated_requests)
        instance_ids=[o.instance_id for o in updated_requests]
        reservation = self.conn.get_all_instances(instance_ids=instance_ids)
        isReady = self._isAllInstanceReady(reservation)
        while isReady == False:
            print "Instances not ready waiting 15s"
            time.sleep(30)
            reservation = self.conn.get_all_instances(instance_ids=instance_ids)
            isReady = self._isAllInstanceReady(reservation)
        return True
 
     

    def launchSpotInstance(self,count,type,needEIP=None):
        if type == 'single_worker':
            img_id = SINGLE_WORKER
        elif type == 'two_workers':
            img_id = TWO_WORKERS
        else:
            raise Exception('no image found')
        requests = self.conn.request_spot_instances(price='0.06',image_id=img_id,count=count,key_name='CSkey',security_groups=['quick-start-1'],instance_type='m1.small')
        
        print "sent requests"
        time.sleep(220)
        print "checkout sport request"
        self._checkSpotRequestReady(requests)
        
        print "checkout inztance"
        self._checkSpotInstanceReady(requests)
        
        if needEIP == True:
            print "associate instance ip "
            self.allocateAddressToInstance()

        print "ready"
        return True

