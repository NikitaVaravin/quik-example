import pandas as pd
import datetime
import statsmodels.api as sm
import numpy as np
from sklearn.metrics import mean_squared_error,mean_absolute_percentage_error,mean_absolute_error
import itertools

from sklearn.linear_model import Ridge
import matplotlib as mpl
import matplotlib.pyplot as plt


def make_model_validate(df,target_variable,columns_drop,cut,regime = "val",start = 0):
    
    df = df.iloc[start:]
    
    train_df = df.iloc[:cut*-1,:].loc[:,[i for i in df.columns if i not in [target_variable]+columns_drop]] #cut*-1
    test_df = df.iloc[cut*-1:,:].loc[:,[i for i in df.columns if i not in [target_variable]+columns_drop]]

    y_train = df.loc[:,[target_variable]].iloc[:cut*-1] #cut*-1
    y_test = df.loc[:,[target_variable]].iloc[cut*-1:] 

    mod = sm.OLS(y_train,train_df)
    res = mod.fit()

    clf = Ridge(alpha=1.0)
    model = clf.fit(train_df,y_train)

    predict = pd.DataFrame(pd.DataFrame(data = pd.DataFrame(test_df.loc[:,pd.DataFrame(res.params).T.columns].T.to_numpy() * pd.DataFrame(res.params).to_numpy()).sum().to_numpy(),
                          columns= [target_variable],index = df["Date"].iloc[cut*-1:]))
    
    
    if regime == "val":
        rmse_ols = mean_squared_error(y_test,predict)**0.5
        rmse_ridge = mean_squared_error(y_test,model.predict(test_df))**0.5

        mae_ols = mean_absolute_error(y_test,predict)
        mae_ridge = mean_absolute_error(y_test,model.predict(test_df))

        mape_ols = mean_absolute_percentage_error(y_test,predict)
        mape_ridge = mean_absolute_percentage_error(y_test,model.predict(test_df))

        return [rmse_ols,rmse_ridge,mae_ols,mae_ridge,mape_ols,mape_ridge]
    
    elif regime == "coef":
    
        return pd.DataFrame(res.params)
    
    else:
        
        print(res.summary())
        
        fig, ax = plt.subplots(figsize=(8, 6), layout='constrained')
        ax.plot(df["Date"],df[target_variable], label= "train")
        ax.plot(predict.index,predict[target_variable], label= "test_predict")
        ax.legend()
        plt.title(target_variable)
        
def validate_model(df,target_variable,regime,variable_test,metrics,start = 0,cut_list = [3,6,9,12]):
    
    df_variable_test = pd.DataFrame()

    if regime == "metrics":

        for i in variable_test:

            inp = []
            columns_drop = ["Date",*i]
            for j in cut_list:

                if metrics == "rmse":
                    inp += [make_model_validate(df,target_variable,columns_drop,j,start = start)[0]]
                if metrics == "mae":
                    inp += [make_model_validate(df,target_variable,columns_drop,j,start = start)[2]]
                if metrics == "mape":
                    inp += [make_model_validate(df,target_variable,columns_drop,j,start = start)[4]]

            df_variable_test = pd.concat([df_variable_test,pd.DataFrame(inp).T])

        df_variable_test.columns = cut_list
        df_variable_test.index = np.array(variable_test)
        return df_variable_test

    elif regime == "coef":
        for j in cut_list:
            columns_drop = ["Date"]
            temp = make_model_validate(df,target_variable,columns_drop,j,"coef",start = start)
            temp.columns = [j]

            if len(df_variable_test) == 0:
                df_variable_test = temp
            else:
                df_variable_test = df_variable_test.join(temp)

        df_variable_test.columns = cut_list
        return df_variable_test


def get_list_variable(list_variable):
    
    end_list = []
    
    for i in range(len(list_variable)+1):
    
        test_list = list(itertools.permutations(list_variable,i))
        test_list = [sorted(list(i)) for i in test_list]
        test_list = set([tuple(i) for i in test_list])
        
        end_list += test_list
        
    return end_list

# фабрика переменных -> станок
def lags_fabrik(df,names,lags,typ,dop_if):
    
    def make_columns(name,lag,func,shift = True):
        
        if shift == True:
            temp_columns = df.loc[:,[name]].shift(periods = lag-1).apply(func) - df.loc[:,[name]].shift(periods = lag).apply(func)
            temp_columns.columns = [i[0]  + "_" + i[2] + "_" + str(i[1])]

            return temp_columns
        
        else:
            temp_columns = df.loc[:,[name]].shift(periods = lag).apply(func)
            temp_columns.columns = [i[0]  + "_" + i[2] + "_" + str(i[1])]
            return temp_columns
            
    end_df = df.copy()
    
    for i in zip(names,lags,typ,dop_if):
        
        if i[2] == "ln_diff":

            end_df = end_df.join(make_columns(i[0],i[1],lambda x:np.log(x)))
            
        if i[2] == "diff":
            
            end_df = end_df.join(make_columns(i[0],i[1],lambda x:x))
        
        if i[2] == "lag":
            
            if i[1] == 0:
                continue
            else:
                end_df = end_df.join(make_columns(i[0],i[1],lambda x:x,False))
                
        if i[2] == "dammy":
            
            def dammy_switch(x):
                if x > i[3]:
                    return 1
                else:
                    return 0
                
            dammy_switch_vec = np.vectorize(dammy_switch)
            
            end_df = end_df.join(make_columns(i[0],i[1],dammy_switch_vec,False))
       
    return end_df

# удобная надстройка для генерации переменных как в R
def multi_variables(df,name,rang,typ,dop_if):
    
    end_df = df.copy()
    
    for i in zip(name,rang,typ,dop_if):
        
        end_df = lags_fabrik(end_df,
                             [i[0] for z in range(i[1][0] - 1, i[1][1])],
                            [z+1 for z in range(i[1][0] - 1 , i[1][1])],
                            [i[2] for z in range(i[1][0] - 1 , i[1][1])],
                            [i[3] for z in range(i[1][0] - 1 , i[1][1])])
    
    
    
    return end_df