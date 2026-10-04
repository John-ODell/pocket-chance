# Workout for Waveshare 1.3" IPS LCD Display Module for Raspberry Pi Pico (240x240)
#     Tony Goodhew 19th Aug 2021
# Menu driven program using built-in joystick and buttons for control
from machine import Pin,SPI,PWM
import sys
import framebuf
import utime
import os
import math
import random
from time import sleep
# ============ Start of Drive Code ================
#  == Copy and paste into your code ==
BL = 13  # Pins used for display screen
DC = 8
RST = 12
MOSI = 11
SCK = 10
CS = 9

class LCD_1inch3(framebuf.FrameBuffer):
    def __init__(self):
        self.width = 240
        self.height = 240
        
        self.cs = Pin(CS,Pin.OUT)
        self.rst = Pin(RST,Pin.OUT)
        
        self.cs(1)
        self.spi = SPI(1)
        self.spi = SPI(1,1000_000)
        self.spi = SPI(1,100000_000,polarity=0, phase=0,sck=Pin(SCK),mosi=Pin(MOSI),miso=None)
        self.dc = Pin(DC,Pin.OUT)
        self.dc(1)
        self.buffer = bytearray(self.height * self.width * 2)
        super().__init__(self.buffer, self.width, self.height, framebuf.RGB565)
        self.init_display()
        
        self.red   =   0x07E0 # Pre-defined colours
        self.green =   0x001f # Probably easier to use colour(r,g,b) defined below
        self.blue  =   0xf800
        self.white =   0xffff
        
    def write_cmd(self, cmd):
        self.cs(1)
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)  

    def write_data(self, buf):
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(bytearray([buf]))
        self.cs(1)

    def init_display(self):
        """Initialize display"""  
        self.rst(1)
        self.rst(0)
        self.rst(1)
        
        self.write_cmd(0x36)
        self.write_data(0x70)

        self.write_cmd(0x3A) 
        self.write_data(0x05)

        self.write_cmd(0xB2)
        self.write_data(0x0C)
        self.write_data(0x0C)
        self.write_data(0x00)
        self.write_data(0x33)
        self.write_data(0x33)

        self.write_cmd(0xB7)
        self.write_data(0x35) 

        self.write_cmd(0xBB)
        self.write_data(0x19)

        self.write_cmd(0xC0)
        self.write_data(0x2C)

        self.write_cmd(0xC2)
        self.write_data(0x01)

        self.write_cmd(0xC3)
        self.write_data(0x12)   

        self.write_cmd(0xC4)
        self.write_data(0x20)

        self.write_cmd(0xC6)
        self.write_data(0x0F) 

        self.write_cmd(0xD0)
        self.write_data(0xA4)
        self.write_data(0xA1)

        self.write_cmd(0xE0)
        self.write_data(0xD0)
        self.write_data(0x04)
        self.write_data(0x0D)
        self.write_data(0x11)
        self.write_data(0x13)
        self.write_data(0x2B)
        self.write_data(0x3F)
        self.write_data(0x54)
        self.write_data(0x4C)
        self.write_data(0x18)
        self.write_data(0x0D)
        self.write_data(0x0B)
        self.write_data(0x1F)
        self.write_data(0x23)

        self.write_cmd(0xE1)
        self.write_data(0xD0)
        self.write_data(0x04)
        self.write_data(0x0C)
        self.write_data(0x11)
        self.write_data(0x13)
        self.write_data(0x2C)
        self.write_data(0x3F)
        self.write_data(0x44)
        self.write_data(0x51)
        self.write_data(0x2F)
        self.write_data(0x1F)
        self.write_data(0x1F)
        self.write_data(0x20)
        self.write_data(0x23)
        
        self.write_cmd(0x21)

        self.write_cmd(0x11)

        self.write_cmd(0x29)

    def show(self):
        self.write_cmd(0x2A)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0xef)
        
        self.write_cmd(0x2B)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0xEF)
        
        self.write_cmd(0x2C)
        
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(self.buffer)
        self.cs(1)
        
# ========= End of Screen Driver ===========

def colour(R,G,B): # Convert 3 byte colours to 2 byte colours, RGB565
# Get RED value
    rp = int(R*31/255) # range 0 to 31
    if rp < 0: rp = 0
    r = rp *8
# Get Green value - more complicated!
    gp = int(G*63/255) # range 0 - 63
    if gp < 0: gp = 0
    g = 0
    if gp & 1:  g = g + 8192
    if gp & 2:  g = g + 16384
    if gp & 4:  g = g + 32768
    if gp & 8:  g = g + 1
    if gp & 16: g = g + 2
    if gp & 32: g = g + 4
# Get BLUE value       
    bp =int(B*31/255) # range 0 - 31
    if bp < 0: bp = 0
    b = bp *256
    colour = r+g+b
    return colour

# 7-seg character definations and routines
nums =[1,1,1,1,1,1,0,  # 0 # One row per digit 
       0,1,1,0,0,0,0,  # 1
       1,1,0,1,1,0,1,  # 2
       1,1,1,1,0,0,1,  # 3
       0,1,1,0,0,1,1,  # 4
       1,0,1,1,0,1,1,  # 5
       1,0,1,1,1,1,1,  # 6
       1,1,1,0,0,0,0,  # 7
       1,1,1,1,1,1,1,  # 8
       1,1,1,0,0,1,1,  # 9
       1,1,1,1,1,0,1,  # a = 10 - HEX characters
       0,0,1,1,1,1,1,  # b = 11
       0,0,0,1,1,0,1,  # c = 12
       0,1,1,1,1,0,1,  # d = 13
       1,1,0,1,1,1,1,  # e = 14
       1,0,0,0,1,1,1,  # f = 15
       1,1,1,1,0,1,1,  # g needed for seg!
       0,0,0,0,0,0,1,  # -
       0,0,0,0,0,0,0]  # Blank

# ========= End of 7-seg section ==========
'''
Adjustable font for the WaveShare 1.3" IPS LCD Display Module for Raspberry Pi Pico (240x240)
                         Tony Goodhew 17th Aug 2021
           Modified from code by Les Wright 2021 V 1.1 for Pimoroni Pico Display                  
              https://forums.pimoroni.com/t/pico-display-and-fonts/16194/18
'''
#ASCII Character Set
cmap = ['00000000000000000000000000000000000', #Space
        '00100001000010000100001000000000100', #!
        '01010010100000000000000000000000000', #"
        '01010010101101100000110110101001010', ##
        '00100011111000001110000011111000100', #$
        '11001110010001000100010001001110011', #%
        '01000101001010001000101011001001101', #&
        '10000100001000000000000000000000000', #'
        '00100010001000010000100000100000100', #(
        '00100000100000100001000010001000100', #)
        '00000001001010101110101010010000000', #*
        '00000001000010011111001000010000000', #+
        '000000000000000000000000000000110000100010000', #,
        '00000000000000011111000000000000000', #-
        '00000000000000000000000001100011000', #.
        '00001000010001000100010001000010000', #/
        '01110100011000110101100011000101110', #0
        '00100011000010000100001000010001110', #1
        '01110100010000101110100001000011111', #2
        '01110100010000101110000011000101110', #3
        '00010001100101011111000100001000010', #4
        '11111100001111000001000011000101110', #5
        '01110100001000011110100011000101110', #6
        '11111000010001000100010001000010000', #7
        '01110100011000101110100011000101110', #8
        '01110100011000101111000010000101110', #9
        '00000011000110000000011000110000000', #:
        '01100011000000001100011000010001000', #;
        '00010001000100010000010000010000010', #<
        '00000000001111100000111110000000000', #=
        '01000001000001000001000100010001000', #>
        '01100100100001000100001000000000100', #?
        '01110100010000101101101011010101110', #@
        '00100010101000110001111111000110001', #A
        '11110010010100111110010010100111110', #B
        '01110100011000010000100001000101110', #C
        '11110010010100101001010010100111110', #D
        '11111100001000011100100001000011111', #E
        '11111100001000011100100001000010000', #F
        '01110100011000010111100011000101110', #G
        '10001100011000111111100011000110001', #H
        '01110001000010000100001000010001110', #I
        '00111000100001000010000101001001100', #J
        '10001100101010011000101001001010001', #K
        '10000100001000010000100001000011111', #L
        '10001110111010110101100011000110001', #M
        '10001110011010110011100011000110001', #N
        '01110100011000110001100011000101110', #O
        '11110100011000111110100001000010000', #P
        '01110100011000110001101011001001101', #Q
        '11110100011000111110101001001010001', #R
        '01110100011000001110000011000101110', #S
        '11111001000010000100001000010000100', #T
        '10001100011000110001100011000101110', #U
        '10001100011000101010010100010000100', #V
        '10001100011000110101101011101110001', #W
        '10001100010101000100010101000110001', #X
        '10001100010101000100001000010000100', #Y
        '11111000010001000100010001000011111', #Z
        '01110010000100001000010000100001110', #[
        '10000100000100000100000100000100001', #\
        '00111000010000100001000010000100111', #]
        '00100010101000100000000000000000000', #^
        '00000000000000000000000000000011111', #_
        '11000110001000001000000000000000000', #`
        '00000000000111000001011111000101110', #a
        '10000100001011011001100011100110110', #b
        '00000000000011101000010000100000111', #c
        '00001000010110110011100011001101101', #d
        '00000000000111010001111111000001110', #e
        '00110010010100011110010000100001000', #f
        '000000000001110100011000110001011110000101110', #g
        '10000100001011011001100011000110001', #h
        '00100000000110000100001000010001110', #i
        '0001000000001100001000010000101001001100', #j
        '10000100001001010100110001010010010', #k
        '01100001000010000100001000010001110', #l
        '00000000001101010101101011010110101', #m
        '00000000001011011001100011000110001', #n
        '00000000000111010001100011000101110', #o
        '000000000001110100011000110001111101000010000', #p
        '000000000001110100011000110001011110000100001', #q
        '00000000001011011001100001000010000', #r
        '00000000000111110000011100000111110', #s
        '00100001000111100100001000010000111', #t
        '00000000001000110001100011001101101', #u
        '00000000001000110001100010101000100', #v
        '00000000001000110001101011010101010', #w
        '00000000001000101010001000101010001', #x
        '000000000010001100011000110001011110000101110', #y
        '00000000001111100010001000100011111', #z
        '00010001000010001000001000010000010', #{
        '00100001000010000000001000010000100', #|
        '01000001000010000010001000010001000', #}
        '01000101010001000000000000000000000' #}~
]

def printchar(letter,xpos,ypos,size,charupdate,c):
    origin = xpos
    charval = ord(letter)
    #print(charval)
    index = charval-32 #start code, 32 or space
    #print(index)
    character = cmap[index] #this is our char...
    rows = [character[i:i+5] for i in range(0,len(character),5)]
    #print(rows)
    for row in rows:
        #print(row)
        for bit in row:
            #print(bit)
            if bit == '1':
                LCD.pixel(xpos,ypos,c)
                if size==2:
                    LCD.pixel(xpos,ypos+1,c)
                    LCD.pixel(xpos+1,ypos,c)
                    LCD.pixel(xpos+1,ypos+1,c)
                if size == 3:
                    LCD.pixel(xpos,ypos,c)
                    LCD.pixel(xpos,ypos+1,c)
                    LCD.pixel(xpos,ypos+2,c)
                    LCD.pixel(xpos+1,ypos,c)
                    LCD.pixel(xpos+1,ypos+1,c)
                    LCD.pixel(xpos+1,ypos+2,c)
                    LCD.pixel(xpos+2,ypos,c)
                    LCD.pixel(xpos+2,ypos+1,c)
                    LCD.pixel(xpos+2,ypos+2,c)
            xpos+=size
        xpos=origin
        ypos+=size
    if charupdate == True:
        LCD.show()
        
    
def delchar(xpos,ypos,size,delupdate):
    if size == 1:
        charwidth = 5
        charheight = 9
    if size == 2:
        charwidth = 10
        charheight = 18
    if size == 3:
        charwidth = 15
        charheight = 27
    c =colour(0,0,0) # Colour of background
    LCD.fill_rect(xpos,ypos,charwidth,charheight,c) #xywh
    if delupdate == True:
        LCD.show()

def printstring(string,xpos,ypos,size,charupdate,strupdate,c):   
    if size == 1:
        spacing = 8
    if size == 2:
        spacing = 14
    if size == 3:
        spacing = 18
    for i in string:
        printchar(i,xpos,ypos,size,charupdate,c)
        xpos+=spacing
    if strupdate == True:
        LCD.show()
# =============End of Characters section ===============

# == Project specific routines ==============
def draw_rect(x, y,):
    LCD.rect(x,y,40,60, colour(210,100,120))
def draw_circle(x,y,radius,color):
    for i in range(x - radius, x + radius):
        for j in range(y - radius, y + radius):
            if (i-x)**2+(j - y)**2<= radius**2:
                LCD.pixel(i,j,color)
def draw_triangle(x1,y1,x2, y2, x3, y3, color):
    draw_line(x1,y1,x2,y2, color)
    draw_line(x2,y2,x3,y3, color)
    draw_line(x3,y3,x1,y1, color)
def print_status_message(prev_points, current_points):
    if current_points > prev_points:
        printstring("Winner",30,100,3,0,0,colour(180,120,220))
    elif current_points < prev_points:
        prinstring("Loser!",30,100,3,0,0,colour(220,180,120))
def slots():
    LCD.fill(0)
    points = 10
    #printstring("risk",100,100,2,0,0,colour(245,245,99))
    printstring("Points:{}".format(points),10,60,2,0,0,colour(200,200,180))
    rect_coordinates = [(0,100),(65,100),(130,100)]
    LCD.show()
    ctrl = Pin(3,Pin.IN,Pin.PULL_UP)
    while True:
        printstring("SLOTS 2x Wager 1",10,20,2,0,0,colour(240,100,100))
        printstring("10x JACKPOT Y",10,40,2,0,0,colour(240,120,200))
        printstring("3",220,80,2,0,0,colour(180,230,180))
        printstring("5",220,140,2,0,0,colour(120,240,180))
        printstring("10x",200,220,2,0,0,colour(200,240,180))
        printstring("Menu Ctrl+Y ",0,210,2,0,0,colour(240,120,200))
        keyX_state = keyX.value()
        keyY_state = keyY.value()
        keyA_state = keyA.value()
        keyB_state = keyB.value()
        ctrl_state = ctrl.value()
        prev_points = points
        if keyA_state == 0:
            choice = random.choice([1,2,3,4])
            if choice + choice <=4:
                points += 2
            else:
                points -= 1
            for (x,y) in rect_coordinates:
                cr = random.randint(0x000, 0xFFFF)
                clr = random.randint(0x000, 0xFFFF)
                LCD.rect(x,y,60,100,cr)
                LCD.rect(x+1,y+2,60,100,cr)
                draw_circle(x+30,y+40,25,clr)
                LCD.show()
                utime.sleep(.4)
            for (x,y) in rect_coordinates:
                draw_rect(x+5,y+5)
                draw_rect(x+10,y+10)
                LCD.show()
                utime.sleep(.4)
            if points>prev_points:
                 printstring("Winner!",20,100,3,0,0,colour(255,255,255))
                 LCD.show()
                 utime.sleep(.8)
            elif points < prev_points:
                 printstring("Loser!",20,100,3,0,0,colour(255,255,255))
                 LCD.show()
                 utime.sleep(.8)                
        elif keyB_state == 0:
            choice = random.choice([1,2,3,4])
            if sum([choice, choice, choice])<=10:
                points += 6
            else:
                points -= 3
            for (x,y) in rect_coordinates:
                cr = random.randint(0x000, 0xFFFF)
                clr = random.randint(0x000, 0xFFFF)
                LCD.rect(x,y,60,100,cr)
                draw_circle(x+30,y+40,25,clr)
                LCD.show()
                utime.sleep(.4)
            for (x,y) in rect_coordinates:
                draw_rect(x+10,y+10)
                LCD.show()
                utime.sleep(.4)
            if points>prev_points:
                 printstring("Winner!",20,100,3,0,0,colour(255,255,255))
                 LCD.show()
                 utime.sleep(.8)
            elif points < prev_points:
                 printstring("Loser!",20,100,3,0,0,colour(255,255,255))
                 LCD.show()
                 utime.sleep(.8)               
        elif keyX_state== 0:
            choice = random.choice([1,2,3,4])
            if sum([choice, choice, choice, choice])<=6:
                points += 10
            else:
                points -= 5
            for (x,y) in rect_coordinates:
                cr = random.randint(0x000, 0xFFFF)
                clr = random.randint(0x000, 0xFFFF)
                LCD.rect(x,y,60,100,cr)
                draw_circle(x+30,y+40,25,clr)
                LCD.show()
                utime.sleep(.4)
            for (x,y) in rect_coordinates:
                draw_rect(x+10,y+10)
                LCD.show()
                utime.sleep(.4)
            if points>prev_points:
                 printstring("Winner!",20,100,3,0,0,colour(255,255,255))
                 LCD.show()
                 utime.sleep(.8)
            elif points < prev_points:
                 printstring("Loser!",20,100,3,0,0,colour(255,255,255))
                 LCD.show()
                 utime.sleep(.8)               
        elif keyY_state== 0:
            choice = random.choice([1,2,3,4])
            if sum([choice, choice, choice]) == 5:
                points *=10
            else:
                points = 0
            for (x,y) in rect_coordinates:
                cr = random.randint(0x000, 0xFFFF)
                clr = random.randint(0x000, 0xFFFF)
                LCD.rect(x,y,60,100,cr)
                draw_circle(x+30,y+40,25,clr)
                LCD.show()
                utime.sleep(.4)
            for (x,y) in rect_coordinates:
                draw_rect(x+10,y+10)
                LCD.show()
                utime.sleep(.4)
            if points>prev_points:
                 printstring("JACKPOT!",20,100,3,0,0,colour(255,255,255))
                 LCD.show()
                 utime.sleep(1.5)
            elif points < prev_points:
                 printstring("BUST,GO HOME!",1,100,3,0,0,colour(255,255,255))
                 LCD.show()
                 utime.sleep(1.5)
            #printstring("Points:{}".format(points), 20, 20, 2, 0, 0, colour(235,59,173))
        printstring("Points:{}".format(points),10,60,2,0,0,colour(200,200,180))
        LCD.show()
        LCD.fill(0)
        if ctrl_state == 0 and keyY_state == 0:
            break
            

def shuffle(deck):
    for i in range(len(deck)-1, 0, -1):
        j = random.randrange(i + 1)  # Get random index
        deck[i], deck[j] = deck[j], deck[i]  # Swap

def poker():
    deck = [str(i) for i in range(2, 11)] + list('JQKA')
    suits = ['H','D','C','S']
    deck = [str(number) + ' ' + suit for suit in suits for number in deck]
    game_start = True
    while game_start:
        LCD.fill(0)
        printstring("Welcome to poker", 0, 20, 2, 0, 0, colour(235,59,173))
        LCD.show()
        shuffle(deck)
        player_hand = [deck.pop(), deck.pop()]
        dealer_hand = [deck.pop(), deck.pop()]
        table_hand = [deck.pop(),deck.pop(),deck.pop(),deck.pop(),deck.pop()]
        printstring("Press A to bet", 0, 60, 2, 0, 0, colour(59,255,117))
        printstring("Press Y to Fold", 0, 180, 2, 0, 0, colour(59,255,117))
        LCD.show()
        while True:
            LCD.fill(0)
            if keyA.value() == 0:  # If keyA is pressed
                LCD.rect(0, 90, 240, 40, colour(55,233,112,))
                table_hand_subset = table_hand[:3]
                printstring("Hand " + ','.join(player_hand), 0, 60, 2, 0, 0, colour(155,155,255))
                printstring("" + ', '.join(map(str,table_hand_subset)), 70, 100, 1, 0, 0, colour(255,255,255))# Show the first 3 table cards
                printstring("Press B to bet", 0, 190, 2, 0, 0, colour(59,255,117))
                printstring("Press Y to Menu", 0, 220, 2, 0, 0, colour(59,255,117))
                LCD.show()
            elif keyB.value() == 0:  # If keyB is pressed, show the next card
                table_hand_subset.append(table_hand[3])
                printstring("" + ', '.join(map(str,table_hand_subset)), 20, 100, 1, 0, 0, colour(255,255,255))
                printstring("Hand " + ','.join(player_hand), 0, 60, 2, 0, 0, colour(155,155,255))
                printstring("Press X to bet", 0, 190, 2, 0, 0, colour(59,255,117))
                printstring("Press Y to Menu", 0, 220, 2, 0, 0, colour(59,255,117))
                LCD.rect(0, 90, 240, 40, colour(55,233,112,))
                LCD.show()
                utime.sleep(2)
                
            elif keyX.value() == 0:  # If keyX is pressed, show the final card
                table_hand_subset.append(table_hand[4])
                LCD.rect(0, 90, 240, 40, colour(55,233,112,))
                printstring("" + ','.join(map(str,table_hand_subset)), 10, 100, 1, 0, 0, colour(255,255,255))
                printstring("Hand: " + ','.join(player_hand), 0, 60, 2, 0, 0, colour(155,155,255))
                printstring("Dealer: " + ','.join(dealer_hand), 0, 180, 2, 0, 0, colour(252,92,92))
                LCD.rect(0, 90, 240, 40, colour(55,233,112,))# Show the dealer's hand
                LCD.show()
                utime.sleep(1.5)
                printstring("Play Again? hit A", 0, 20, 2, 0, 0, colour(46,240,82))
                printstring("To Menu hit Y", 0, 220, 2, 0, 0, colour(46,240,82))
                LCD.show()
                

            elif keyY.value() == 0:  # If keyY is pressed, end the game
                game_start = False
                menu_active = True
                LCD.fill(0)
                LCD.show()
                break
def printataus(prev_points, current_points):
    if current_points > prev_points:
        printstring("Winner", 30, 100, 3, True, True, colour(180, 120, 220))
    elif current_points < prev_points:
        printstring("Loser!", 30, 100, 3, True, True, colour(220, 180, 120))

def high_low():
    game_start = True
    points = 10
    prev_points = points
    LCD.fill(0)
    printstring("Welcome to HiLow", 0, 20, 2, 0, 0, colour(235,59,173))
    printstring("51 is Jackpot!", 0, 40, 2, 0, 0, colour(235,59,173))
    printstring("A for menu", 0, 60, 2, 0, 0, colour(235,59,173))
    printstring("Bet Low+2", 80, 190, 3, 0, 0, colour(255,150,0))
    printstring("Bet High+2", 80, 140, 3, 0, 0, colour(255,150,0))
    printstring("Bet Mid+5", 80, 110, 3, 0, 0, colour(255,150,0))
    LCD.show()  
    while game_start:
        LCD.fill(0)
        printstring("points{}".format(points), 10, 200, 2, 0, 0, colour(255,255,255))
        keyX_state = keyX.value()
        keyY_state = keyY.value()
        keyA_state = keyA.value()
        keyB_state = keyB.value()
        
        if keyX_state == 0:
            #print("High")
            player_choice = random.randint(1,100)
            if player_choice >= 50:  # If keyX is pressed
                result = "High"
                points += 2
            else:
                result = "High"
                points -= 1
            printstring("Your Bet: " + result, 0, 80, 3, 0, 0, colour(59,255,117))
            LCD.show()
            utime.sleep(.5)
        
        elif keyY_state == 0:
            player_choice = random.randint(1,100)
            if player_choice <= 49:
                result = "Low"
                points += 2
            else:
                result = "Low"
                points -= 1   
            printstring("Bet: " + result, 0, 80, 3, 0, 0, colour(240,145,46))
            utime.sleep(.5)
            LCD.show()
        
        elif keyB_state == 0:
            player_choice = random.randint(1,100)
            if 35 <= player_choice <= 79:
                result = "Middle"
                points += 5
            else:
                result = "Middle"
                points -= 2   
            printstring("Bet: " + result, 0, 80, 3, 0, 0, colour(240,145,46))
            LCD.show()
            utime.sleep(.5)
            LCD.show()
        if keyX_state == 0 or keyY_state == 0 or keyB_state == 0:
            utime.sleep(0.1)
            dealer_draw = random.randint(1,100)  # Dealer draws a card
            if dealer_draw == 51:
                result = "JACKPOT"
                points *= 51
            else:
                result = str(dealer_draw)
                points -= 5
            printstring("Dealer: " + result, 0, 140, 3, 0, 0, colour(67,89,250))
            LCD.show()
            utime.sleep(2)
            LCD.fill(0)
            
            printataus(prev_points, points)
            prev_points = points
            printstring("points{}".format(points), 10, 200, 3, 0, 0, colour(255,255,255))
            printstring("Menu-->", 110, 20, 3, 0, 0, colour(46,240,82))
            printstring("Try Again?", 0, 40, 3, 0, 0, colour(46,240,82))
            LCD.show()
            utime.sleep(2)
        if keyA_state == 0:
            LCD.fill(0)
            LCD.show()
            game_start = False



        
def rps_game():
    LCD.fill(0)
    game_start = True
    while True:
        LCD.fill(0)
        keyA_state = keyA.value()
        keyB_state = keyB.value()
        keyX_state = keyX.value()
        printstring("Welcome To", 20, 25, 3, 0, 0, colour(244,2233,125,))
        printstring("Rock,Paper,Scissors", 0, 70, 2, 0, 0, colour(70,200,255,))
        printstring("Hit A to Play!", 0, 100, 3, 0, 0, colour(255,20,127,))
        printstring("Hit X for Menu", 0, 150, 3, 0, 0, colour(102,40,204))
        LCD.show()
        if keyA_state == 0:   # If keyA is pressed and the game hasn't started
            LCD.fill(0)
            printstring("Rock,Paper,Scissors", 0, 20, 2, 0, 0, colour(70,200,255,))
            utime.sleep(1)
            LCD.show()
            printstring("Ready", 0, 50, 3, 0, 0, colour(255,255,255,))
            utime.sleep(1)
            LCD.show()
            printstring("Set", 90, 90, 3, 0, 0, colour(255,255,255,))
            utime.sleep(1)
            LCD.show()
            printstring("Shoot", 130, 130, 3, 0, 0, colour(255,255,255,))
            utime.sleep(1)
            LCD.show()
            game = random.choice(['Rock', 'Paper', 'Scissors'])
            printstring(game, 50, 200, 3, 0, 0, colour(100,150,255,))
            LCD.show()
            utime.sleep(3)
            #LCD.fill(0)
            LCD.show()

        elif keyB_state == 0:  # If keyB is pressed and the game has started
            game_start = True  # Set game_start to False to restart the game

        elif keyX_state == 0:  # If keyX is pressed
            LCD.fill(0)
            LCD.show()
            break  # Exit the game


def coin_flip():
    coins_flipped = True
    while coins_flipped:
        LCD.fill(0)
        printstring("Press A to Flip ->", 0, 20, 2, 0, 0, colour(50,200,255))
        printstring("Press B for Menu", 0, 40, 2, 0, 0, colour(50,200,255))
        printstring("!Welcome to!", 0, 80, 3, 0, 0, colour(255,120,56))
        printstring("Heads V Tails", 0, 110, 3, 0, 0, colour(255,50,255))
        printstring("d|*c*|b", 60, 150, 3, 0, 0, colour(56,120,255))
        printstring("(o.o)[=]~~~", 10, 190, 3, 0, 0, colour(46,255,155))
        LCD.show()
        while True:
            keyA_state = keyA.value()# Start a loop that continues until the program is stopped
            keyB_state = keyB.value()# Read the state of keyA
            if keyA_state == 0 or keyB_state == 0:
                break
        if keyA_state == 0:# If keyA is pressed
            LCD.fill(0)  # Clear the LCD screen
            flip = random.randint(1,2)  # Flip the coin
            if flip == 1:
                result = "Heads"
            else:
                result = "Tails"
            printstring(result, 80, 120, 3, 0, 0, c)
            #LCD.show()
            cc = random.randint(0x000, 0xFFFF)
            cx, cy = LCD.width//2, LCD.height//2
            for r in range (120, 0, -5):
                for angle in range (91):
                    x3 = int(r*math.sin(math.radians(angle)))
                    y3 = int(r*math.cos(math.radians(angle)))
                    LCD.pixel(cx-x3, cy+y3, cc)
                    LCD.pixel(cx-x3, cy-y3, cc)
                    LCD.pixel(cx+x3, cy+y3, cc)
                    LCD.pixel(cx+x3, cy-y3, cc)
            LCD.show()
            utime.sleep(1)
        elif keyB_state == 0:
            coins_flipped = False
            #break
        LCD.fill(0)
        LCD.show()

def draw_random_circles():
        dice_roll = True
        throw = None
        dice = None
        while dice_roll:
            LCD.fill(0)
            printstring("1.Load your Dice", 0, 25, 2, 0, 0, colour(30,128,255))
            printstring("2.Hit Y to Shoot", 0, 180, 2, 0, 0, colour(30,128,255))
            printstring("classic 6 Press A", 0, 50, 2, 0, 0, colour(188,255,20))
            printstring("12 faces Press B", 12, 90, 2, 0, 0, colour(133,245,70))
            printstring("D-20 Press X", 70, 140, 2, 0, 0, colour(160,245,160))
            LCD.show()
            if keyA.value() == 0:
                throw = random.randint(1, 6)
                dice = "6 face"
            elif keyB.value()==0:
                throw = random.randint(1,12)
                dice = "12 face"
            elif keyX.value()==0:
                throw = random.randint(1, 20)
                dice = "D-20"
            elif keyY.value()==0:
                break
            else:
                continue
            LCD.show()
        def draw_pixels(x, y, width, height, num_pixels, color):
            LCD.fill(0)
            pixel_positions = [(random.randint(x, x+width-1), random.randint(y, y+height-1)) for _ in range(num_pixels)]
            for pos in pixel_positions:
                LCD.pixel(pos[0], pos[1], color)
        draw_pixels(2, 2, 238, 238, 150, colour(255,128,0))
        draw_pixels(1, 1, 239, 239, 150, colour(130,42,245))
        draw_pixels(0, 0, 240, 240, 150, colour(102,178,255))    
        printstring("{} ({})".format(throw, dice), 20, 80, 3, 0, 0, colour(230,100,200))
        LCD.show()
        utime.sleep(2.5)
        LCD.fill(0)
        LCD.show()
    

    
def ring(cx,cy,r,cc):  
    for angle in range(91):
        y3=int(r*math.sin(math.radians(angle)))
        x3=int(r*math.cos(math.radians(angle)))
        LCD.pixel(cx-x3,cy+y3,cc)
        LCD.pixel(cx-x3,cy-y3,cc)
        LCD.pixel(cx+x3,cy+y3,cc)
        LCD.pixel(cx+x3,cy-y3,cc)
# =============== Main ==============================
pwm = PWM(Pin(BL)) # Screen Brightness
pwm.freq(1000)
pwm.duty_u16(32768) # max 65535 - mid value

# Define pins for buttons and Joystick
keyA = Pin(15,Pin.IN,Pin.PULL_UP) # Normally 1 but 0 if pressed
keyB = Pin(17,Pin.IN,Pin.PULL_UP)
keyX = Pin(19,Pin.IN,Pin.PULL_UP)
keyY= Pin(21,Pin.IN,Pin.PULL_UP)

up = Pin(2,Pin.IN,Pin.PULL_UP)
down = Pin(18,Pin.IN,Pin.PULL_UP)
left = Pin(16,Pin.IN,Pin.PULL_UP)
right = Pin(20,Pin.IN,Pin.PULL_UP)
ctrl = Pin(3,Pin.IN,Pin.PULL_UP)

LCD = LCD_1inch3() # Initialise the display
# Background colour 
LCD.fill(colour(0,0,0)) # BLACK
LCD.show()

# ======= Menu ==============  
m = 0
yellow = colour(255,255,0)
blue = colour(0,0,255)
running = True
while running:
    menu_active=True
    c = colour(255,0,0) 
    printstring("J'Boy-V3.1.2",17,10,3,0,0,c)
    printstring("Pocket Chance", 5, 45, 3, 0, 0, c)
    c = yellow
    if m == 0:
        c = blue
    printstring("Slots",35,80,2,0,0,c)
    c = yellow
    if m == 1:
        c = blue
    printstring("Coin Toss",35,100,2,0,0,c)
    c = yellow
    if m == 2:
        c = blue
    printstring("High/Low",35,120,2,0,0,c)
    c = yellow
    if m == 3:
        c = blue
    printstring("Poker",35, 140,2,0,0,c)
    c = yellow
    if m == 4:
        c = blue
    printstring("R/P/S",35,163,2,0,0,c)
    c = yellow
    if m == 5:
        c = blue
    printstring("Dice",35,185,2,0,0,c)
    c = yellow
    if m == 6:
        c == blue
    printstring("Off", 35, 210, 2,0,0,c)
    c = yellow
    LCD.show()
    
    # Check joystick UP/DOWN/CTRL
    if(up.value() == 0):
        m = m - 1
        if m < 0:
            m = 0
            
    elif(down.value() == 0):
        m = m + 1
        if m > 6:
            m = 6
                       
    elif(ctrl.value() == 0):
        if(m == 0): # Exit loop and HALT program
            slots()
        if(m == 1):
            coin_flip()
        if(m == 2):
            high_low()# Dynamic part in procedure
        if(m == 3):
            poker()
        if(m == 4):
            rps_game()
        if(m == 5):
            draw_random_circles()
        if(m == 6):
            break
        continue
                        
LCD.fill(0)
for r in range(10):
    ring(120,120,60+r,colour(255,255,0))

c = colour(255,0,0)
printstring("Halted",80,110,2,0,0,c)
LCD.show()
# Tidy up
utime.sleep(3)
LCD.fill(0)
#LCD.show()`