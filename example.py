from genericDaemon import genericDaemon
import os,sys

def mainProgram():
    
    if sys.platform == "win32":
        myFile = open("C:\someFile.txt", "a")
    else:
        myFile = open("/Users/someFile.txt", "a")
            
    myFile.write("Just a test \n")
    myFile.close()


if __name__ == "__main__":
    mydaemon = genericDaemon(mainProgram,10,"TS")
    mydaemon.makeDaemon()

