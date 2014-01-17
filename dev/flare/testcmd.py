from cmd import Cmd
import sys
import signal

class MyPrompt(Cmd):

    def do_hello(self, args):
        """Says hello. If you provide a name, it will greet you with it."""
        if len(args) == 0:
            name = 'stranger'
        else:
            name = args
        print "Hello, %s" % name

    def do_quit(self, args):
        """Quits the program."""
        print "Quitting."
        return True

    def do_EOF(self,line):
        print 'xxx'

    def do_xxx(self, args):
        raise Exception('sdf')
        print args==''

    def postloop(self):
        print 'post'

    def preloop(self):
        print 'pre'


def signal_handler(signal, frame):
    print 'You pressed Ctrl+C!'
    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    prompt = MyPrompt()
    prompt.prompt = '> '
    prompt.cmdloop('Starting prompt...')
    print 'end.'
# $Id$ 
