#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/4/14 8:40
from CV_NEW.CVDataCombine import main as cv_combine
from CV_NEW.CVDataCombineSmall import main as cv_combine_small
from CV_NEW.RunCV import run_cv as cv
from CV_NEW.RunCVSmall import run_cv as cv_small
from ScheduledTask.GenerateLiveParams import run_live
from xquant.xqutils.helper import link

lm = link.LinkMessage()

#cv_combine_small()
cv_combine()
lm.sendMessage(" Tomorrow Easy CV Combine Done ")

#cv_small()
#lm.sendMessage(" Tomorrow Easy Small Model CV Done ")

cv()
lm.sendMessage(" Tomorrow Easy Big Model CV Done ")

#run_live()
#lm.sendMessage(" Tomorrow Easy Live Parameter Generated Done ")