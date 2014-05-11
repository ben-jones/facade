from __future__ import division
import threading
import subprocess
import time
import paramiko


# client commands
class Command(object):
    def __init__(self, cmd):
        self.cmd = cmd
        self.process = None

    def run(self, timeout):
        def target():
            print 'Thread started'
            self.process = subprocess.Popen(self.cmd, shell=True)
            self.process.communicate()
            print 'Thread finished'

        thread = threading.Thread(target=target)
        thread.start()

        thread.join(timeout)
        if thread.is_alive():
            print 'Terminating process'
            self.process.terminate()
            thread.join()
        print self.process.returncode


class Router:
    def __init__(self, ip, user, passwd):
        self.ip = ip
        self.user = user
        self.passwd = passwd
        self.name = 'R'
        #self.logfile = initialize_logfile()
        self.host = self.connectHost(ip, user, passwd)
        self.remoteCommand('mkdir -p /tmp/browserlab/')
        #self.initialize_servers()

    def connectHost(self, ip, user, passwd):
        host = paramiko.SSHClient()
        host.load_system_host_keys()
        host.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print 'DEBUG: connect to ' + ip + ' user: ' + user + ' pass: ' + passwd
        host.connect(ip, username=user, password=passwd)
        return host

    def remoteCommand(self, cmd):
        """This should be used for starting iperf servers, pings,
        tcpdumps, etc.
        """
        stdin, stdout, stderr = self.host.exec_command(cmd)
        #for line in stdout:
        #    print 'DEBUG: '+ line
        return

    def command(self, cmd):
        self.remoteCommand(cmd['CMD'])
        logcmd(str(cmd), self.name)
        return

def run(cmd, logfile=None):
    p = subprocess.Popen(cmd, shell=True, universal_newlines=True, stdout=logfile)
    ret_code = p.wait()
    if logfile:
        logfile.flush()
    return ret_code

def set_network_delay(router, NET_DEL):
    delay = str(NET_DEL/2.0)
    router.remoteCommand('tc qdisc del dev eth1 root; tc qdisc del dev eth0 root')
    if NET_DEL != 0:
        router.remoteCommand('tc qdisc add dev eth1 root netem delay '+delay+'ms; tc qdisc add dev eth0 root netem delay '+delay+'ms;')
    return

def set_const(REQ_DEL, SIZE):
    delay = str(REQ_DEL/1000.0)
    psize = str(SIZE)
    open('htpt/const.py', 'w').write('TIMEOUT='+delay+'\nSIZE='+psize)
    return

def main():
    # both NET_DEL and REQ_DEL are in ms
    timeout = 10
    router = Router('192.168.1.1', 'root', 'passw0rd')
    server = Router('192.168.20.1', 'gtnoise', 'gtnoise')

    for NET_DEL in [0,10,40,100,500]: #150,200,300,400,500,1000]
        set_network_delay(router, NET_DEL)
        for REQ_DEL in [0,10,40,100,500]:
            for SIZE in [50, 100, 200, 500]:
                set_const(REQ_DEL, SIZE)

                filename = str(NET_DEL)+'_'+str(REQ_DEL)+'_'+str(SIZE)+'.log'

                server.remoteCommand('kill -9 $(pgrep htpt); ./htpt/htpt/htpt.py -server > /home/gtnoise/Documents/server_'+filename)

                time.sleep(1)

                print "START 200; NET_DEL: "+str(NET_DEL)+"ms; REQ_DEL:"+str(REQ_DEL)+"ms; SIZE:"+str(SIZE)+" bytes"
                run('./htpt/htpt.py -client', open('/home/gtnoise/Documents/search/client_'+filename, 'w'))
                print "DONE"

                run('cp /home/gtnoise/htpt/log-file.txt /home/gtnoise/Documents/search/tp_'+filename)
                server.remoteCommand('kill -9 $(pgrep htpt)')

    router.host.close()
    server.host.close()

    return
