import argparse
import multiprocessing
import sys

from Engine import process_now
from Map import MAPS


def parse_args():
    """parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Extract answer choices from scanned jpg bubble forms.")

    parser.add_argument('frontdir', help="Image directory.")

    parser.add_argument('-b', '--backdir', default=None,
                        help='Optional back side image directory')

    parser.add_argument('-f', '--form', default='882E',
                        choices=MAPS.keys(), help='Form string')

    return parser.parse_args()


if __name__ == '__main__':
    multiprocessing.log_to_stderr()
    args = parse_args()
    args.pool = multiprocessing.Pool()

    process_now(**vars(args))

    args.pool.close()
    args.pool.join()
    print('completed')
