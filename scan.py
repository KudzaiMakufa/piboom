#!/usr/bin/env python
import RPi.GPIO as GPIO
import MFRC522
import json
import requests
from Tkinter import *
import time

# Keys
DEFAULT_KEY = [0xFF,0xFF,0xFF,0xFF,0xFF,0xFF]

# Selecting key
KEY = DEFAULT_KEY


def format_uid(uid):
    s = ""
    for i in range(0, len(uid)):
        s += "%x" % uid[i]
    return s.upper()
#code to scan tag

def scantag():

    RFID = MFRC522.MFRC522()

    print "# RFID Reader\n"
    print "Info: Leave the sector field empty to exit.\n"

    # Get tag size if available
    (Status, TagSize) = RFID.Request(RFID.PICC_REQIDL)

    while True:

        if TagSize > 0:
            message = "Sector [1 - %s]: " % (TagSize - 1)
        else:
            message = "Sector: "

        try:
            Sector = 1
        except:
            print""
            break
        else:
            print("Waiting for Next Car...\n")

        while True:

            (Status, TagSize) = RFID.Request(RFID.PICC_REQIDL)

            if Status != RFID.MI_OK:
                continue

            if TagSize < 1:
                print "Can't read tag properly!"
                break

            if Sector < 1 or Sector > (TagSize - 1):
                print "Sector out of range (1 - %s)\n" % (TagSize - 1)
                break

            # Selecting blocks
            BaseBlockLength = 4
            if Sector < 32:
                BlockLength = BaseBlockLength
                StartAddr = Sector * BlockLength
            else:
                BlockLength = 16
                StartAddr = 32 * BaseBlockLength + (Sector - 32) * BlockLength

            BlockAddrs = []
            for i in range(0, (BlockLength - 1)):
                BlockAddrs.append((StartAddr + i))
            TrailerBlockAddr = (StartAddr + (BlockLength - 1))

            # Initializing tag
            (Status, UID) = RFID.Anticoll()

            if Status != RFID.MI_OK:
                break

            # Reading sector
            RFID.SelectTag(UID)
            Status = RFID.Auth(RFID.PICC_AUTHENT1A, TrailerBlockAddr, KEY, UID)
            data = []
            text_read = ""
            if Status == RFID.MI_OK:
                for block_num in BlockAddrs:
                    block = RFID.Read(block_num)
                    if block:
                        data += block
                if data:
                    text_read = "".join(chr(i) for i in data)
                print "UID:  ", format_uid(UID)
                print "Data: ", text_read, "\n"
                if text_read == "":
                    phone = "null"
                elif text_read != "":
                    phone = text_read

                payload = {'rfidno': format_uid(UID) ,'clientid':phone}
                r = requests.post("http://server-ip/autoboom/public/park/changepoints", data=payload)
                result = r.json()
                print result["save"]

                # open gui with details

                window = Tk()

                window.title("Auto Boomgate")
                window.resizable(False, False)

                window.attributes('-zoomed', False)

                w = 500  # width for the Tk root
                h = 300  # height for the Tk root

                # get screen width and height
                ws = window.winfo_screenwidth()  # width of the screen
                hs = window.winfo_screenheight()  # height of the screen

                # calculate x and y coordinates for the Tk root window
                x = (ws / 2) - (w / 2)
                y = (hs / 2) - (h / 2)

                # set the dimensions of the screen
                # and where it is placed
                window.geometry('%dx%d+%d+%d' % (w, h, x, y))

                btn = Button(window, text="Scan", command=scantag)
                #mvlb = Label(window, text=" pro")
                lbl = Label(window, text="                  Auto Boomgate")
                rfidno = Label(window, text="       Card No")
                clientname = Label(window, text="       Phone Numbe")
                pointsleft = Label(window, text="       Parking Points left")
                boomstate = Label(window, text= "Boomgate State")
                allocatedslot = Label(window, text= "Allocated Slot")


                decision = ""
                if result["save"] == "open" and result["reason"] == "login" :
                    decision = "Welcome : Proceed to \n slot "+str(result["slot"])+" "

                elif result["save"] == "close" and result["reason"] == "pointsout" :
                    decision = "You are out of parking credits \n Recharge your account"

                elif result["save"] == "close" and result["reason"] == "deducterror" :
                    decision = "Scan your tag again "
                elif result["save"] == "open" and result["reason"] == "exit" :
                    decision = "Thank you for parking with us \n AutoBoomGate"
                elif result["save"] == "close" and result["reason"] == "noaccount" :
                    decision = "The Card is not registered in system \n AutoBoomGate"

                dscnlab = Label(window,text = decision)
                inprfidno = Label(window, text=format_uid(UID))
                inpclientname = Label(window, text=result["name"])
                inppointsleft = Label(window, text=result["points"])
                inpboomstate = Label(window,text = result["save"])
                inallocatedslot = Label(window, text=result["slot"])
               # mvlb.grid(column=120, row=0)
                lbl.grid(column=2, row=1)
                rfidno.grid(column=1, row=2)
                clientname.grid(column=1, row=3)
                pointsleft.grid(column=1, row=4)
                boomstate.grid(column = 1,row = 5)
                allocatedslot.grid(column = 1,row = 6)
                dscnlab.grid(column=2, row=7)

                inprfidno.grid(column=3, row=2)
                inpclientname.grid(column=3, row=3)
                inppointsleft.grid(column=3, row=4)
                inpboomstate.grid(column=3,row = 5)
                inallocatedslot.grid(column =3,row=6)

             

                window.after(7000, lambda: window.destroy())
                window.mainloop()


            else:
                print "Can't access sector", Sector, "!\n"
            RFID.StopCrypto1()
            break

    RFID.AntennaOff()
    GPIO.cleanup()
scantag()



