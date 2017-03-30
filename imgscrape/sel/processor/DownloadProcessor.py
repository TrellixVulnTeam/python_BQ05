# pylint: disable=C0103, too-few-public-methods, locally-disabled, no-self-use, unused-argument, attribute-defined-outside-init, bare-except

'''Download Processor'''
from .BaseProcessor import BaseProcessor
from multiprocessing import Pool
import os
import urllib.request
import time
import base64

class DownloadProcessor(BaseProcessor):
    '''docs'''
    def __init__(self, output_directory='./', process_count=os.cpu_count()):
        '''docs'''
        self.output_directory = output_directory
        self.process_count = process_count

    def before_process(self):
        '''docs'''
        self.create_folder()
        self.pic_counter = 1

        self.preview_urls = []
        self.original_urls = []
        self.pic_prefixes = []

    def process(self, preview_image_url, original_image_url, search_term):
        '''docs'''
        self.search_term = search_term
        pic_prefix_str = search_term + str(self.pic_counter)
        if preview_image_url:
            self.preview_urls.append(preview_image_url)
            self.original_urls.append(original_image_url)
            self.pic_prefixes.append(pic_prefix_str)
            self.pic_counter += 1

    def download_single_image(self, params):
        '''docs'''
        """ Download data according to the url link given.
            Args:
                url_link (str): url str.
                pic_prefix_str (str): pic_prefix_str for unique label the pic
        """
        preview_url, original_url, pic_prefix_str = params
        self.download_fault = 0

        timeout = 1
        if preview_url.startswith("http://") or preview_url.startswith("https://"):
            try:
                response = urllib.request.urlopen(preview_url, data=None, timeout=timeout)
                if response.headers['Content-Type'] == "image/jpeg":
                    file_ext = ".jpg"
                elif response.headers['Content-Type'] == "image/png":
                    file_ext = ".png"
                elif response.headers['Content-Type'] == "image/gif":
                    file_ext = ".gif"
                else:
                    raise "image format not found"
                temp_filename = pic_prefix_str + file_ext
                temp_filename_full_path = os.path.join(self.gs_raw_dirpath, temp_filename)
                info_txt_path = os.path.join(self.gs_raw_dirpath, self.search_term + '_info.txt')
                data = response.read()  # a `bytes` object
                if len(data) > 0:
                    f = open(temp_filename_full_path, 'wb')  # save as test.gif
                    # print(url_link)
                    f.write(data)  # if have problem skip
                    f.close()
                    with open(info_txt_path, 'a') as f:
                        f.write(pic_prefix_str + ': ' + original_url)
                        f.write('\n')
            except:
                print('Problem with processing this data: ', original_url)
                self.download_fault = 1
            pass
        elif preview_url.startswith("data:"):
            if preview_url.startswith("data:image/jpeg"):
                file_ext = ".jpg"
            elif preview_url.startswith("data:image/png"):
                file_ext = ".png"
            elif preview_url.startswith("data:image/gif"):
                file_ext = ".gif"
            else:
                raise "image format not found"
            temp_filename = pic_prefix_str + file_ext
            temp_filename_full_path = os.path.join(self.gs_raw_dirpath, temp_filename)
            info_txt_path = os.path.join(self.gs_raw_dirpath, self.search_term + '_info.txt')
            with open(temp_filename_full_path, "wb") as fh:
                preview_url = preview_url[preview_url.find(",") + 1:]
                fh.write(base64.standard_b64decode(preview_url))
                with open(info_txt_path, 'a') as f:
                    f.write(pic_prefix_str + ': ' + original_url)
                    f.write('\n')

    def create_folder(self):
        """
            Create a folder to put the log data segregate by date
        """
        self.gs_raw_dirpath = os.path.join(self.output_directory, time.strftime("_%d_%b%y", time.localtime()))
        if not os.path.exists(self.gs_raw_dirpath):
            os.makedirs(self.gs_raw_dirpath)

    def after_process(self):
        '''docs'''
        thread_pool = Pool(processes=self.process_count)
        thread_pool.map(self.download_single_image, zip(self.preview_urls, self.original_urls, self.pic_prefixes))
        thread_pool.close()
        thread_pool.join()
