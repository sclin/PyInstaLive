import time
import subprocess
import os
import shutil
import json
import shlex

try:
    import pil
    import helpers
    import logger
    from constants import Constants
except ImportError:
    from . import pil
    from . import helpers
    from . import logger
    from .constants import Constants


def strdatetime():
    return time.strftime('%m-%d-%Y %I:%M:%S %p')


def strtime():
    return time.strftime('%I:%M:%S %p')


def strdate():
    return time.strftime('%m-%d-%Y')


def strepochtime():
    return str(int(time.time()))


def strdatetime_compat(epochtime):
    return time.strftime('%m%d%Y_{:s}'.format(epochtime))


def check_ffmpeg():
    try:
        fnull = open(os.devnull, 'w')
        subprocess.call(["ffmpeg"], stdout=fnull, stderr=subprocess.STDOUT)
        return True
    except OSError as e:
        return False


def run_command(command):
    try:
        fnull = open(os.devnull, 'w')
        subprocess.Popen(shlex.split(command), stdout=fnull, stderr=subprocess.STDOUT)
        return False
    except Exception as e:
        return str(e)


def bool_str_parse(bool_str):
    if bool_str.lower() in ["true", "yes", "y", "1"]:
        return True
    elif bool_str.lower() in ["false", "no", "n", "0"]:
        return False
    else:
        return "Invalid"


def generate_json_segments():
    while not pil.broadcast_downloader.is_aborted:
        time.sleep(2.5)
        if 'initial_buffered_duration' not in pil.livestream_obj and pil.broadcast_downloader.initial_buffered_duration:
            pil.livestream_obj['initial_buffered_duration'] = pil.broadcast_downloader.initial_buffered_duration
        pil.livestream_obj['segments'] = pil.broadcast_downloader.segment_meta
        try:
            with open(pil.live_folder_path + ".json", 'w') as json_file:
                json.dump(pil.livestream_obj, json_file, indent=2)
        except Exception as e:
            logger.warn(str(e))


def clean_download_dir():
    dir_delcount = 0
    error_count = 0
    lock_count = 0
    try:
        logger.info('Cleaning up temporary files and folders...')
        if Constants.PYTHON_VER[0] == "2":
            directories = (os.walk(pil.dl_path).next()[1])
        else:
            directories = (os.walk(pil.dl_path).__next__()[1])

        for directory in directories:
            if directory.endswith('_downloads'):
                if not any(filename.endswith('.lock') for filename in
                           os.listdir(os.path.join(pil.dl_path, directory))):
                    try:
                        shutil.rmtree(os.path.join(pil.dl_path, directory))
                        dir_delcount += 1
                    except Exception as e:
                        logger.error("Could not remove folder: {:s}".format(str(e)))
                        error_count += 1
                else:
                    lock_count += 1
        logger.separator()
        if dir_delcount == 0 and error_count == 0 and lock_count == 0:
            logger.info('The cleanup has finished. No folders were removed.')
            logger.separator()
            return
        logger.info('The cleanup has finished.')
        logger.info('Folders removed:     {:d}'.format(dir_delcount))
        logger.info('Locked folders:      {:d}'.format(lock_count))
        logger.info('Errors:              {:d}'.format(error_count))
        logger.separator()
    except KeyboardInterrupt as e:
        logger.separator()
        logger.warn("The cleanup has been aborted.")
        if dir_delcount == 0 and error_count == 0 and lock_count == 0:
            logger.info('No folders were removed.')
            logger.separator()
            return
        logger.info('Folders removed:     {:d}'.format(dir_delcount))
        logger.info('Locked folders:      {:d}'.format(lock_count))
        logger.info('Errors:              {:d}'.format(error_count))
        logger.separator()


def show_info():
    cookie_files = []
    cookie_from_config = ''
    try:
        for file in os.listdir(os.getcwd()):
            if file.endswith(".json"):
                with open(file) as data_file:
                    try:
                        json_data = json.load(data_file)
                        if json_data.get('created_ts'):
                            cookie_files.append(file)
                    except Exception as e:
                        pass
            if pil.ig_user == file.replace(".json", ''):
                cookie_from_config = file
    except Exception as e:
        logger.warn("Could not check for cookie files: {:s}".format(str(e)))
        logger.whiteline()
    logger.info("To see all the available arguments, use the -h argument.")
    logger.whiteline()
    logger.info("PyInstaLive version:        {:s}".format(Constants.SCRIPT_VER))
    logger.info("Python version:             {:s}".format(Constants.PYTHON_VER))
    if not check_ffmpeg():
        logger.error("FFmpeg framework:        Not found")
    else:
        logger.info("FFmpeg framework:           Available")

    if len(cookie_from_config) > 0:
        logger.info("Cookie files:               {:s} ({:s} matches config user)".format(str(len(cookie_files)),
                                                                                         cookie_from_config))
    elif len(cookie_files) > 0:
        logger.info("Cookie files:               {:s}".format(str(len(cookie_files))))
    else:
        logger.warn("Cookie files:               None found")

    logger.info("CLI supports color:         {:s}".format("No" if not logger.supports_color() else "Yes"))
    logger.info(
        "Command to run at start:    {:s}".format("None" if not pil.run_at_start else pil.run_at_start))
    logger.info(
        "Command to run at finish:   {:s}".format("None" if not pil.run_at_finish else pil.run_at_finish))

    if os.path.exists(pil.config_path):
        logger.info("Config file contents:")
        logger.whiteline()
        with open(pil.config_path) as f:
            for line in f:
                logger.plain("    {:s}".format(line.rstrip()))
    else:
        logger.error("Config file:         Not found")
    logger.whiteline()
    logger.info("End of PyInstaLive information screen.")
    logger.separator()


def new_config():
    try:
        if os.path.exists(pil.config_path):
            logger.info("A configuration file is already present:")
            logger.whiteline()
            with open(pil.config_path) as f:
                for line in f:
                    logger.plain("    {:s}".format(line.rstrip()))
            logger.whiteline()
            logger.info("To create a default config file, delete 'pyinstalive.ini' and run this script again.")
            logger.separator()
        else:
            try:
                logger.warn("Could not find configuration file, creating a default one...")
                config_file = open(pil.config_path, "w")
                config_file.write(Constants.CONFIG_TEMPLATE.format(os.getcwd()).strip())
                config_file.close()
                logger.warn("Edit the created 'pyinstalive.ini' file and run this script again.")
                logger.separator()
                return
            except Exception as e:
                logger.error("Could not create default config file: {:s}".format(str(e)))
                logger.warn("You must manually create and edit it with the following template: ")
                logger.whiteline()
                for line in Constants.CONFIG_TEMPLATE.strip().splitlines():
                    logger.plain("    {:s}".format(line.rstrip()))
                logger.whiteline()
                logger.warn("Save it as 'pyinstalive.ini' and run this script again.")
                logger.separator()
    except Exception as e:
        logger.error("An error occurred: {:s}".format(str(e)))
        logger.warn(
            "If you don't have a configuration file, manually create and edit one with the following template:")
        logger.whiteline()
        logger.plain(Constants.CONFIG_TEMPLATE)
        logger.whiteline()
        logger.warn("Save it as 'pyinstalive.ini' and run this script again.")
        logger.separator()


def create_lock_user():
    try:
        if not os.path.isfile(os.path.join(pil.dl_path, pil.dl_user + '.lock')):
            if pil.use_locks:
                open(os.path.join(pil.dl_path, pil.dl_user + '.lock'), 'a').close()
                return True
        else:
            return False
    except Exception as e:
        logger.warn("Lock file could not be created. Downloads started from -df might cause problems.")
        return True


def create_lock_folder():
    try:
        if not os.path.isfile(os.path.join(pil.live_folder_path, 'folder.lock')):
            if pil.use_locks:
                open(os.path.join(pil.live_folder_path, 'folder.lock'), 'a').close()
                return True
        else:
            return False
    except Exception as e:
        logger.warn("Lock file could not be created. Downloads started from -df might cause problems.")
        return True


def remove_lock():
    try:
        os.remove(os.path.join(pil.dl_path, pil.dl_user + '.lock'))
        os.remove(os.path.join(pil.live_folder_path, 'folder.lock'))
    except Exception:
        pass


def check_lock_file():
    return os.path.isfile(os.path.join(pil.dl_path, pil.dl_user + '.lock'))
