import os, sys
import time

if sys.platform != "win32":
    import daemon
    import subprocess
else:
    import pythoncom
    import win32serviceutil
    import win32service
    import win32event
    import servicemanager
    import socket


# genericDaemon is just a control panel for the Daemon and service classes
class genericDaemon(object):

    def __init__(self,mainProgram=None,waitTime=1,daemonName=None,errLog="None"):
        
        self.waitTime       = waitTime
        self.mainProgram    = mainProgram
        self.daemonName     = daemonName
        self.pyName         = sys.argv[0]
        self.errLog         = errLog

        # assign command from user
        try:
            self.comm       = sys.argv[1]
        except:
            self.comm       = ""

        
        
    def makeDaemon(self):

        # set daemonName if left blank
        if self.daemonName == None:
            self.daemonName = self.pyName

        # check user input    
        if not self.goodInput():
            self.usage()
            return


        # check if we're on windows
        if sys.platform == "win32":

#####################################################################
######################## Make Windows Service #######################
            
            # make windows service
            pyFile = self.pyName.split(".")[0]
            func   = str(self.mainProgram).split(" ")[1]
            #os.system("python CreateService.py -c " + self.comm + " -p " + pyFile + " -f " + func + " -n " + self.daemonName)



    # create a string that will be input into another python doc
            serviceString = """
import pythoncom
import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import time
import sys


class AppServerSvc (win32serviceutil.ServiceFramework):

    # Our service configurations
    _svc_name_          = "%s"
    _svc_display_name_  = "%s"
    waitTime            = %s
    pyFile              = "%s"
    func                = "%s"
    errFile             = "%s"
    

    def __init__(self,args):
        win32serviceutil.ServiceFramework.__init__(self,args)
        self.hWaitStop = win32event.CreateEvent(None,0,0,None)
        socket.setdefaulttimeout(60)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_,''))

        self.main()

    def main(self):
        while True:     

            mainLoop()
            
            if win32event.WaitForSingleObject(self.hWaitStop, AppServerSvc.waitTime * 1000) == win32event.WAIT_OBJECT_0: 
                break  
        

    ##################### The Service #######################
def mainLoop():
    
    try:
        module = __import__(AppServerSvc.pyFile)
        mainProgram = getattr(module, AppServerSvc.func)
    except:
        file = open(errFile, "a")

        file.write("Module or function failed to load")
        file.close()
            
    try:
        mainProgram()
    except:
        file = open(errFile, "a")

        file.write("Main Program failed to run")
        file.close()    
        

if __name__ == "__main__":
    win32serviceutil.HandleCommandLine(AppServerSvc)
""" % (self.daemonName,self.daemonName,self.waitTime,pyFile,func,self.errLog)


            # save string to a file
            fileName = self.daemonName + "_SERVICE.py"
            serviceFile = open(fileName, "w")
            serviceFile.write(serviceString)

            serviceFile.close()

            # create windows service
            os.system("python " + fileName + " " + self.comm)


        
        else:
            
#####################################################################
############################ Make Daemon ############################
            
            myDaemon = Daemon(self.mainProgram,self.waitTime,self.daemonName)
                
            if self.comm.lower() == "start":
                myDaemon.start()
                        
            elif self.comm.lower() == "stop":
                myDaemon.stop()

    def goodInput(self):
        if sys.platform != "win32":
            if self.comm.lower() != "start" and self.comm.lower() != "stop":
                return False
            else:
                return True
        else:
            if self.comm.lower() != "start" and self.comm.lower() != "stop" and self.comm.lower() != "install" and self.comm.lower() != "remove":
                return False
            else:
                return True
            
    def usage(self):
        if sys.platform != "win32":
            print"\n"
            print self.daemonName + " usage:"
            print "start    Starts the daemon"
            print "stop     Stops the daemon"
            print "\n"
        else:
            print"\n"
            print self.daemonName + " usage:"
            print "install      Installs the service"
            print "start        Starts the service"
            print "stop         Stops the service"
            print "remove       Deletes the service"
            print "\n"
                    
                    
#################################################################################
#################################### CLASSES ####################################

if sys.platform != "win32":
    
#----------------------------------- DAEMON ------------------------------------#

    # Daemon class will only run on Linux/OSX
    class Daemon(genericDaemon):
        def __init__(self,mainProgram=None,waitTime=1,daemonName=None):
            self.daemonName = daemonName
            self.waitTime = waitTime
            self.mainProgram = mainProgram
            self.pyName = sys.argv[0]
            
        def start(self):
            print "Starting " + self.daemonName + '...'
            
            # check if daemon is running
            daemonInfo = self.isRunning("clean")
            
            if (len(daemonInfo) > 1 and self.daemonName == self.pyName) or (len(daemonInfo) > 0 and self.daemonName != self.pyName):
                print self.daemonName + " is already running."
        
            else:
                
            # change name of python process
                try:
                    import setproctitle
                    setproctitle.setproctitle(self.daemonName)
                    #setproctitle.setproctitle("testing!")
                except:
                    pass # Ignore errors, since this is only cosmetic
                
                try:
                    with daemon.DaemonContext():
                        while True:
                            
                            self.mainProgram()
                            time.sleep(self.waitTime)
                            #time.sleep(5)
                        
                except:
                    print self.daemonName + " failed to start"
                    
                
        def stop(self):
            
            daemonInfo = self.isRunning("clean")
                
            #if not lookup:
            if not daemonInfo:
                print self.daemonName + " is not running"
                exit
            else:
                
                #get pids from daemonInfo
                pids = [daemons[0] for daemons in daemonInfo]
                
                print str(len(pids)) + " instances of " + self.daemonName + " running"
                
                print "Stopping..."
                for pid in pids:
                    try:
                        kill = subprocess.check_output("kill " + pid, shell=True)
                        
                        print self.daemonName + " stopped"
                    except:
                        print "Failed to kill PID: " + pid
        
        def isRunning(self, clean="clean"):
            try:
                lookup = subprocess.check_output("ps -A | grep " + self.daemonName + " | grep -v grep | grep -v stop", shell=True)
                
            except:
                return []
            
            if clean == "clean":
                daemonInfo = [each.split(" ") for each in lookup.rstrip().split("\n")]
                
                for daemons in daemonInfo:
                    while '' in daemons:
                        daemons.remove('')
                
                return daemonInfo
            
            return lookup

else:
    pass            
