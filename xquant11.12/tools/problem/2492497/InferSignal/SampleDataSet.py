import copy
import datetime as dt
import numpy as np


class SampleDataSet(object):
    def __init__(self, factorData, subTagData, sliceLag, tagName, open_tick_num=0):
        self._sliceLag = sliceLag
        self._tagName = tagName
       
        if open_tick_num > 0:
            if isinstance(self._tagName, list):
                self._factorData, self._subTagData = self.extend_factor_tag(factorData, subTagData, sliceLag, open_tick_num, self._tagName)
            else:
                self._factorData, self._subTagData = self.extend_factor_tag(factorData, subTagData, sliceLag, open_tick_num, [self._tagName])
        else:
            self._factorData = factorData
            self._subTagData = subTagData

        self._tags = self.load_tags()
        self._iStartIndex = self.createIStartIndex(self._subTagData, self._sliceLag)       
        self._iIndex = np.array(self._iStartIndex)
        self._num_examples = self._iIndex.__len__()
        self._iBatchIndex = np.arange(self._num_examples)

    @property
    def factorData(self):
        return self._factorData

    @property
    def subTagData(self):
        return self._subTagData

    @property
    def iStartIndex(self):
        return self._iStartIndex

    @property
    def num_examples(self):
        return self._num_examples

    def extend_factor_tag(self, factor_data, sub_tag, sliceLag, open_tick_num, tag_names):
        index = 0
        date = dt.datetime.fromtimestamp(sub_tag["timestamp"][index]).strftime("%Y%m%d %H%M%S%f").split(" ")[0]
        noon_timestamp = dt.datetime.strptime("{0} {1}".format(date, "120000"), "%Y%m%d %H%M%S").timestamp()
        first_afternoon = False
        extend_factor = []
        extend_sub_tag = {}
        sub_tag_gen_len = sliceLag - open_tick_num
        extend_count = 0
        if sub_tag_gen_len <= 0:
            return factor_data, sub_tag
            
        tag_keys = sub_tag.keys()   
        for key in tag_keys:
            extend_sub_tag[key] = [] 

        while index < sub_tag["timestamp"].__len__():
            if index == 0:
                if sub_tag["timestamp"][index] > noon_timestamp:
                    first_afternoon = True
                                    
                sub_tag_gen = {}
                for key in tag_keys:
                    sub_tag_gen[key] = []
                for i in range(sub_tag_gen_len):
                    extend_factor.append(np.zeros(factor_data[0, :].shape, np.float))
                    for key in tag_keys:
                        sub_tag_gen[key].append(copy.deepcopy(sub_tag[key][0]))

                for i in range(sub_tag_gen_len):           
                    for tag_name in tag_names:
                        sub_tag_gen[tag_name][i] = float("nan") 
                        
                for key in tag_keys:                    
                    extend_sub_tag[key].extend(sub_tag_gen[key])
                        
                extend_count = extend_count + 1
            elif sub_tag["timestamp"][index] > noon_timestamp and (not first_afternoon):
                sub_tag_gen = {}
                for key in tag_keys:
                    sub_tag_gen[key] = []

                for i in range(sub_tag_gen_len):
                    extend_factor.append(np.zeros(factor_data[index, :].shape, np.float))
                    for key in tag_keys:
                        sub_tag_gen[key].append(copy.deepcopy(sub_tag[key][index]))

                for i in range(sub_tag_gen_len):           
                    for tag_name in tag_names:
                        sub_tag_gen[tag_name][i] = float("nan")

                for key in tag_keys:                    
                    extend_sub_tag[key].extend(sub_tag_gen[key])
                        
                extend_count = extend_count + 1

                first_afternoon = True
                
            extend_factor.append(factor_data[index, :])

            for key in tag_keys:
                extend_sub_tag[key].append(sub_tag[key][index])
                
            index += 1  
                        
        return np.array(extend_factor), extend_sub_tag        

    def load_tags(self):
        tags = None
        if isinstance(self._tagName, list):
            for tagName in self._tagName:
                if tags is None:
                    tags = np.array(self._subTagData[tagName]).reshape(-1, 1)
                else:
                    tags = np.concatenate((tags, np.array(self._subTagData[tagName]).reshape(-1, 1)), axis=1)
        else:               
            tags = np.array(self._subTagData[self._tagName]).reshape(-1, 1)
                       
        return tags

    def next_batch_infer(self, batch_size):
        batchData = []
        batchLabel = []
        batchSubTag = {"timestamp": []}
            
        for index in self._iBatchIndex:
            iStart = self._iIndex[index]
            iEnd = iStart + self._sliceLag            
            batchData.append(np.reshape(self._factorData[iStart:iEnd, :], self._factorData[iStart:iEnd, :].size))
            batchLabel.append(self._tags[iEnd - 1])
            batchSubTag["timestamp"].append(self._subTagData["timestamp"][iEnd - 1])

        return np.array(batchData, dtype=np.float32), np.array(batchLabel, dtype=np.float32), batchSubTag   
        
    def createIStartIndex(self, subTagData, sliceLag):
        iStartIndex = []
        iStart = 0
        iEnd = sliceLag

        while iEnd <= subTagData["timestamp"].__len__():
            if abs(subTagData["timestamp"][iEnd - 1] - subTagData["timestamp"] [iStart]) < 1.5 * 3600:                                
                iStartIndex.append(iStart) 
            iStart += 1
            iEnd += 1        
        return np.array(iStartIndex, dtype=np.int32)
