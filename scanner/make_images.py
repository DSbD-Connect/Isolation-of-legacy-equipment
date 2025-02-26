#!/usr/bin/python3

import socket, sys, datetime, random
id_chars = '0123456789'

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server_address = ('0.0.0.0', 5533)
sock.bind(server_address)

while True:
    data, address = sock.recvfrom(4096)
    
    if data == b'SCAN\n':
        fh = open('image_template','r')
        text = fh.read()
        fh.close()

        now = datetime.datetime.now()
        datestr = now.strftime("%d/%m/%Y %H:%M:%S")
        fname_datestr = now.strftime("%d-%m-%Y--%H-%M-%S")
        pid_chars = [random.choice(id_chars) for _ in range(0,8)]
        pid = ''.join(pid_chars)
        rb_x = random.randint(200,500)
        rb_y = random.randint(200,500)

        text = text.replace('@@PID@@',pid)
        text = text.replace('@@DATE@@',datestr)
        text = text.replace('@@RB_X@@',str(rb_x))
        text = text.replace('@@RB_Y@@',str(rb_y))

        fname = '../image-share/scan_'+pid+'_'+fname_datestr+'.svg'
        fh = open(fname,'w')
        fh.write(text)
        fh.close()
