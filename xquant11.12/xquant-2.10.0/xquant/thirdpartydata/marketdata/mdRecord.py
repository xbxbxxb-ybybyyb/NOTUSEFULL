from .attrNames import SecurityTypeName

#委托队列的类
class MDOrderDetail(object):
    
    def __init__(self,MDTRecord):
        for i in SecurityTypeName.MDOrderListAttrNames:
            if hasattr(MDTRecord,i):
                setattr(self,i,getattr(MDTRecord,i))
            else:
                setattr(self,i,None)
        if hasattr(MDTRecord,"Buy1OrderDetail"):
            self.Buy1OrderDetail = list(MDTRecord.Buy1OrderDetail)
        else:
            self.Buy1OrderDetail = []
        if hasattr(MDTRecord,"Sell1OrderDetail"):
            self.Sell1OrderDetail = list(MDTRecord.Sell1OrderDetail)
        else:
            self.Sell1OrderDetail = []

#逐笔委托的类
class MDOrder(object):
    
    def __init__ (self,MDTRecord):
        for i in SecurityTypeName.MDOrderAttrNames:
            if hasattr(MDTRecord,i):
                setattr(self,i,getattr(MDTRecord,i))
            else:
                setattr(self,i,None)    
    

#tick数据的类
class MDTickRecord(object):
                                                        #maimaipan区分是否买卖盘，1是，0否
    def __init__ (self,MDTRecord,typeid=0,maimaipan=0): #用typeid区分tick数据的类型，期货是1，指数是2，其他是0 
        if typeid == 0 :                               #其他类型                       
            if maimaipan == 0:                         #一般tick数据
                AttrNames = SecurityTypeName.MDTickAttrNames   
            else:                                              #包含买卖盘的一般tick数据
                AttrNames = SecurityTypeName.getMDTickABAttrNames()
        elif typeid == 1 :                             
            if maimaipan == 0:                                 #一般期货类型tick数据
                AttrNames = SecurityTypeName.MDTickFuturesAttrNames  
            else:
                AttrNames = SecurityTypeName.geMDTickABFuturesAttrNames() #包含买卖盘期货类型tick数据
        else:
            AttrNames = SecurityTypeName.MDTickAttrNames      #指数类型，不区分买卖盘
            
        
        for i in AttrNames:
            if hasattr(MDTRecord,i):
                setattr(self,i,getattr(MDTRecord,i))
            else :
                setattr(self,i,None) 
    
    
#k线的类
class MDKLine(object):
         
    def __init__ (self,MDTRecord):
        for i in SecurityTypeName.MDKLineAttrNames:
            if hasattr(MDTRecord,i):
                setattr(self,i,getattr(MDTRecord,i))
            else:
                setattr(self,i,None) 


    

#逐笔成交的#类
class MDTransactionRecord(object):
    
    def __init__ (self,MDTRecord):
        for i in SecurityTypeName.MDTransactionAttrNames:
            if hasattr(MDTRecord,i):
                setattr(self,i,getattr(MDTRecord,i))
            else:
                setattr(self,i,None) 
        
    #用于测试
    def pritAttr(self):
        for i in self._AttributeName:
            print(getattr(self,i))       