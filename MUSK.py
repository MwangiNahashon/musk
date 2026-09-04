# PIL module is used to extract pixels of images and modify them
from tkinter import *
import tkinter as tk
from tkinter import filedialog,messagebox
from PIL import Image
from PIL import ImageTk
import time
import os
 
# Converting the encoded message into 8-bit binary values using the ASCII table of values
def messagefun(key, message):
 
        # list of binary codes
        # of given message
        binarymessage = []
        for i in key:
            binarymessage.append(format(ord(i), '08b'))

 
        for i in message:
            binarymessage.append(format(ord(i), '08b'))
        return binarymessage
 
# Pixels of the image that will be used are
# Converted according to the binary message and finally returned

def modified(pixel, key, message):
 
    datalist = messagefun(key, message)
    lendata = len(datalist)
    iminfo = iter(pixel)

 
    for i in range(lendata):
 
        # Extracting 3 pixels from the image at a time
        pixel = [value for value in iminfo.__next__()[:3] +
                                iminfo.__next__()[:3] +
                                iminfo.__next__()[:3]]
 
        # Pixel value should be made
        # odd for 1 and even for 0
        for j in range(0, 8):
            if (datalist[i][j] == '0' and pixel[j]% 2 != 0):
                pixel[j] -= 1
 
            elif (datalist[i][j] == '1' and pixel[j] % 2 == 0):
                if(pixel[j] != 0):
                    pixel[j] -= 1
                else:
                    pixel[j] += 1
                
 
        # The ninth pixel of every set tells us
        # whether to stop or to read further.
        # 0 means keep reading 1 means the
        # message is over.
        if (i == lendata - 1):
            if (pixel[-1] % 2 == 0):
                if(pixel[-1] != 0):
                    pixel[-1] -= 1
                else:
                    pixel[-1] += 1
 
        else:
            if (pixel[-1] % 2 != 0):
                pixel[-1] -= 1
 
        pixel_final = tuple(pixel)
        yield pixel_final[0:3]
        yield pixel_final[3:6]
        yield pixel_final[6:9]
 
def track_encoder(newimg, key, message):
    w = newimg.size[0]
    (a, b) = (0, 0)
 
    for pixel in modified(newimg.getdata(), key, message):
 
        # Getting the modified pixels from the modified() function
        newimg.putpixel((a, b), pixel)
        if (a == w - 1):
            a = 0
            b += 1 
        else:
            a += 1
 
# Encode data into image
def encode():
    screen1=tk.Tk()
    screen1.title("ENCRYPTION")
    screen1.geometry("720x660")
    screen1.resizable(False,False)
    screen1.configure(bg="#2f4155")
    Label(screen1,text="Hide Text in Image(Image should have *.png file extension)",bg="#2f4155",fg="black",font="Times 18 italic bold").place(x=10,y=10)
    #icon
    image_icon=PhotoImage(file="icon.png")
    screen1.iconphoto(False,image_icon)
    #First Frame
    frame1=Frame(screen1,bd=3,bg="#742921",width=340,height=280,relief=GROOVE)
    frame1.place(x=10,y=55)
    lbl=Label(screen1,bg="#742921")
    lbl.place(x=10,y=55)
    #insert = input("Enter name of image with extension e.g. image.png: ")
    def Open_Cover_Image():
        global img
        filename = filedialog.askopenfilename(initialdir=os.getcwd(),
                                        title='Select Cover Image (*.png)',
                                        filetype=(("PNG file","*.png"),("All file","*.png")))
        img=Image.open(filename)
        #pil_image=img.copy()
        image=ImageTk.PhotoImage(img)
        lbl.configure(image=image,width=340,height=280)
        lbl.image=image
    #image = Image.open(insert, 'r')
    #key = input("Enter your four character secret key: ")
     #Second frame
    frame2=Frame(screen1,bd=3,width=340,height=280,bg="white",relief=GROOVE)
    frame2.place(x=358,y=55)
    #third Frame
    frame3=Frame(screen1,bd=3,bg="#07493d",width=600,height=100,relief=GROOVE)
    frame3.place(x=10,y=400)
    user_key_Label=tk.Label(frame3, text="Enter key (4 characters): ", font="Times 14 italic bold", bg="#07493d")
    user_key_Label.grid(row=0, column=0)
    user_key = tk.Entry(frame3, width=10,show="*",font="Times 14 italic bold")
    user_key.grid(row=0, column=1)
    stego_Label=tk.Label(frame3, text="Enter name of stego image: ", font="Times 14 italic bold", bg="#07493d")
    stego_Label.grid(row=1, column=0)
    stego = tk.Entry(frame3, width=20, font="Times 14 italic bold")
    stego.grid(row=1, column=1)
    Label(screen1,text="NOTE: KEY LENGTH SHOULD BE EXACTLY FOUR CHARACTERS",bg="grey",fg="black",font="Times 16 italic bold").place(x=10,y=350)
    # Create the message entry field
    user_message_label = tk.Label(frame2, text="Enter Message: ",bg="white", font="Times 8 italic bold")
    user_message_label.grid(row=1, column=0)
    user_message = tk.Text(frame2, width=30,bg="white",fg="black",height=17,)
    user_message.grid(row=1, column=1)
    scrollbar = tk.Scrollbar(frame2, command=user_message.yview)
    user_message.configure(yscrollcommand=scrollbar.set)
    scrollbar.grid(row=1, column=2, sticky="ns")
    def key_check():
        start_time = time.time()
        message = user_message.get("1.0","end")
        key = user_key.get()
        set_stego=stego.get()
        for char in message:
            if char != " ":
                if len(message.strip()) == 0:
                    messagebox.showerror("*** Message Error !!! ***", "The Message Field is Empty")
                    messagebox.showerror("*** Overall ***", "All entries must be filled in the recommended format")
                    break
                elif len(key) != 4:
                    messagebox.showerror("*** Key Error !!! ***", "Key length not recommended")
                    break
                elif len(set_stego) == 0:
                    messagebox.showerror("*** Stego Name Error1 !!! ***", "You haven't choosen a name for your stego image")
                    break
                else:
                    newimg=img.copy()
                    track_encoder(newimg, key, message)
                    set_stego_=str(set_stego +".png")
                    newimg.save(set_stego_, str(set_stego_.split(".")[-1].upper()))
                    end_time = time.time()
                    time_taken_to_encode = end_time - start_time
                    user_key.delete(0,END)
                    messagebox.showinfo("Success !!!","Message Successfully Encoded into Image...")
                    messagebox.showinfo("Time Taken !!!", "Encoding took =  " + str(time_taken_to_encode))
                    break
            else:
                if len(message.strip()) == 0 and len(key) == 4 and len(set_stego) != 0:
                    messagebox.showerror("*** Message Error !!! ***", "The Message Field is Empty")
                    messagebox.showerror("*** Overall ***", "All entries must be filled in the recommended format")
                    break
                elif len(message.strip()) != 0 and len(key) != 4 and len(set_stego) != 0:
                    messagebox.showerror("*** Key Error !!! ***", "Key length not recommended")
                    break
                elif len(set_stego) == 0:
                    messagebox.showerror("*** Stego Name Error !!! ***", "You haven't choosen a name for your stego image")
                    break
                elif len(key) == 4:
                    messagebox.showerror("*** Message Error !!! ***", "The Message Field is Empty")
                    break
                else:
                    messagebox.showerror("*** Key Error !!! ***", "Key length not recommended")
                    break
        
    #fourth Frame
    frame4=Frame(screen1,bd=3,bg="#07493d",width=600,height=100,relief=GROOVE)
    frame4.place(x=10,y=480)

    Button(frame4,text="Open Cover Image",width=20,bg="#097924",fg="black",bd=0,height=2,font="Times 14 bold",command=Open_Cover_Image).place(x=20,y=30)
    Button(frame4,text="Encode Text",width=20,bg="#4a0979",fg="black",bd=0,height=2,font="Times 14 bold",command=key_check).place(x=350,y=30)
    Label(frame4,text="The Open Cover Image and Encode Text Button",bg="#07493d",fg="yellow").place(x=20,y=5)

    Button(text="Back",height="2",width=23,bg="#020024",fg="white",bd=0,command=lambda: [screen1.destroy(),main()]).place(x=500,y=600)

    screen1.mainloop()
 
# Decode the data in the image
def decode():
    global message_1, time_taken_to_decode
    screen2=tk.Tk()
    screen2.title("DECRYPTION")
    screen2.geometry("720x630")
    screen2.resizable(False,False)
    screen2.configure(bg="#2f4155")
    Label(screen2,text="Decypher Text from Image(Image should have *.png file extension)",bg="#2f4155",fg="black",font="Times 17 italic bold").place(x=10,y=10)
     #icon
    image_icon=PhotoImage(file="icon.png")
    screen2.iconphoto(False,image_icon)
    

    #first frame
    frame1=Frame(screen2,bd=3,bg="#07493d",width=340,height=280,relief=GROOVE)
    frame1.place(x=10,y=150)
    lbl=Label(screen2,bg="#07493d")
    lbl.place(x=10,y=150)
    #third frame
    frame3=Frame(screen2,bd=3,bg="#2d6722",width=600,height=100,relief=GROOVE)
    frame3.place(x=10,y=100)
    
    Label(screen2,text="NOTE: KEY LENGTH SHOULD BE EXACTLY FOUR CHARACTERS",bg="#2f4155",fg="black",font="Times 16 italic bold").place(x=10,y=60)
    key_label = Label(frame3, text="Enter your four character secret key to confirm: ", bg="#2f4155", font="Times 14 italic bold")
    key_label.grid(row=1, column=0)
    key_entry = tk.Entry(frame3,show="*",font="Times 14 italic bold")
    key_entry.grid(row=1, column=1)

    
    def decypher():
        global message_1, time_taken_to_decode
        filename = filedialog.askopenfilename(initialdir=os.getcwd(),
                                        title='Select Cover Image (*.png)',
                                        filetype=(("PNG file","*.png"),("All file","*.png")))
        img=Image.open(filename)
        pil_image=img.copy()
        image=ImageTk.PhotoImage(img)
        
        key = key_entry.get()
        message_1 = ''
        imginfo = iter(pil_image.getdata())
        while (True):
            start_time=time.time()
            pixels = [value for value in imginfo.__next__()[:3] +
                                imginfo.__next__()[:3] +
                                imginfo.__next__()[:3]]
 
            # string of binary data
            binarymessage = ''
 
            for i in pixels[:8]:
                if (i % 2 == 0):
                    binarymessage += '0'
                else:
                    binarymessage += '1'
            
            message_1 += chr(int(binarymessage, 2))
            if (pixels[-1] % 2 != 0):
                if key == (message_1[:4]):
                    lbl.configure(image=image,width=340,height=280)
                    lbl.image=image
                    end_time=time.time()
                    time_taken_to_decode = end_time - start_time
                    messagebox.showinfo("Time Taken !!!", "Decoding took =  " + str(time_taken_to_decode))
                    text_output()
                elif len(key) != 4:
                    messagebox.showerror("*** Key Error !!! ***", "Invalid Key length")
                    messagebox.showerror("*** Overall ***", "All entries must be filled in the recommended format")
                else:
                    messagebox.showerror("*** Overall ***", " Invalid Key !!!!")
                    
                    break
                break
            
            
    #fourth Frame
    frame4=Frame(screen2,bd=3,bg="#07493d",width=300,height=100,relief=GROOVE)
    frame4.place(x=10,y=450)
    Button(frame4,text="Open Stego Image",width=20,bg="#097924",fg="black",bd=0,height=2,font="Times 14 bold",command=decypher).place(x=20,y=30)
    Label(frame4,text="The Stego Image Button",bg="#07493d",fg="yellow").place(x=20,y=5)

    Button(text="Back",height="2",width=23,bg="#020024",fg="white",bd=0,command=lambda: [screen2.destroy(),main()]).place(x=500,y=560)

    
    def text_output():
        screen3=tk.Tk()
        screen3.title("OUTPUT")
        screen3.geometry("500x500")
        screen3.resizable(False,False)
        screen3.configure(bg="#2f4155")
        Label(screen3,text=" Decoded Text Output:",bg="#2d6722",fg="black",font="Times 17 italic bold").place(x=10,y=10)
       
        frame1=Frame(screen3,bd=3,bg="#07493d",width=340,height=280,relief=GROOVE)
        frame1.place(x=10,y=0)
        message_label = tk.Text(frame1, font="Times 10 italic bold", bg="white", fg="black", width=64, height=23)
        message_label.grid(row=1, column=0)
        scrollbar = tk.Scrollbar(frame1, command=message_label.yview)
        message_label.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=1, column=1, sticky='ns')
        message_label.insert(END, message_1[4:])
        Button(screen3,text="Back",height="2",width=23,bg="#020024",fg="white",bd=0,command=lambda: [screen3.destroy(),screen2.destroy(),main()]).place(x=300,y=400)
        def exit():
            choice = messagebox.askyesno(None, 'Do you want to quite?')
            if choice == True:
                screen3.destroy()
                screen2.destroy()
        Button(screen3,text="Exit",height="2",width=23,bg="#1089ff",fg="white",bd=0,command=lambda:[exit()]).place(x=300,y=450)
        screen3.mainloop()
        
    screen2.mainloop()


        
# Main Function
def main():
    root=Tk()
    root.title(" *** WELCOME TO THE MUSK  *** ")
    root.geometry("800x200")
    root.resizable(False,False)
    root.configure(bg="#2f4155")

     #icon
    image_icon=PhotoImage(file="i2.png")
    root.iconphoto(False,image_icon)

    Label(text="YOUR PRIVACY IS OUR PRIORITY",fg="black",font=("Times 25 italic bold")).place(x=100,y=50)
    def exit():
        choice = messagebox.askyesno(None, 'Do you want to quite?')
        if choice == True:
            root.destroy()
    Button(text="ENCODE",height="2",width=23,bg="#ed3833",fg="black",bd=0,command=lambda: [root.destroy(),encode()]).place(x=10,y=120)
    Button(text="DECODE",height="2",width=23,bg="#00bd56",fg="white",bd=0,command=lambda: [root.destroy(),decode()]).place(x=200,y=120)
    Button(text="Exit",height="2",width=23,bg="#1089ff",fg="white",bd=0,command=lambda:[exit()]).place(x=600,y=120)

    root.mainloop()
main()
