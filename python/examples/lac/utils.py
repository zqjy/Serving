#   Copyright (c) 2019 PaddlePaddle Authors. All Rights Reserved.
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
"""
util tools
"""
from __future__ import print_function
import os
import sys
import numpy as np
import paddle.fluid as fluid
import io


def str2bool(v):
    """
    argparse does not support True or False in python
    """
    return v.lower() in ("true", "t", "1")


def parse_result(words, crf_decode, dataset):
    """ parse result """
    offset_list = (crf_decode.lod())[0]
    words = np.array(words)
    crf_decode = np.array(crf_decode)
    batch_size = len(offset_list) - 1

    for sent_index in range(batch_size):
        begin, end = offset_list[sent_index], offset_list[sent_index + 1]
        sent = []
        for id in words[begin:end]:
            if dataset.id2word_dict[str(id[0])] == 'OOV':
                sent.append(' ')
            else:
                sent.append(dataset.id2word_dict[str(id[0])])
        tags = [
            dataset.id2label_dict[str(id[0])] for id in crf_decode[begin:end]
        ]

        sent_out = []
        tags_out = []
        parital_word = ""
        for ind, tag in enumerate(tags):
            # for the first word
            if parital_word == "":
                parital_word = sent[ind]
                tags_out.append(tag.split('-')[0])
                continue

            # for the beginning of word
            if tag.endswith("-B") or (tag == "O" and tags[ind - 1] != "O"):
                sent_out.append(parital_word)
                tags_out.append(tag.split('-')[0])
                parital_word = sent[ind]
                continue

            parital_word += sent[ind]

        # append the last word, except for len(tags)=0
        if len(sent_out) < len(tags_out):
            sent_out.append(parital_word)
    return sent_out, tags_out


def parse_padding_result(words, crf_decode, seq_lens, dataset):
    """ parse padding result """
    words = np.squeeze(words)
    batch_size = len(seq_lens)

    batch_out = []
    for sent_index in range(batch_size):

        sent = []
        for id in words[begin:end]:
            if dataset.id2word_dict[str(id[0])] == 'OOV':
                sent.append(' ')
            else:
                sent.append(dataset.id2word_dict[str(id[0])])
        tags = [
            dataset.id2label_dict[str(id)]
            for id in crf_decode[sent_index][1:seq_lens[sent_index] - 1]
        ]

        sent_out = []
        tags_out = []
        parital_word = ""
        for ind, tag in enumerate(tags):
            # for the first word
            if parital_word == "":
                parital_word = sent[ind]
                tags_out.append(tag.split('-')[0])
                continue

            # for the beginning of word
            if tag.endswith("-B") or (tag == "O" and tags[ind - 1] != "O"):
                sent_out.append(parital_word)
                tags_out.append(tag.split('-')[0])
                parital_word = sent[ind]
                continue

            parital_word += sent[ind]

        # append the last word, except for len(tags)=0
        if len(sent_out) < len(tags_out):
            sent_out.append(parital_word)

        batch_out.append([sent_out, tags_out])
    return batch_out


def init_checkpoint(exe, init_checkpoint_path, main_program):
    """
    Init CheckPoint
    """
    assert os.path.exists(
        init_checkpoint_path), "[%s] cann't be found." % init_checkpoint_path

    def existed_persitables(var):
        """
        If existed presitabels
        """
        if not fluid.io.is_persistable(var):
            return False
        return os.path.exists(os.path.join(init_checkpoint_path, var.name))

    fluid.io.load_vars(
        exe,
        init_checkpoint_path,
        main_program=main_program,
        predicate=existed_persitables)
