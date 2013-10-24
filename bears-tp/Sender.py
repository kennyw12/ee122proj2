import sys
import getopt

import Checksum
import BasicSender

'''
This is a skeleton sender class. Create a fantastic transport protocol here.
'''
class Sender(BasicSender.BasicSender):
    def __init__(self, dest, port, filename, debug=False):
        super(Sender, self).__init__(dest, port, filename, debug)
        self.sent = {}
        self.inflight = set()
        self.ack = set()

    # Main sending loop.
    def start(self):
        seqno = 0
        wnd = 5
        msg = self.infile.read(500)
        msg_type = None
        dupackCount = 0
        end_msg = False
        last_sent = 0
        last_ack = 0
        for i in range(wnd):
            next_msg = self.infile.read(500)

            msg_type = 'data'
            if seqno == 0:
                msg_type = 'start'
            elif next_msg == "":
                msg_type = 'end'
                end_msg = True

            packet = self.make_packet(msg_type,seqno,msg)
            self.sent[seqno] = packet
            self.inflight.add(seqno)
            self.send(packet)
            last_sent = seqno
            print "sent: %s" % msg_type + str(seqno)
            msg = next_msg
            seqno += 1
        while last_sent != last_ack:
            checked = False
            response = None
            while not checked:
                response = self.receive(0.5)
                if response == None:
                    self.handle_timeout()
                else:
                    checked = Checksum.validate_checksum(response)
                    if checked:
                        print "recv: %s" % response
                    else:
                        print "recv: %s <--- CHECKSUM FAILED" % response
            ackno = int(self.split_packet(response)[1])
            if ackno in self.ack:
                dupackCount += 1
                if dupackCount == 3:
                    self.send(self.sent[ackno])
                    dupackCount = 0
            else:
                dupackCount = 0
                self.inflight.remove(ackno - 1)
                last_ack = ackno - 1
                self.ack.add(ackno)
                if not end_msg:
                    next_msg = self.infile.read(500)

                    msg_type = 'data'
                    if seqno == 0:
                        msg_type = 'start'
                    elif next_msg == "":
                        msg_type = 'end'
                        end_msg = True

                    packet = self.make_packet(msg_type,seqno,msg)
                    self.sent[seqno] = packet
                    self.inflight.add(seqno)
                    self.send(packet)
                    last_sent = seqno
                    print "sent: %s" % msg_type + str(seqno)
                    msg = next_msg
                    seqno += 1

        self.infile.close()

    def handle_timeout(self):
        for packet in self.inflight:
            self.send(self.sent[packet])

    def handle_new_ack(self, ack):
        pass

    def handle_dup_ack(self, ack):
        pass

    def log(self, msg):
        if self.debug:
            print msg

'''
This will be run if you run this script from the command line. You should not
change any of this; the grader may rely on the behavior here to test your
submission.
'''
if __name__ == "__main__":
    def usage():
        print "BEARS-TP Sender"
        print "-f FILE | --file=FILE The file to transfer; if empty reads from STDIN"
        print "-p PORT | --port=PORT The destination port, defaults to 33122"
        print "-a ADDRESS | --address=ADDRESS The receiver address or hostname, defaults to localhost"
        print "-d | --debug Print debug messages"
        print "-h | --help Print this usage message"

    try:
        opts, args = getopt.getopt(sys.argv[1:],
                               "f:p:a:d", ["file=", "port=", "address=", "debug="])
    except:
        usage()
        exit()

    port = 33122
    dest = "localhost"
    filename = None
    debug = False

    for o,a in opts:
        if o in ("-f", "--file="):
            filename = a
        elif o in ("-p", "--port="):
            port = int(a)
        elif o in ("-a", "--address="):
            dest = a
        elif o in ("-d", "--debug="):
            debug = True

    s = Sender(dest,port,filename,debug)
    try:
        s.start()
    except (KeyboardInterrupt, SystemExit):
        exit()
