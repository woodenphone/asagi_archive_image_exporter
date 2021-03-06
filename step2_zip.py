#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      User
#
# Created:     27-09-2018
# Copyright:   (c) User 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------
# StdLib
import logging
import argparse
import os
import csv
import zipfile
# Remote libraries
# local
from common import *# Things like logging setup






def add_to_zip(zip_obj, filepath, internal_path):
    """Return whether file was added to zip"""
    try:
##        logging.debug('Zipping {0!r} as {1!r}'.format(filepath, internal_path))# PERFORMANCE This might cause slowdowns, disable outside testing
        zip_obj.write(filepath, internal_path)
        return True
    except OSError, err:
        logging.error(err)
    return False


def generate_image_filepath(board_dir, filename):
    # Expects filename to look like: '1536631035276.webm'
    # Outputs: 'BASE/153/6/1536631035276.webm'
    # boards/<boardName>/<thumb or image>/<char 0-3>/<char 4-5>/<full image name>
    # base/image/1536/63/1536631035276.webm
    assert(len(filename) > 4)# We can't generate a path is this is lower, and the value is based on unix time so should always be over 1,000,000
    media_filepath = os.path.join(board_dir, filename[0:4], filename[4:6], filename)# string positions 0,1,2,3/4,5/filename
    return media_filepath


def generate_full_image_filepath(images_dir, board_name, filename):
    # boards/<boardName>/<thumb or image>/<char 0-3>/<char 4-5>/<full image name>
    board_dir = os.path.join(images_dir, board_name,  'image')
    full_image_filepath = generate_image_filepath(board_dir, filename)
    return full_image_filepath


def generate_thumbnail_image_filepath(images_dir, board_name, filename):
    # boards/<boardName>/<thumb or image>/<char 0-3>/<char 4-5>/<full image name>
    board_dir = os.path.join(images_dir, board_name, 'thumb')
    full_image_filepath = generate_image_filepath(board_dir, filename)
    return full_image_filepath


def zip_from_csv(csv_filepath, images_dir, zip_path, board_name):
    """Attempt to zip all images from the CSV file"""
    logging.debug('zip_from_csv() locals() = {0!r}'.format(locals()))# Record arguments
    logging.info('Zipping files in {0} to {1}'.format(csv_filepath, zip_path))

    # Error checking before any work is done
    if not (os.path.exists(csv_filepath)):# We can't do anything if this is not present.
        logging.error('CSV file does not exist, cannot export! csv_filepath = {0!r}'.format(csv_filepath))
        raise ValueError()
    if not (os.path.exists(images_dir)):# We can't do anything if this is not present.
        logging.error('Image dir does not exist, cannot export! images_dir = {0!r}'.format(images_dir))
        raise ValueError()

    # Ensure output dir exists
    output_dir = os.path.dirname(zip_path)
    if not os.path.exists(output_dir):
        logging.debug('Creating output_dir = {0!r}'.format(output_dir))
        os.makedirs(output_dir)
        assert(os.path.exists(output_dir))# the dir should now exist

    file_counter = 0# Total number of files attempted.
    failed_file_counter = 0# Total number of files that had a failure in some way.
    success_file_counter = 0# Total number of files that were successfully added to zip.
    row_counter = 0
    with zipfile.ZipFile(zip_path, 'w') as myzip:
        # First, add the CSV to the zip
        add_to_zip(
            zip_obj=myzip,
            filepath=os.path.join(csv_filepath),
            internal_path=os.path.basename(csv_filepath)
        )

        # Add images from each row in the CSV file
        with open(csv_filepath, 'rb', ) as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',',quotechar='"', quoting = csv.QUOTE_ALL, lineterminator='\n')
            for row in reader:
                row_counter += 1
                if (row_counter % 100 == 0):
                    logging.info('Processed {0} rows.'.format(row_counter))
                # Add media to zip
                if row['media']:
                    media_success = add_to_zip(
                        zip_obj=myzip,
                        filepath=generate_full_image_filepath(# Filesystem
                            images_dir=images_dir,
                            board_name=board_name,
                            filename=row['media']
                        ),
                        internal_path=generate_full_image_filepath(# Zip internal
                            images_dir='',
                            board_name=board_name,
                            filename=row['media']
                        )
                    )
                    if media_success:
                        success_file_counter += 1
                    else:
                        failed_file_counter += 1
                    file_counter += 1
                # Add preview_op to zip
                if row['preview_op']:
                    preview_op_success = add_to_zip(
                        zip_obj=myzip,
                        filepath=generate_thumbnail_image_filepath(# Filesystem
                            images_dir=images_dir,
                            board_name=board_name,
                            filename=row['preview_op']
                        ),
                        internal_path=generate_thumbnail_image_filepath(# Zip internal
                            images_dir='',
                            board_name=board_name,
                            filename=row['preview_op']
                        )
                    )
                    if preview_op_success:
                        success_file_counter += 1
                    else:
                        failed_file_counter += 1
                    file_counter += 1

                # Add preview_reply to zip
                if row['preview_reply']:
                    preview_reply_success = add_to_zip(
                        zip_obj=myzip,
                        filepath=generate_thumbnail_image_filepath(# Filesystem
                            images_dir=images_dir,
                            board_name=board_name,
                            filename=row['preview_reply']
                        ),
                        internal_path=generate_thumbnail_image_filepath(# Zip internal
                            images_dir='',
                            board_name=board_name,
                            filename=row['preview_reply']
                        )
                    )
                    if preview_reply_success:
                        success_file_counter += 1
                    else:
                        failed_file_counter += 1
                    file_counter += 1

    logging.debug('row_counter = {rc}'.format(rc=row_counter))
    logging.debug('file_counter = {tot}, success_file_counter = {suc}, failed_file_counter = {fail}'.format(
        tot=file_counter, suc=success_file_counter, fail=failed_file_counter
        ))

    assert(os.path.exists(zip_path))# The zip file should now exist.
    logging.info('Finished zipping files from {0} rows in {1} to {2}'.format(row_counter, csv_filepath, zip_path))
    return


def yaml():
    """Run from a YAML config file"""
    logging.info('exiting yaml()')
    return


def cli():
    """Command line running"""
    # Handle command line args
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv_filepath', help='csv_filepath, mandatory.',
                    type=str)
    parser.add_argument('--images_dir', help='images_di, mandatory.r',
                    type=str)
    parser.add_argument('--zip_path', help='zip_path, mandatory.',
                    type=str)
    parser.add_argument('--board_name', help='board_name, mandatory.',
                    type=str)
    args = parser.parse_args()

    logging.debug('args: {0!r}'.format(args))# Record CLI arguments

    zip_from_csv(
        csv_filepath=args.csv_filepath,
        images_dir=args.images_dir,
        zip_path=args.zip_path,
        board_name=args.board_name
    )

    logging.info('exiting cli()')
    return


def dev():
    """For development/debugging in IDE/editor without CLI arguments"""
    logging.warning('running dev()')

    import config

    csv_filepath = config.CSV_FILEPATH
    zip_path = config.ZIP_PATH
    images_dir = '.'
    board_name = config.BOARD_NAME
    zip_from_csv(
        csv_filepath=csv_filepath,
        images_dir=images_dir,
        zip_path=zip_path,
        board_name=board_name,
    )

    logging.warning('exiting dev()')
    return


def main():
    cli()
##    dev()
    return

if __name__ == '__main__':
    setup_logging(os.path.join("debug", "step2_zip.log.txt"))# Setup logging
    try:
        main()
    # Log exceptions
    except Exception, e:
        logging.critical("Unhandled exception!")
        logging.exception(e)
    logging.info("Program finished.")







