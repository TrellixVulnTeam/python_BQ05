# Copyright 2017 The 'Scalable Private Learning with PATE' Authors All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Script to download votes files to the data/ directory.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from six.moves import urllib
import os
import tarfile

FILE_URI = 'https://storage.googleapis.com/pate-votes/votes.gz'
DATA_DIR = 'data/'


def download():
    print('Downloading ' + FILE_URI)
    tar_filename, _ = urllib.request.urlretrieve(FILE_URI)
    print('Unpacking ' + tar_filename)
    with tarfile.open(tar_filename, "r:gz") as tar:
        def is_within_directory(directory, target):
            
            abs_directory = os.path.abspath(directory)
            abs_target = os.path.abspath(target)
        
            prefix = os.path.commonprefix([abs_directory, abs_target])
            
            return prefix == abs_directory
        
        def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
        
            for member in tar.getmembers():
                member_path = os.path.join(path, member.name)
                if not is_within_directory(path, member_path):
                    raise Exception("Attempted Path Traversal in Tar File")
        
            tar.extractall(path, members, numeric_owner=numeric_owner) 
            
        
        safe_extract(tar, DATA_DIR)
    print('Done!')


if __name__ == '__main__':
    if not os.path.exists(DATA_DIR):
        print('Data directory does not exist. Creating ' + DATA_DIR)
        os.makedirs(DATA_DIR)
    download()
