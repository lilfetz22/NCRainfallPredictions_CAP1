import pandas as pd
import numpy as np
import csv
import statsmodels.api as sm
import warnings
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
    
def hyperparameter_find(training_data, comb, testing_data, search = False, exogtr = None, exogtest = None):
    leastmae = 1000
    for com in tqdm(comb):
        li_one_step = []
        for i in tqdm(range(len(testing_data))):
            if i == 0:
                copytraining = training_data.copy()
                if exogtr is not None:
                    excopy = exogtr.copy()
                    mod_1 = sarima_model_creation(copytraining, com[0], 0, com[1], com[2], 0, 
                                                  com[3], 12, exog=excopy)
                    one_step_pred = mod_1.forecast(exog=excopy.iloc[[-12]]) #change this to -12
                    excopy = pd.concat([excopy, exogtest.iloc[[i]]])
                else:
                    mod_1 = sarima_model_creation(copytraining, com[0], 0, com[1], com[2], 0, com[3], 12)
                    one_step_pred = mod_1.forecast()
                li_one_step.append(one_step_pred[0])
                copytraining = pd.concat([copytraining, testing_data[[i]]])
            else:
                if exogtr is not None:
                    mod_1 = sarima_model_creation(copytraining, com[0], 0, com[1], com[2], 0, 
                                                  com[3], 12, exog=excopy)
                    one_step_pred2 = mod_1.forecast(exog=excopy.iloc[[-12]]) # change this to -12
                    excopy = pd.concat([excopy, exogtest.iloc[[i]]])
                else:
                    mod_1 = sarima_model_creation(copytraining, com[0], 0, com[1], com[2], 0, com[3], 12)
                    one_step_pred2 = mod_1.forecast()
                li_one_step.append(one_step_pred2[0])
                copytraining = pd.concat([copytraining, testing_data[[i]]])
        mae = mean_absolute_error(testing_data, li_one_step)
        if search is True:
            if mae < leastmae:
                leastmae = mae
                H_AR = com[0]
                H_MA = com[1]
                H_SAR = com[2]
                H_SMA = com[3]
            print(com,mae)            
    if search is True:
        return('AR: '+ str(H_AR), 'MA: ' +str(H_MA), 'SAR: '+str(H_SAR), 'SMA: '+str(H_SMA))
    else:
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

todokeys = ('Roanoke Rapids, NC', 'Murfreesboro, NC', 'Lumberton Area, NC', 'LONGWOOD, NC', 'WHITEVILLE 7 NW, NC', 'Charlotte Area, NC', 'Mount Mitchell Area, NC', 'ASHEVILLE AIRPORT, NC', 'BANNER ELK, NC', 'BEECH MOUNTAIN, NC', 'BRYSON CITY 4, NC', 'BREVARD, NC', 'CASAR, NC', 'COWEETA EXP STATION, NC', 'CULLOWHEE, NC', 'FOREST CITY 8 W, NC', 'FRANKLIN, NC', 'GASTONIA, NC', 'GRANDFATHER MTN, NC', ' HENDERSONVILLE 1 NE, NC', ' HIGHLANDS, NC', 'HOT SPRINGS, NC', 'LAKE LURE 2, NC', 'LAKE TOXAWAY 2 SW, NC', 'MARSHALL, NC', 'MONROE 2 SE, NC', ' MOUNT HOLLY 4 NE, NC', ' OCONALUFTEE, NC', 'PISGAH FOREST 3 NE, NC', 'ROBBINSVILLE AG 5 NE, NC', 'ROSMAN, NC', 'SHELBY 2 NW, NC', 'TAPOCO, NC', 'TRYON, NC', 'WAYNESVILLE 1 E, NC', 'Boone 1 SE, NC', 'DANBURY, NC', 'EDEN, NC', ' MOUNT AIRY 2 W, NC', 'REIDSVILLE 2 NW, NC', 'HAYESVILLE 1 NE, NC', 'MURPHY 4ESE, NC', ' KING, NC')
sub_exogen = {k: exogen[k] for k in todokeys}

from collections import defaultdict
l_o_dfs = defaultdict(list)
for key,value in tqdm(sub_exogen.items()):
    lo_dfs2 = exog_combinations(rd, value)
    l_o_dfs[key] = lo_dfs2
l_o_dfs['LONGWOOD, NC']

def exogenous_var(data, ncloc, l_exoloc, best_comb):
#     for key, value in tqdm(exo_dict.items()):
    dat = data[ncloc]
#         l_exog = exog_combinations(data, value)
    tr, test = train_test_split(dat, test_size = 0.2, shuffle=False)
    keymae = hyperparameter_find(tr, best_comb, test)
    print('keymae of: '+ key +' = '+str(keymae))
    bettermae = {}
    for exog in tqdm(l_exoloc):
        extr, extest = train_test_split(exog, test_size = 0.2, shuffle=False)
        exmae = hyperparameter_find(tr, best_comb, test, exogtr=extr, exogtest = extest)
        co = tuple(exog.columns)
        print('exmae = {}'.format(co) + ' '+ str(exmae))
        if exmae < keymae:
            bettermae[co] = exmae
            bettermae2 = {key: bettermae}
    return(co)

best_comb = [[4,3,3,4]]
warnings.filterwarnings("ignore")
for key,value in tqdm(l_o_dfs.items()):
    exogenous_var(rd, key, value, best_comb)
