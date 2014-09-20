#! /usr/bin/env python3

from contextlib import contextmanager
from os import curdir
import argparse
import fnmatch
import hashlib
import os


MIN_BIG_FILE_SIZE_BYTES = 100 * 1024


logger = None


@contextmanager
def current_directory(dir):
    olddir = os.getcwd()
    try:
        os.chdir(dir)
        yield
    finally:
        os.chdir(olddir)


def our_getsize(dir, file):
    # Change to the file's directory and do the system call using just
    # the filename to try and avoid hitting OS pathname length limits.
    with current_directory(dir):
        try:
            return os.path.getsize(file)
        except FileNotFoundError as err:
            logger.warning(str(err))
            return 0


def getdirstamp(dir, subdirs, files):
    if subdirs:
        logger.debug('no stamp because subdirs')
        return None
    all_files_sizes = ((file, our_getsize(dir, file))
                       for file in files)
    big_files_sizes = [(file, size)
                       for (file, size) in all_files_sizes
                       if size >= MIN_BIG_FILE_SIZE_BYTES]
    if not big_files_sizes:
        logger.debug('no stamp because no big files')
        return None
    stamp_repr = ascii(repr(tuple(sorted(big_files_sizes))))
    logger.debug('stamp_repr == {}'.format(stamp_repr))
    return hashlib.md5(bytes(stamp_repr, 'ascii')).hexdigest()


def getstampdirs(rootdir):
    stamp_dirset = {}
    for dir, subdirs, files in os.walk(rootdir):
        logger.debug('visiting {}'.format(dir))
        stamp = getdirstamp(dir, subdirs, files)
        if stamp:
            stamp_dirset.setdefault(stamp, set()).add(dir)
    return stamp_dirset


def resolve(dirs):
    print("Directories are equal:")
    for dir in dirs:
        line = "  {}".format(dir)
        try:
            print(line)
        except UnicodeEncodeError:
            print(ascii(line))
    print()


def main():
    for stamp, dirs in getstampdirs(curdir).items():
        if len(dirs) > 1:
            resolve(dirs)


def config_logging(prog, verbose):
    import logging
    levels = (logging.WARNING, logging.INFO, logging.DEBUG)
    logging.basicConfig(
        level=levels[min((verbose or 0), len(levels)-1)],
        format='%(name)s: %(levelname)s: %(message)s')
    return logging.getLogger(prog)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('-v', '--verbose', help='emit informational messages (twice for debug)', action='count', default=0)
    args = ap.parse_args()
    logger = config_logging(ap.prog, args.verbose)
    main()
