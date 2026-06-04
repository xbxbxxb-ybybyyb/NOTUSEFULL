# -*- coding: utf-8 -*-
"""
Created on 2017/10/11 10:35

@author: 013050
"""
import numpy as np
import datetime as dt
import copy
import random
import re
import pandas as pd
import queue
import threading


class Data(object):
    def __init__(self, factor_data, tag_data, lag, phase_train=True, log_fd=None):

        self._phase_train = phase_train
        self._sliceLag = lag
        self._log_fd = log_fd

        self._factorData = factor_data.astype(np.float32)

        self._tags = tag_data.astype(np.float32)

        if self._phase_train:
            self._QUEUE_SIZE = 32
            self._train_data_queue = queue.Queue(self._QUEUE_SIZE)
            self._is_prefetch = True
            self._is_first_create = True
            self._is_queue_destroy = False
            self._prefetch_thr = None

        self._iStartIndex = np.arange(len(factor_data) - lag)

        self._iIndex = np.array(self._iStartIndex)
        self._num_examples = self._iIndex.__len__()
        self._iBatchIndex = np.arange(self._num_examples)
        self._epochs_completed = 0
        self._index_in_epoch = 0

    def get_train_queue(self):
        return self._train_data_queue

    @property
    def factorData(self):
        return self._factorData

    @property
    def iStartIndex(self):
        return self._iStartIndex

    @property
    def num_examples(self):
        return self._num_examples

    @property
    def epochs_completed(self):
        return self._epochs_completed

    def set_tags(self, in_tags):
        self._tags = in_tags

    def get_tags(self):
        return self._tags

    def prefetch_train(self, batch_size, shuffle=True):
        epo_count = 0
        while self._is_prefetch:
            """Return the next `batch_size` examples from this data set."""
            start = self._index_in_epoch
            # Shuffle for the first epoch
            if epo_count == 0 and start == 0 and shuffle:
                random.shuffle(self._iBatchIndex)

            # Go to the next epoch
            if start + batch_size > self._num_examples:
                self._index_in_epoch = 0
                random.shuffle(self._iBatchIndex)
                continue
            else:
                self._index_in_epoch += batch_size
                end = self._index_in_epoch
                iBatchIndex = self._iBatchIndex[start:end]

            batchData = []
            batchLabel = []
            for index in iBatchIndex:
                iStart = self._iIndex[index]
                iEnd = iStart + self._sliceLag
                batchData.append(self._factorData[iStart:iEnd, :])
                batchLabel.append(self._tags[iEnd - 1])
            self._train_data_queue.put([np.array(batchData, dtype=np.float32), np.array(batchLabel, dtype=np.float32)])

        while not self._train_data_queue.empty():
            try:
                self._train_data_queue.get(block=True, timeout=1)
            except queue.Empty:
                print("queue is empty")
        self._is_queue_destroy = True
        if self._log_fd is None:
            print("prefetch finshed")
        else:
            self._log_fd.logger.debug("prefetch finshed")

    def __del__(self):
        self.destroy()

    def destroy(self):
        if self._phase_train:
            self._is_prefetch = False
            if self._train_data_queue is not None:
                while not self._train_data_queue.empty():
                    try:
                        self._train_data_queue.get(block=True, timeout=1)
                        self._train_data_queue.task_done()
                    except queue.Empty:
                        if self._log_fd is None:
                            print("queue is empty")
                        else:
                            self._log_fd.logger.debug("queue is empty")

            if self._prefetch_thr is not None:
                self._prefetch_thr.join()
                self._prefetch_thr = None
                if self._log_fd is None:
                    print("prefetch destroy finshed")
                else:
                    self._log_fd.logger.debug("prefetch destroy finshed")

            self._train_data_queue = None

    def next_batch_train_prefetch(self, batch_size, shuffle=True):
        if self._phase_train and self._is_first_create:
            self._is_first_create = False
            self._prefetch_thr = threading.Thread(target=Data.prefetch_train,
                                                  args=(self, batch_size, shuffle,))
            self._prefetch_thr.daemon = True
            self._prefetch_thr.start()
        while not self._is_queue_destroy and self._train_data_queue is not None:
            try:
                batchData, batchLabel = self._train_data_queue.get(block=True, timeout=1)
                # print (batchData.shape, batchLabel.shape, batchLabel[0:3])
                self._train_data_queue.task_done()
                return batchData, batchLabel
            except queue.Empty:
                if self._log_fd is None:
                    print("queue is empty")
                else:
                    self._log_fd.logger.debug("queue is empty")

    def next_batch_valid(self):
        batchData = []
        batchLabel = []
        for index in self._iBatchIndex:
            iStart = self._iIndex[index]
            iEnd = iStart + self._sliceLag
            batchData.append(self._factorData[iStart:iEnd, :])
            batchLabel.append(self._tags[iEnd - 1])
        return np.array(batchData, dtype=np.float32), np.array(batchLabel, dtype=np.float32)
