#!/usr/bin/env python
# coding: utf-8

# # Data Story
# 
# This jupyter notebook explains the entire process that took place when analyzing the rainfall data and predicting rainfall data for the next 50 years. It first begins with exploratory data analysis, then moves to creating a Sarima model, then finishes by predicting the next 50 years of monthly rainfall from the sarima model. 

# ## Exploratory Data Analysis

# In this section of the notebook, I will be exploring the data and answering the following questions:
# 
#    1. Is there something intereseting to count?
#    2. Are there any trends (e.g. high, low, increasing, decreasing, anomalies)?
#    3. Are there any valuable comparisons between two related quantities?
#   
# I used histograms, bar plots, scatterplots, and time-series plots to answer the following questions:
# 
#    4. Are there any insights from the data?
#    5. Are there any correlations? 
#    6. What is a hypothesis that can be taken further?
#    7. What other questions arise from these insights and correlations?
#    
# After answering these questions, I provide a link to a presentation that uses text and plots to tell the compelling story of my data.

# In[34]:


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import csv
import statsmodels.api as sm
import visualization as vz
import warnings
from sklearn.model_selection import train_test_split
from tqdm import tqdm_notebook as tqdm
from textwrap import wrap
from itertools import combinations
from scipy import stats
from datetime import datetime
from statsmodels.tsa.seasonal import seasonal_decompose
from collections import defaultdict
from statsmodels.graphics.tsaplots import plot_acf
from sklearn.metrics import mean_absolute_error
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
warnings.filterwarnings("ignore")

file = '../data/manipulated_data/rainfalldata.csv'
rd = pd.read_csv(file)
file2 = '../data/manipulated_data/ncrainfalldata.csv'
ncrd = pd.read_csv(file2)
rd.Date = pd.to_datetime(rd.Date)
rd = rd.set_index('Date')
ncrd.Date = pd.to_datetime(ncrd.Date)
ncrd = ncrd.set_index('Date')


# ### Viewing the datasets.

# In[2]:


rd.head()


# In[3]:


ncrd.head()


# ### Visualizing the average rainfall per month for Raleigh, NC as a bar graph using the standard error of the mean for error bars. 
# 

# In[4]:


monthavg = []
monthsem = []
monthstd = []
for i in range(1,13):
    monthavg.append(np.mean(rd['Raleigh, NC'][rd.index.month == i]))
    monthsem.append(stats.sem(rd['Raleigh, NC'][rd.index.month == i]))
    monthstd.append(np.std(rd['Raleigh, NC'][rd.index.month == i]))
    
fig, ax = plt.subplots()
ax.bar(rd.index.month.unique(), monthavg, yerr = monthsem, alpha=0.5, ecolor='black', capsize=10)
ax.set_title('Average Monthly Rainfall in Raleigh, NC from 1956 to 2019')
ax.set_xlabel('Month')
ax.set_ylabel('Rainfall (in)')
plt.tight_layout()
plt.savefig('raleighmonthly.jpg')
plt.show()


# ### Resampling the data as average rainfall per year and comparing two different sites
# 

# In[5]:


rdyearavg = rd.resample('Y').mean()
rdyearavg.head()


# In[6]:


def yearlyavgfigs(df, loc, **keyword_parameters):
    ''' this function takes in a dataframe and a location (column) and displays the average yearly rainfall 
    for each location. Only can take up to 2 locations
    '''
    plt.figure(figsize = (400/96, 400/96),dpi=96)
    if len(loc) == 1:
        if ('color' in keyword_parameters):
            plt.plot(df.index.year, df[loc[0]], keyword_parameters['color'])
        else:
            plt.plot(df.index.year, df[loc[0]])
        plt.title('Average Yearly Rainfall in ' + loc[0] + ' from 1980 to 2019')
    else:
        plt.plot(df.index.year, df[loc[0]])
        plt.plot(df.index.year, df[loc[1]])
        plt.title("\n".join(wrap('Average Yearly Rainfall in ' + loc[0] + '-' + loc[1] + ' from 1980 to 2019', 
                                 60)))
    plt.xlabel('Year')
    plt.ylabel('Rainfall (in)')
    plt.show()
yearlyavgfigs(rdyearavg, ['Raleigh, NC'])
yearlyavgfigs(rdyearavg, ['Greensboro AP, NC'], color='orange')
yearlyavgfigs(rdyearavg, ['Raleigh, NC', 'Greensboro AP, NC'])


# ### There is a seasonality to rainfall amounts throughout the year. The following steps utilize seasonal decomposition to investigate the how often the seasonality occurred

# In[7]:


plt.rcParams["figure.figsize"] = (50,50)
plt.rcParams["font.size"] = 32.0


# In[8]:


result = seasonal_decompose(rd['Raleigh, NC'], freq=12, model='multiplicative')
result.plot()
plt.savefig('seasonalityral.jpg')
plt.show()


# ### It appears that there may be a slight increase towards the end of the sample towards an increase in rainfall amounts. Therefore, the following cells looks into whether there is a positive trend in the dataset. 

# In[9]:


t = result.trend
t2col = t.reset_index()
t2col = t2col.dropna()
t2col = t2col.reset_index()
x = np.array(t2col.index).reshape(-1,1)


# In[10]:


tdf = pd.DataFrame(t)
tdf = tdf.dropna()
y = np.array(tdf['Raleigh, NC'])


# ### As shown by the Least Squares model below. The best fit line for the trend data is a 0 degree line with one coefficient. Basically showing that there is no positive or negative correlation in rainfall over the past 40 years in Raleigh, NC. 

# In[11]:


model = sm.OLS(y, x).fit()
predictions = model.predict(x) 
model.summary()


# In[12]:


plt.rcParams["font.size"] = 12.0


# ### A look at the correlations between only 25 locations. "rd.iloc" can be manipulated to be any other set of 25 locations to see the correlations between those locations

# In[13]:


#nc heatmap
rd_fr25 = rd.iloc[:,0:25]
vz.get_corr_heat_map(rd_fr25, ignore_cancelled = False)


# # Correlation
# 
# Beginning with autocorrelation of all target (NC) locations only

# In[14]:


def autocorr(x):
    result = np.correlate(x, x, mode='full')
    rs = int(result.size/2)
    return result[rs:]


# In[15]:


autocorr(rd['Raleigh, NC'])
plot_acf(rd['Raleigh, NC'])


# ### There appear to be correlation peaks located at every prior 12 months. Showing that the previous year's rainfall for that month is correlated to that month's rainfall. Next looks at the correlation between the rainfall of the current month to the rainfall of the previous month (lag 1) and the rainfall of the same month from the prior year (lag 12)

# In[16]:


def lag_corr(df,lag=1):
    df2 = df.copy()
    cols = df2.columns
    for col in df2.columns:
        df2[col+'_'+str(lag)] = df2[col].shift(lag)
    df2=df2.dropna()
    correlation = df2.corr()
    correlation = correlation.drop(cols, axis=1)
    correlation = correlation.iloc[0:len(cols)]
    return(correlation)  


# In[17]:


nc_corr1 = lag_corr(ncrd)
nc_corr1.head() 


# In[18]:


lag12ncrd = lag_corr(ncrd,lag=12)
lag12ncrd.head()


# In[19]:


# must run Data Wrangling report first and save the dictionary from there. At the very bottom of the report it 
# stores the exogenous locations as a dictionary. The target location is the key with the exogenous locations 
# as a list of strings of the exogenous locations name. 
get_ipython().run_line_magic('store', '-r exogen')


# In[21]:


exogen.keys()


# ### Below shows one location with its exogenous variables as the lag 1

# In[22]:


def exolag(df, location, lag=1):
    df2 = df.copy()
    lt = exogen[location]
    lt2 = lt.copy()
    lt2.append(location)
    locdf = df2[lt2]
    exol = lag_corr(locdf, lag=lag)
    return(exol)
exolag(rd, 'Arcola, NC')


# In[23]:


exolag(rd, 'Arcola, NC', lag=12)


# ## Sarima Model

# ### Step 1 - fitting the model to the data

# In[24]:


def sarima_model_creation(data, p, d, q, P, D, Q, m, exog=None):
    my_order = [p,d,q]
    my_sorder = [P,D,Q,m]
    sarimamod = sm.tsa.statespace.SARIMAX(data, exog, order=my_order, seasonal_order=my_sorder, 
                                          enforce_stationarity=False, enforce_invertibility=False,
                                          initialization='approximate_diffuse')
    model_fit = sarimamod.fit()# start_params=[0, 0, 0, 0, 1])
    return(model_fit)  


# ### Step 2 - separating the training, validation, and test data

# In[25]:


training = rd['Raleigh, NC'].iloc[0:376]
validation = rd['Raleigh, NC'].iloc[376:424]
# used to train the model during the test of the never before seen test data
test_training = rd['Raleigh, NC'].iloc[0:424] 
testing = rd['Raleigh, NC'].iloc[424:]


# ### Step 3 - Creating a baseline forecast, without the training

# In[26]:


baseline = sarima_model_creation(training, 0,0,0,0,0,0,12)
baseline.forecast()


# ### Step 4 - Finding the hyperparameters

# In[27]:


def iteration_hyper(it):
    ''' This function takes a number and creates a list of lists that each contain a number from zero to the 
    provided number (it)
    '''
    outlist = []
    for AR in range(it):
        for MA in range(it):
            for SAR in range(it):
                for SMA in range(it):
                    outlist.append([AR,MA,SAR,SMA])
    return(outlist)
        
config = iteration_hyper(5) # creates all possible numbers for each parameter from 0-4


# In[28]:


def hyperparameter_find(training_data, comb, testing_data):
    ''' this function uses the training data and testing data to find out which combination of hyperparameters
    best predicts the following months rainfall.
    '''
    leastmae = 1000
    for com in comb:
        li_one_step = []
        for i in range(len(testing_data)): # iterate through the testing data
            if i is not 0:
                # create a model from all the data that includes the addition of the actual rainfall amount
                # from the previous month
                mod_1 = sarima_model_creation(copytraining, com[0], 0, com[1], com[2], 0, com[3], 12)
                one_step_pred = mod_1.forecast() # make the prediction for the next month
                li_one_step.append(one_step_pred[0]) # save prediction to a list
                copytraining = pd.concat([copytraining, testing_data[[i]]]) # add the true rainfall value
            else:
                copytraining = training_data.copy() # make a copy of the dataset
                mod_1 = sarima_model_creation(copytraining, com[0], 0, com[1], com[2], 0, com[3], 12)
                one_step_pred2 = mod_1.forecast()
                li_one_step.append(one_step_pred2[0])
                copytraining = pd.concat([copytraining, testing_data[[i]]])
        # find the mean absolute error between the what the rainfall was and what the model predicted it to be        
        mae = mean_absolute_error(testing_data, li_one_step) 
        if mae < leastmae:
            leastmae = mae
            H_AR = com[0]
            H_MA = com[1]
            H_SAR = com[2]
            H_SMA = com[3]
        print(com,mae) # due to the length of time this function takes to run, this provides an update of each
        # combination and the Mean Absolute error for that model run with the given parameters
    return('AR: '+ str(H_AR), 'MA: ' +str(H_MA), 'SAR: '+str(H_SAR), 'SMA: '+str(H_SMA))


# In[ ]:


# this cell takes a very long time to run as there are 625 different possiblities. DO NOT UN-Comment and run all
# hyperparameter_find(training, config, validation)


# The best hyperparameters for this data set were: p=4, d=0, q=3, P=3, D=0, Q=4, m=12
# 
#     p: Trend autoregression order.
#     d: Trend difference order.
#     q: Trend moving average order.
#     P: Seasonal autoregressive order.
#     D: Seasonal difference order.
#     Q: Seasonal moving average order.
#     m: The number of time steps for a single seasonal period.

# testing model on never before seen data

# In[29]:


best_comb = [[4,3,3,4]]
# the results of the following statement is shown below, takes a bit to run
#hyperparameter_find(test_training, best_comb, testing)


# Mean Absolute Error for training data = 1.23234368392907 Mean Absolute Error for Testing data = 1.8150609730404315

# ### Step 5 - Determining if any exogenous (external) locations outside of NC will increase the performace of the model
# 
# I created a library of functions that will be used to evaluate an location and its exogenous locations.  These functions first break into parallel processes to evaluate multiple exogenous MAE's at once.  The model creation and prediction uses recursive iterations for efficient memory management to then bubble up and store any improved MAE into a dictionary.

# In[30]:


def model_creation_pred_one_step(train_data, test_data, exotrain=None, exotest=None, progress_bar=None):
    ''' recursively makes forecast based on provided data for the next month
        args: train_data = large data set to base predictions on
              test_data  = decreasing dataset of data to test model
              exotrain   = exogenous location data that matches the same timeframe of train_data but was not included
              exotest    = exogenous location data that matches the same timeframe of test_data but was not included
        returns: A list of all predictions for the location matching the entire test_data timeframe
    '''
    list_one_step = []
    
    nextMonth = model_based_forecast(train_data, exotrain)
    list_one_step.append(nextMonth[0])             # captures prediction
    progress_bar.update()

    # if test data exists
    if len(test_data) > 1:
        # increment data for next month's iteration
        train_data = pd.concat([train_data, test_data[[0]]])
        test_data = test_data.drop(test_data.index[0], axis = 0)
        if exotrain is not None:
            exotrain = pd.concat([exotrain, exotest.iloc[0]])
            exotest = exotest.drop(exotest.index[0], axis = 0)

        # execute & capture future predictions
        futurePredictions = model_creation_pred_one_step(train_data, test_data, exotrain, exotest, progress_bar)
        # add to list
        list_one_step.extend(futurePredictions)
        
    return(list_one_step)


def model_based_forecast(train_data, exotrain=None):
    ''' creates model from training data & makes a forecast
        args: train_data = DataFrame to build forecasting model
              exotrain   = DataFrame of exogenous location's rainfall data
        returns: FLOAT value of next month's forecast value
    '''
    mod = sarima_model_creation(train_data, 4, 0, 3, 3, 0, 4, 12, exotrain)
    # if exists, passing exotrain's prevMonth (december, for forecasting jan), otherwise only forcast based on model
    nextMonth = mod.forecast() if exotrain is None else mod.forecast( exotrain.iloc[[-1]] )       # turnary assignment expression
    return(nextMonth)


import copy

def maeFinder(train_data, test_data, exotrain=None, exotest=None, pbar=None):
    ''' Function that finds the Mean Absolute Error between test_data and model-based predictions
        args: train_data = large data set to base predictions on
              test_data  = decreasing dataset of data to test model
              exotrain   = exogenous location data that matches the same timeframe of train_data but was not included
              exotest    = exogenous location data that matches the same timeframe of test_data but was not included
              pbar       = Progress Bar object from tqdm, to provide updates to
        returns: FLOAT of Mean Absolute Error value of potential exogenous location when included into model
    '''
    clone_train_data = copy.deepcopy(train_data)
    clone_test_data = copy.deepcopy(test_data)
    clone_exotrain = exotrain if exotrain is None else copy.deepcopy(exotrain)
    clone_exotest = exotest if exotest is None else copy.deepcopy(exotest)
    
    pbar = pbar if pbar is not None else tqdm(total=len(test_data)) # initialize counter
    
    predictions = model_creation_pred_one_step(clone_train_data, clone_test_data, clone_exotrain, clone_exotest, pbar)
    mae = mean_absolute_error(test_data, predictions)
    return(mae)


def find_exmae(exog, bettermae):
    ''' Standalone task method to find mae of a given exogenous variable.  
        Intended to be used as the function for the process pool and handle memory synchronization
        args: exog = exogenous location data to be evaluated as a potential associated location to model
              bettermae = List of new locations with better exmaes than the current keymae
        returns: Dictionary of exmae with columns
        #bettermae state is updated synchronously across all forked processes
    '''
    extr, extest = train_test_split(exog, test_size=0.2, shuffle=False)
    exmae = maeFinder(tr, test, extr, extest, pbar)
    co = tuple(exog.columns)
    if exmae < keymae:
        lock.acquire()  # process sychronization lock
        try:
            bettermae[co] = exmae
            bettermae2 = {key: bettermae}
        finally:
            lock.release()  # process synchronization release
        
    return { "co": co, "exmae": exmae }


def initExmaeWorker(l, kmae, train, testing, list_exoloc, progress_bar):
    ''' Constructor function for creating and establishing initial/global 
        variables across process pool.
        args: l = synchronization lock object
              kmae = global keymae value
              train = training dataframe object to use across processes
              testing = testing dataframe object to use across processes
              list_exoloc = list of exogenous locations related to target location
              progress_bar = tqdm object for visual progress updates
    '''
    global lock
    global keymae
    global tr
    global test
    global l_exoloc
    global pbar
    lock = l
    keymae = kmae
    tr = train
    test = testing
    l_exoloc = list_exoloc
    pbar = progress_bar


import multiprocessing

def exogenous_var(data, ncloc, l_exoloc):
    ''' Function to evaluate an location model completely.  First, it finds
        a keymae of the current data frame about a location with 20% data split.
        Secondly, it spawns a pool of processes (# of CPU cores) to calculate each potential
        exogenous location's potential improvement of the model.  Each exmae is printed to
        stdout and if improved, it is stored into the bettermae dictionary.  The NC location
        does not complete until all exmaes have been calculated.
        args: data  = entire dataframe of locations and rainfall amounts over time
              ncloc = Name of NC location (matches column in data)
              l_exoloc = list of exogenous locations to the ncloc parameter
    '''
    dat = data[ncloc]
    tr, test = train_test_split(dat, test_size=0.2, shuffle=False)
    keymae = maeFinder(tr, test)
    print('keymae of: '+ key +' = '+str(keymae))
    bettermae = {}
    bettermaeLock = multiprocessing.Lock()
    
    def on_success(result):
        print('exmae = {}'.format(result["co"]) + ' '+ str(result["exmae"]))
        progressbar.update() # update counter of completion
    
    def on_error(err):
        print(err)
        pass
    
    process_limit = multiprocessing.cpu_count()
    progressbar = tqdm(total=len(l_exoloc))  # initialize counter
    pool = multiprocessing.Pool(processes=process_limit, initializer=initExmaeWorker, initargs=(bettermaeLock, keymae, tr, test, l_exoloc, progressbar))
    for exog in l_exoloc:
        pool.apply_async(find_exmae, args=(exog, bettermae), kwds={}, callback=on_success, error_callback=on_error)
    
    pool.close()      # no more tasks can be added for the pool to accomplish
    pool.join()       # tell parent to wait until all tasks are accomplished by the process pool

    return()


# In[31]:


def exog_combinations(df, exoe):
    ''' This function takes the dataframe of rain data and the list of exogenous variables from a single NC
    location and then returns a list of dataframes that contains all of the rainfall data for just the 
    exogenous variables
    '''
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


# Using the previous function, it is placed into a for loop which creates a full list of dataframes for every location and exogenous location.

# In[35]:


l_o_dfs = defaultdict(list)
for key,value in tqdm(exogen.items()):
    lo_dfs2 = exog_combinations(rd, value)
    l_o_dfs[key] = lo_dfs2
l_o_dfs['LONGWOOD, NC']


# the following for loop goes through all of the NC locations and creates a model and finds the performance of
# the model using Mean Absolute Error. It then goes through includes each of the possible combinations of the 
# location's exogenous variables and creates a model and determines the performance of the model. Thus, it makes a model for all 46 locations with exogenous locations that are within 50 kilometers. Then it creates a model for one of the 46 target locations including their exogenous locations. If a target location has one exogenous location, then it will create one model for the target location and one for the target location with the exogenous variable included. However, if the target location has 2 or more exogenous locations it will still create a model for the target and a model for the target with each exogenous variable included. However, it will also include a forth model that creates a model with the target, target and both exogenous locations. Greater than 2 exogenous locations will also include every possible combination of the exogenous locations as separate models. All models are evaluated by Mean Absolute Error. 

# In[ ]:


# for key,value in tqdm(l_o_dfs.items()):
#     exogenous_var(rd, key, value)


# Only 8 of the 46 locations performed better including the exogenous variables, and are listed below: 
# 'WHITEVILLE 7 NW, NC', 'CASAR, NC', 'FOREST CITY 8 W, NC', 'GASTONIA, NC', 'LAKE LURE 2, NC', 
#                        'ELIZABETHTOWN, NC', ' MOUNT HOLLY 4 NE, NC','GRANDFATHER MTN, NC'

# ### Step 6 - Predictions

# Only 8 locations had exogenous variables that increased the performance of the model; therefore, a majority of the locations could be run for predictions only including the locations' rainfall data. 

# In[36]:


# removal of locations that have exogenous variables
with_exogs = ['WHITEVILLE 7 NW, NC', 'CASAR, NC', 'FOREST CITY 8 W, NC', 'GASTONIA, NC', 'LAKE LURE 2, NC', 
                       'ELIZABETHTOWN, NC', ' MOUNT HOLLY 4 NE, NC','GRANDFATHER MTN, NC']
ncrd2 = ncrd.copy()
ncrd_less = ncrd2.drop(with_exogs,axis=1)


# In[37]:


def prediction_fx(data, begin, end):
    ''' this function uses the dataframe without exogenous variables and creates a model, fits the model, and 
    then predicts the next 50 years of rainfall data as both a point prediction and a confidence interval
    '''
    base = datetime.strptime(begin,'%Y-%m-%d')
    date_list = [base + relativedelta(months=x) for x in range(600)]
    prediction1_df = pd.DataFrame(index=date_list)
    for col in tqdm(data.columns):
        loc = data[col]
        mod_fit1 = sarima_model_creation(loc, 4,0,3,3,0,4,12)
        point_predictions = pd.DataFrame(mod_fit1.predict(start=begin, end=end), columns=[col])
        future_pred1 = mod_fit1.get_prediction(start=begin, end=end)
        future_pred1_ci = future_pred1.conf_int(alpha=0.5)
        point_predictions_df = pd.merge(point_predictions, future_pred1_ci, left_index=True, right_index=True)
        prediction1_df = pd.merge(prediction1_df, point_predictions_df, left_index=True, right_index=True)
    return(prediction1_df)


# In[ ]:


pre_df = prediction_fx(ncrd_less, '2019-05-01', '2069-05-01')


# In[ ]:


exo_var_dict2 = {
    'WHITEVILLE 7 NW, NC': rd[[' LORIS 2 S, SC']],
    'CASAR, NC': rd[['GAFFNEY 6 E, SC']],
    'FOREST CITY 8 W, NC': rd[['GAFFNEY 6 E, SC']],
    'GASTONIA, NC': rd[['FORT MILL 4 NW, SC','GAFFNEY 6 E, SC']],
    'LAKE LURE 2, NC': rd[['CHESNEE 7 WSW, SC']],
    ' MOUNT HOLLY 4 NE, NC': rd[['CHESNEE 7 WSW, SC','GAFFNEY 6 E, SC']],
    'ELIZABETHTOWN, NC': rd[[' LORIS 2 S, SC']],
    'GRANDFATHER MTN, NC': rd[['ELIZABETHTON, TN']]
    
}


# In[ ]:


def prediction_exog_fx2(data, exog_dict, begin, end):
    """ this function uses the dataframe out exogenous variables and creates a model, fits the model, and
    then predicts the next 50 years of rainfall data as both a point prediction and a confidence interval
    """
    base = datetime.strptime(begin, '%Y-%m-%d')
    date_list = [base + relativedelta(months=x) for x in range(600)]
    prediction_df = pd.DataFrame(index = date_list)
    pred_val_df = pd.DataFrame(index = date_list)
    exog_predictions_df = pd.DataFrame(index = date_list)
    for key,value in tqdm(exog_dict.items()):
        loc = data[key]
        mod_fit1 = sarima_model_creation(loc, 4,0,3,3,0,4, 12,exog=value)
        if value.shape[1] > 1:
            shap = value.shape[1]
            for i in range(shap):
                exog_mod_fit = sarima_model_creation(value.iloc[:,i],4,0,3,3,0,4,12)
                e_preds2 = pd.DataFrame(exog_mod_fit.predict(start=begin, end=end))
                if i is 0:
                    exog_predictions_df = e_preds2
                else:
                    exog_predictions_df = pd.merge(exog_predictions_df, e_preds2, left_index=True, 
                                                   right_index=True)
        else:
            exog_mod_fit = sarima_model_creation(value, 4,0,3,3,0,4,12)
            exog_predictions_df = pd.DataFrame(exog_mod_fit.predict(start=begin, end=end))
        future_pred = mod_fit1.get_prediction(exog=exog_predictions_df,start=begin, end=end)
        future_pred_ci = future_pred.conf_int(alpha=0.5)
        future_pred_val= pd.DataFrame(mod_fit1.predict(exog=exog_predictions_df, start=begin, end=end), 
                                      columns = [key])
        future_pred_full = pd.merge(future_pred_val, future_pred_ci, left_index=True, right_index=True)
        prediction_df = pd.merge(prediction_df, future_pred_full, left_index=True, right_index=True)
    return(prediction_df)


# In[ ]:


e_ci_df = prediction_exog_fx2(rd, exo_var_dict2, '2019-05-01', '2069-05-01')


# In[ ]:


merged_ci_vals = pd.merge(pre_df, e_ci_df, left_index=True, right_index=True)
merged_ci_vals.head(10)


# In[ ]:


merged_ci_vals.to_csv('../data/manipulated_data/predictions.csv')


# In[ ]:


get_ipython().system('jupyter nbconvert --to script Data_Story.ipynb')


# In[39]:


from IPython.display import display


