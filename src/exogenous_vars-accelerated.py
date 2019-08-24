import os
import getpass
import pandas as pd
import numpy as np
import csv
import statsmodels.api as sm
import warnings
import multiprocessing
from tqdm import tqdm_notebook as tqdm
from sklearn.model_selection import train_test_split
from itertools import combinations
from scipy import stats
from datetime import datetime
from sklearn.metrics import mean_absolute_error

file = 'rainfalldata.csv'
rd = pd.read_csv(file)
file2 = 'ncrainfalldata.csv'
ncrd = pd.read_csv(file2)
rd.Date = pd.to_datetime(rd.Date)
rd = rd.set_index('Date')

#%store -r exogen
exogen = {
 'Arcola, NC': ['John Kerr Dam, VA'],
 'Henderson 2 NNW, NC': ['John Kerr Dam, VA'],
 'Laurinburg, NC': [' DILLON, SC', ' CHERAW, SC'],
 'Roanoke Rapids, NC': ['Emporia, VA'],
 'Murfreesboro, NC': ['Emporia, VA'],
 'Lumberton Area, NC': [' DILLON, SC'],
 'LONGWOOD, NC': [' LORIS 2 S, SC', 'Myrtle Beach Area, SC'],
 'WHITEVILLE 7 NW, NC': [' LORIS 2 S, SC'],
 'Charlotte Area, NC': ['CATAWBA, SC', 'FORT MILL 4 NW, SC'],
 'Mount Mitchell Area, NC': ['ERWIN 1 W, TN'],
 'ASHEVILLE AIRPORT, NC': ['CAESARS HEAD, SC', 'CLEVELAND 3S, SC'],
 'BANNER ELK, NC': ['ELIZABETHTON, TN','ERWIN 1 W, TN','ROAN MOUNTAIN 3SW, TN'],
 'BEECH MOUNTAIN, NC': ['BRISTOL AP, TN', 'ELIZABETHTON, TN','ERWIN 1 W, TN','ROAN MOUNTAIN 3SW, TN'],
 'BRYSON CITY 4, NC': ['GATLINBURG 2 SW, TN', 'MT LECONTE, TN', 'NEWFOUND GAP, TN', ' TOWNSEND 5S, TN'],
 'BREVARD, NC': ['Pickens Area, SC', 'CAESARS HEAD, SC', 'CLEVELAND 3S, SC'],
 'CASAR, NC': ['CHESNEE 7 WSW, SC', 'GAFFNEY 6 E, SC'],
 'COWEETA EXP STATION, NC': ['LONG CREEK, SC', 'WALHALLA, SC', 'CLAYTON 1 SSW, GA', ' HELEN, GA', 'SAUTEE 3W, GA'],
 'CULLOWHEE, NC': ['MT LECONTE, TN', 'NEWFOUND GAP, TN'],
 'FOREST CITY 8 W, NC': ['CHESNEE 7 WSW, SC','GAFFNEY 6 E, SC','SPARTANBURG 3 SSE, SC'],
 'FRANKLIN, NC': ['LONG CREEK, SC', 'CLAYTON 1 SSW, GA', 'NEWFOUND GAP, TN'],
 'GASTONIA, NC': ['FORT MILL 4 NW, SC', 'GAFFNEY 6 E, SC'],
 'GRANDFATHER MTN, NC': ['ELIZABETHTON, TN', 'ROAN MOUNTAIN 3SW, TN'],
 ' HENDERSONVILLE 1 NE, NC': ['CAESARS HEAD, SC', 'CLEVELAND 3S, SC'],
 ' HIGHLANDS, NC': ['Pickens Area, SC','LONG CREEK, SC','WALHALLA, SC','CLAYTON 1 SSW, GA'],
 'HOT SPRINGS, NC': ['ERWIN 1 W, TN','GREENEVILLE EXP STA, TN','NEWPORT 1 NW, TN'],
 'LAKE LURE 2, NC': ['CHESNEE 7 WSW, SC', 'CLEVELAND 3S, SC'],
 'LAKE TOXAWAY 2 SW, NC': ['Pickens Area, SC','CAESARS HEAD, SC','CLEVELAND 3S, SC','LONG CREEK, SC','WALHALLA, SC'],
 'MARSHALL, NC': ['ERWIN 1 W, TN','GREENEVILLE EXP STA, TN','NEWPORT 1 NW, TN'],
 'MONROE 2 SE, NC': ['PAGELAND 9.0 WNW, SC','CATAWBA, SC','FORT MILL 4 NW, SC'],
 ' MOUNT HOLLY 4 NE, NC': ['FORT MILL 4 NW, SC'],
 ' OCONALUFTEE, NC': ['GATLINBURG 2 SW, TN','MT LECONTE, TN','NEWFOUND GAP, TN',' TOWNSEND 5S, TN'],
 'PISGAH FOREST 3 NE, NC': ['Pickens Area, SC','CAESARS HEAD, SC','CLEVELAND 3S, SC'],
 'ROBBINSVILLE AG 5 NE, NC': ['MT LECONTE, TN','NEWFOUND GAP, TN',' TOWNSEND 5S, TN'],
 'ROSMAN, NC': ['Pickens Area, SC','CAESARS HEAD, SC','CLEVELAND 3S, SC','WALHALLA, SC'],
 'SHELBY 2 NW, NC': ['CHESNEE 7 WSW, SC', 'GAFFNEY 6 E, SC'],
 'TAPOCO, NC': ['GATLINBURG 2 SW, TN', 'NEWFOUND GAP, TN', ' TOWNSEND 5S, TN'],
 'TRYON, NC': ['Greenville-Spartanburg Area, SC','CAESARS HEAD, SC','CHESNEE 7 WSW, SC','CLEVELAND 3S, SC', 'SPARTANBURG 3 SSE, SC'],
 'WAYNESVILLE 1 E, NC': ['MT LECONTE, TN', 'NEWFOUND GAP, TN'],
 'Boone 1 SE, NC': ['ROAN MOUNTAIN 3SW, TN'],
 'DANBURY, NC': ['MARTINSVILLE FILTER PLANT, VA', 'MEADOWS OF DAN 5 SW, VA','STUART, VA'],
 'EDEN, NC': ['CHATHAM, VA', 'MARTINSVILLE FILTER PLANT, VA', 'STUART, VA'],
 ' MOUNT AIRY 2 W, NC': ['MEADOWS OF DAN 5 SW, VA', 'STUART, VA'],
 'REIDSVILLE 2 NW, NC': ['MARTINSVILLE FILTER PLANT, VA'],
 'HAYESVILLE 1 NE, NC': ['CLAYTON 1 SSW, GA','BLAIRSVILLE EXP STA, GA',' HELEN, GA','SAUTEE 3W, GA'],
 'MURPHY 4ESE, NC': ['BLAIRSVILLE EXP STA, GA'],
 ' KING, NC': ['STUART, VA']
}

def sarima_model_creation(data, p, d, q, P, D, Q, m, exog=None):
    my_order = [p,d,q]
    my_sorder = [P,D,Q,m]
    sarimamod = sm.tsa.statespace.SARIMAX(data, exog, order=my_order, seasonal_order=my_sorder, 
                                          enforce_stationarity=False, enforce_invertibility=False,
                                          initialization='approximate_diffuse')
    model_fit = sarimamod.fit()# start_params=[0, 0, 0, 0, 1])
    return(model_fit)





# Function : make forecast based on provided data
#
# @param train_data --- what I already believe is true.  Dec 2007 and before 80%
# @param test_data -- what I want to prove Jan 2008 and up 20%
# @param exotrain -- external data not included but could help predictions Dec 2007 and before
# @param exotest -- external data I want to prove
# @return -- list of all predictions for the location
def model_creation_pred_one_step(train_data, test_data, exotrain=None, exotest=None):
    list_one_step = []

    nextMonth = model_based_forecast(train_data, test_data, exotrain, exotest)
    list_one_step.append(nextMonth[0]) 					# captures prediction

    # if test data exists
    if len(test_data) >= 1:
        # increment data for next month's iteration
        train_data = pd.concat([train_data, test_data[[0]]])
        test_data = test_data.drop(test_data.index[0], axis = 0)
        if exotrain is not None:
            exotrain = pd.concat([exotrain, exotest[[0]]])
            exotest = exotest.drop(exotest.index[0], axis = 0)

        # execute & capture future predictions
        futurePredictions = model_creation_pred_one_step(train_data, test_data, exotrain, exotest)
        # add to list
        list_one_step.append(futurePredictions)
    
    return(list_one_step)

# Function : Make forecast from model
# @return -- a forecast of next month's rain amount
def model_based_forecast(train_data, test_data, exotrain=None, exotest=None):
    mod = sarima_model_creation(train_data, 4, 0, 3, 3, 0, 4, 12, exotrain)
    # if exists, passing exotrain's prevMonth (december, for forecasting jan), otherwise only forcast based on model
    nextMonth = mod.forecast() if exotrain is None else mod.forecast( exotrain.iloc[[-1]] )       # turnary assignment expression
    return(nextMonth)

# previously billsFn
def maeFinder(train_data, test_data, exotrain=None, exotest=None):
    clone_train_data = train_data.copy()
    clone_test_data = test_data.copy()
    clone_exotrain = exotrain if exotrain is None else exotrain.copy()
    clone_exotest = exotest if exotest is None else exotest.copy()

    predictions = model_creation_pred_one_step(clone_train_data, clone_test_data, clone_exotrain, clone_exotest)
    mae = mean_absolute_error(test_data, predictions)
    return(mae)


def exog_combinations(df, exoe):
    lo_dfs = []
    if len(exoe) == 1:
        lo_dfs.append(df.loc[:,exoe])
    if len(exoe) > 1:
        lo_dfs.append(df.loc[:,exoe])
        for ex in exoe:
            lo_dfs.append(df.loc[:,[ex]])
        if len(exoe) >2:
            for i in range(2, len(exoe)):
                combolist = list(combinations(exoe,i))
                for c in combolist:
                    lo_dfs.append(df.loc[:,c])
    return(lo_dfs)

exogen.keys()

# Defining set of cities to evaluate
if getpass.getuser() == "rainfalld":       # docker daemon, automatically do all exogen
    todokeys = exogen.keys()
else:    # manual setting of dictionary elements to do
    todokeys = ('Roanoke Rapids, NC', 'Murfreesboro, NC', 'Lumberton Area, NC', 'LONGWOOD, NC', 'WHITEVILLE 7 NW, NC', 'Charlotte Area, NC', 'Mount Mitchell Area, NC', 'ASHEVILLE AIRPORT, NC', 'BANNER ELK, NC', 'BEECH MOUNTAIN, NC', 'BRYSON CITY 4, NC', 'BREVARD, NC', 'CASAR, NC', 'COWEETA EXP STATION, NC', 'CULLOWHEE, NC', 'FOREST CITY 8 W, NC', 'FRANKLIN, NC', 'GASTONIA, NC', 'GRANDFATHER MTN, NC', ' HENDERSONVILLE 1 NE, NC', ' HIGHLANDS, NC', 'HOT SPRINGS, NC', 'LAKE LURE 2, NC', 'LAKE TOXAWAY 2 SW, NC', 'MARSHALL, NC', 'MONROE 2 SE, NC', ' MOUNT HOLLY 4 NE, NC', ' OCONALUFTEE, NC', 'PISGAH FOREST 3 NE, NC', 'ROBBINSVILLE AG 5 NE, NC', 'ROSMAN, NC', 'SHELBY 2 NW, NC', 'TAPOCO, NC', 'TRYON, NC', 'WAYNESVILLE 1 E, NC', 'Boone 1 SE, NC', 'DANBURY, NC', 'EDEN, NC', ' MOUNT AIRY 2 W, NC', 'REIDSVILLE 2 NW, NC', 'HAYESVILLE 1 NE, NC', 'MURPHY 4ESE, NC', ' KING, NC')

sub_exogen = {k: exogen[k] for k in todokeys}

from collections import defaultdict
l_o_dfs = defaultdict(list)
for key,value in tqdm(sub_exogen.items()):
    lo_dfs2 = exog_combinations(rd, value)
    l_o_dfs[key] = lo_dfs2
l_o_dfs['LONGWOOD, NC']

def exogenous_var(data, ncloc, l_exoloc):
#     for key, value in tqdm(exo_dict.items()):
    dat = data[ncloc]
#         l_exog = exog_combinations(data, value)
    tr, test = train_test_split(dat, 0.2, False)
    keymae = maeFinder(tr, test)
    print('keymae of: '+ key +' = '+str(keymae))
    bettermae = {}
    bettermaeLock = multiprocessing.Lock()
    
    def find_exmae(exog, l):
        extr, extest = train_test_split(exog, 0.2, False)
        exmae = maeFinder(tr, test, extr, extest)
        co = tuple(exog.columns)
        if exmae < keymae:
            l.acquire()
            try:
                bettermae[co] = exmae
                bettermae2 = {key: bettermae}
            finally:
                l.release()
        
        return { "co": co, "exmae": exmae }
    
    def on_success(result):
        print('exmae = {}'.format(result["co"]) + ' '+ str(result["exmae"]))
    
    def on_error():
		# do something
        pass
    
    
    process_limit = multiprocessing.cpu_count()
    pool = multiprocessing.Semaphore(process_limit)
    # num_exmaes = len(list(l_exoloc.keys()))
    for exog in l_exoloc:
        pool.apply_async(find_exmae, (exog, bettermaeLock), None, on_success, on_error)
    
    pool.close()
    pool.join()

    return()

    # for exog in tqdm(l_exoloc):
    #     extr, extest = train_test_split(exog, 0.2, False)
    #     exmae = maeFinder(tr, test, extr, extest)
    #     co = tuple(exog.columns)
    #     print('exmae = {}'.format(co) + ' '+ str(exmae))
    #     if exmae < keymae:
    #         bettermae[co] = exmae
    #         bettermae2 = {key: bettermae}
    # return(co)

warnings.filterwarnings("ignore")
for key,value in tqdm(l_o_dfs.items()):
    exogenous_var(rd, key, value)

