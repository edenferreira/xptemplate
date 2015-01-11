#!/usr/bin/env python
# coding: utf-8

import os
import sys
import fcntl
import pprint
import subprocess
import logging
import logging.handlers
import stat
import time
import fnmatch

flags = {
        'keep': True, # keep vim open for further check if test fails
}
mybase = os.path.dirname(os.path.realpath(__file__))

class TestError( Exception ): pass

class XPTLogHandler( logging.handlers.WatchedFileHandler ):

    def _open( self ):
        _stream = logging.handlers.WatchedFileHandler._open( self )
        fd = _stream.fileno()

        r = fcntl.fcntl( fd, fcntl.F_GETFD, 0 )
        r = fcntl.fcntl( fd, fcntl.F_SETFD, r | fcntl.FD_CLOEXEC )
        return _stream

    def emit(self, record):

        try:
            st = os.stat(self.baseFilename)
            changed = (st[stat.ST_DEV] != self.dev) or (st[stat.ST_INO] != self.ino)
        except OSError, e:
            st = None
            changed = 1

        if changed and self.stream is not None:
            self.stream.flush()
            self.stream.close()
            self.stream = self._open()
            if st is None:
                st = os.stat(self.baseFilename)
            self.dev, self.ino = st[stat.ST_DEV], st[stat.ST_INO]
        logging.FileHandler.emit(self, record)

def make_logger():
    logname = 'xpt-test'
    filename = logname + ".log"

    logger = logging.getLogger( logname )
    logger.setLevel( logging.DEBUG )

    handler = XPTLogHandler( filename )

    fmt = "[%(asctime)s,%(process)d-%(thread)d,%(filename)s,%(lineno)d,%(levelname)s] %(message)s"

    _formatter = logging.Formatter( fmt )

    handler.setFormatter(_formatter)

    logger.handlers = []
    logger.addHandler( handler )

    stdhandler = logging.StreamHandler( sys.stdout )
    stdhandler.setFormatter( logging.Formatter( "[%(asctime)s,%(filename)s,%(lineno)d] %(message)s" ) )
    stdhandler.setLevel( logging.INFO )

    logger.addHandler( stdhandler )

    return logger

logger = make_logger()

key = {
        "cr":  "\r",
        "tab": "	",
        "esc": "",
        "c_v": "",
        "c_l": "",
        "c_c": "",
        "c_o": "",
}


def main( pattern, subpattern='*' ):
    logger.info("start ...")
    tmux_setup()
    try:
        run_all( pattern, subpattern )
    except TestError as e:
        # with TestError, stop and see what happened
        ex, ac = e[1], e[2]

        logger.info( "failure:" )
        for i in range( len(ex) ):
            if i >= len(ac) or ex[i] != ac[i]:
                logger.info( ( i+1, ex[i], ac[i] ) )

        if flags[ 'keep' ]:
            # wait for user to see what happened
            logger.info( "Ctrl-c to quit" )
            while True:
                time.sleep( 10 )
        else:
            tmux_cleanup()
            raise

    except Exception as e:
        # with other error, close it
        tmux_cleanup()
        raise
    tmux_cleanup()

def run_all( pattern, subpattern ):

    base = os.path.join( mybase, "cases" )

    cases = os.listdir( base )
    cases.sort()

    for c in cases:
        if not os.path.isdir( os.path.join( base, c ) ):
            continue

        if fnmatch.fnmatch( c, pattern ):
            run_case( c, subpattern )

    logger.info("all test passed")

def run_case( cname, subpattern ):

    logger.info( "running " + cname + " ..." )

    base = os.path.join( mybase, "cases", cname )

    tests_dir = os.path.join(base, 'tests')
    if os.path.isdir(tests_dir):
        run_tests(base, subpattern)
    else:
        run_oldstyle(base)

def run_oldstyle(base):

    try_rm_rst(base)

    vim_start(base)
    vim_add_rtp( base )
    vim_set_default_ft( base )
    vim_so_fn( os.path.join( base, "setting.vim" ) )
    vim_load_content( os.path.join( base, "context" ) )
    tmux_keys( "s" )
    vim_key_sequence( os.path.join( base, "keys" ) )
    vim_save_to( os.path.join( base, "rst" ) )

    check_result( base )

    vim_close()

    rcpath = os.path.join( base, 'rc' )
    fwrite( rcpath, "all-passed" )

def run_tests(casebase, subpattern):

    tests_dir = os.path.join(casebase, 'tests')
    testnames = os.listdir(tests_dir)

    for testname in testnames:
        if not fnmatch.fnmatch( testname, subpattern ):
            continue

        logger.info("running {0} {1} ...".format(os.path.basename(casebase),
                                                testname))

        test = load_test(os.path.join(tests_dir, testname))
        if test[None][:1] == ['TODO']:
            logger.info("SKIP: " + testname)
            continue

        try_rm_rst(casebase)

        vim_start(casebase)
        vim_add_rtp( casebase )
        vim_set_default_ft( casebase )
        vim_so_fn( os.path.join( casebase, "setting.vim" ) )
        vim_add_settings(test['setting'])
        vim_add_local_settings(test['localsetting'])
        vim_load_content( os.path.join( casebase, "context" ) )
        tmux_keys( "s" )

        vim_key_sequence_strings(test['keys'])
        vim_save_to( os.path.join( casebase, "rst" ) )

        rst = fread( casebase, "rst" )
        _check_rst( (casebase, testname), test['expected'], rst )
        os.unlink( os.path.join( casebase, "rst" ) )

        vim_close()

    rcpath = os.path.join( casebase, 'rc' )
    fwrite( rcpath, "all-passed" )


def load_test(testfn):

    # None for internal parameters
    test = { None: [],
             'setting': [],
             'localsetting': [],
             'keys': [],
             'expected': [], }

    cont = fread(testfn)
    state = None
    for line in cont.split('\n'):

        if line == '':
            state = None
            continue

        if state is None and line[:-1] in test:
            state = line[:-1]
            continue

        if line == 'emptyline':
            line = ''

        test[state].append( line )
        logger.info( '- ' + repr(state) + ': ' + repr(line) )

    test['expected'] = '\n'.join(test['expected'])
    return test

def try_rm_rst(base):
    try:
        os.unlink( os.path.join( base, 'rst' ) )
    except OSError as e:
        pass

def vim_start( base ):
    vimrcfn = os.path.join( base, "vimrc" )
    if not os.path.exists( vimrcfn ):
        vimrcfn = os.path.join( mybase, "core_vimrc" )

    vim_start_vimrc( vimrcfn )

def vim_start_vimrc( vimrcfn ):
    tmux_keys( "vim -u " + vimrcfn + key["cr"] )
    delay()
    logger.debug( "vim started with vimrc: " + repr(vimrcfn) )

def vim_close():
    tmux_keys( key["esc"], ":qa!", key["cr"] )
    delay()
    logger.debug( "vim closed" )

def vim_load_content( fn ):

    if not os.path.exists( fn ):
        return

    content = fread( fn )

    tmux_keys( ":append", key['cr'] )
    tmux_keys( content, key['cr'] )
    tmux_keys( key['c_c'] )
    tmux_keys( '/', key['c_v'], key['c_l'], key['cr'] )
    delay()

    logger.debug( "vim content loaded: " + repr( content ) )

def vim_so_fn( fn ):
    if not os.path.exists( fn ):
        return

    tmux_keys( ":so " + fn, key['cr'] )
    delay()
    logger.debug( "vim setting loaed: " + repr(fn) )

def vim_add_rtp( path ):
    if not os.path.exists( path ):
        return

    tmux_keys( ":set rtp+=", path, key['cr'] )
    logger.debug( "additional rtp: " + repr( path ) )

def vim_add_settings( settings ):
    if len( settings ) == 0:
        return
    vim_cmd( [ "set" ] + settings )

def vim_add_local_settings( settings ):
    if len( settings ) == 0:
        return
    vim_cmd( [ "setlocal" ] + settings )

def vim_cmd( elts ):
    s = ":" + ' '.join( elts )
    tmux_keys( s + key['cr'] )
    logger.debug( s )

def vim_set_default_ft( base ):
    ft_foo_path = _path( base, 'ftplugin', 'foo', 'foo.xpt.vim' )
    logger.debug( "ft_foo_path: " + ft_foo_path )
    if os.path.isfile( ft_foo_path ):
        vim_add_settings( [ 'filetype=foo' ] )
        # changing setting may cause a lot ftplugin to load
        delay()

def vim_key_sequence( fn ):

    if not os.path.exists(fn):
        return

    content = fread( fn )

    logger.debug( "loaded key sequence: " + repr(content) )
    lines = content.split("\n")
    vim_key_sequence_strings(lines)

def vim_key_sequence_strings( lines ):

    for line in lines:
        if line == '':
            continue
        tmux_keys( line )
        delay()

    logger.debug( "end of key sequence" )

def vim_save_to( fn ):

    tmux_keys( key['esc']*2, ":w " + fn, key['cr'] )

    while not os.path.exists( os.path.join( fn ) ):
        time.sleep(0.1)

    logger.debug( "rst saved to " + repr(fn))

def check_result( base ):

    expected = fread( base, "expected" )
    rst = fread( base, "rst" )
    _check_rst(base, expected, rst)
    os.unlink( os.path.join( base, "rst" ) )

def _check_rst(ident, expected, rst):

    if type(ident) == type(()):
        casepath, testname = ident
    else:
        casepath, testname = ident, ""

    rcpath = os.path.join( casepath, 'rc' )
    if expected != rst:
        fwrite( rcpath, "fail " + testname )
        raise TestError( ident, expected.split("\n"), rst.split("\n") )
    else:
        fwrite( rcpath, "pass " + testname )

def tmux_setup():
    try:
        _tmux( "kill-pane", "-t", 1 )
    except Exception as e:
        pass
    _tmux( "split-window", "-h", "bash --norc" )
    _tmux( "select-pane", "-t", 0 )

def tmux_cleanup():
    _tmux( "kill-pane", "-t", 1 )

def tmux_keys( *args ):
    _tmux( "send-key", "-l", "-t", 1, "".join(args) )

def _tmux( *args ):
    sh( 'tmux', *args )

def fwrite( fn, cont ):
    with open(fn, 'w') as f:
        f.write( cont )

def fread( *args ):
    fn = os.path.join( *args )
    with open(fn, 'r') as f:
        content = f.read()

    if content.endswith('\n'):
        content = content[:-1]

    return content

def delay():
    logger.debug( "delay 1 second" )
    time.sleep( 1 )

def sh( *args, **argkv ):

    args = [str(x) for x in args]
    logger.debug( "Shell Command: " + repr( args ) )

    subproc = subprocess.Popen( args,
                             close_fds = True,
                             stdout = subprocess.PIPE,
                             stderr = subprocess.PIPE, )


    out, err = subproc.communicate()
    subproc.wait()
    rst = [ subproc.returncode, out, err ]

    if subproc.returncode != 0:
        raise Exception( rst )

    return rst

def _path( *args ):
    return os.path.join( *args )


if __name__ == "__main__":
    args = sys.argv
    if '-s' in args:
        # silent mode, do not keep
        flags[ 'keep' ] = False
        args.remove( '-s' )

    if len(args) > 1:
        main(*args[1:])
    else:
        main("*")