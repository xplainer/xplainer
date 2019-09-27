"""
CODE REUSES FROM SHAP
"""
import json
import numpy as np
import xgboost as xgb
import math
import shap
import resource


def shap_call(xgb, sample = None):#, nb_samples = 5, feats='all', nb_features_in_exp=5):
    timer = resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime + \
            resource.getrusage(resource.RUSAGE_SELF).ru_utime
            
   
    
    if (sample is not None):
        try:
            feat_sample  = np.asarray(sample, dtype=np.float32)
        except:
            print("Cannot parse input sample:", sample)
            exit()
        print("\n\n Starting SHAP explainer... \n Considering a sample with features:", feat_sample)
        if not (len(feat_sample) == len(xgb.X_train[0])):
            print("Unmatched features are not supported: The number of features in a sample {} is not equal to the number of features in this benchmark {}".format(len(feat_sample), len(xgb.X_train[0])))
            exit()

        # compute boost predictions
        feat_sample_exp = np.expand_dims(feat_sample, axis=0)
        feat_sample_exp = xgb.transform(feat_sample_exp)
        y_pred = xgb.model.predict(feat_sample_exp)[0]
        y_pred_prob = xgb.model.predict_proba(feat_sample_exp)[0]
        
        # No need to pass dataset as it is recored in model
        # https://shap.readthedocs.io/en/latest/
        
        #X_train_clone = np.vstack((xgb.X_train, feat_sample))
        #transformed_train =  xgb.transform(X_train_clone)
        
        explainer = shap.TreeExplainer(xgb.model)
        shap_values = explainer.shap_values(feat_sample_exp)
        #print(explainer.expected_value)
        #exit()
        
        shap_values_sample = shap_values[-1]
        transformed_sample = feat_sample_exp[-1] #transformed_train[-1]


        

        # we need to sum values per feature 
        # https://github.com/slundberg/shap/issues/397
        #print(xgb.categorical_features, len(shap_values), len(transformed_sample))
        sum_values = []
        if (xgb.use_categorical):
            p = 0
            #print(xgb.categorical_features)
            for f in xgb.categorical_features:
                #print(xgb.categorical_names[f])
                nb_values = len(xgb.categorical_names[f])
                sum_v = 0
                #print(nb_values)
                for i in range(nb_values):
                    #print(i, p+i)
                    sum_v = sum_v + shap_values_sample[p+i]
                p = p + nb_values
                #print(p, sum_v)
                sum_values.append(sum_v)
            #print(sum_values)
        else:
            sum_values = shap_values_sample
        expl_for_sampling = [{"base_value": explainer.expected_value, "sum_value": np.sum(sum_values)}]
        expl = []       
        #print(model_output)
        for i in range(xgb.num_class):
            if (i !=  y_pred):
                continue
            print("\t \t Explanations for the winner class", i, " (xgboost confidence = ", y_pred_prob[i], ")")
            
        for k, v in enumerate(sum_values):
            expl.append(v)
            #print(feat_sample[k])
            if (xgb.use_categorical):
                expl_for_sampling.append(
                    [{"id":k, "score": v, "name":"", "value": feat_sample[k],  "original_name": xgb.feature_names[k], "original_value": xgb.categorical_names[k][int(feat_sample[k])]}])
            else:
                expl_for_sampling.append(
                    [{"id":k, "score": v, "name":"", "value": feat_sample[k],  "original_name": xgb.feature_names[k], "original_value": feat_sample[k]}])

        timer = resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime + \
                resource.getrusage(resource.RUSAGE_SELF).ru_utime - timer
        print('  time: {0:.2f}'.format(timer))
        #print(expl_for_sampling)
        return sorted(expl), expl_for_sampling

            
# 
#     
#     
#     max_sample = 10
#     y_pred_prob = xgb.model.predict_proba(xgb.X_test)
#     y_pred = xgb.model.predict(xgb.X_test)
# 
#     nb_tests = min(max_sample,len(xgb.y_test))
#     top_labels = 1
#     for sample in range(nb_tests):
#         np.set_printoptions(precision=2)
#         feat_sample = xgb.X_test[sample]
#         print("Considering a sample with features:", feat_sample)        
#         if (False):            
#             feat_sample[4] = 3000
#             #feat_sample[3] = 100
#             y_pred_prob_sample = xgb.model.predict_proba([feat_sample])
#             print(y_pred_prob_sample)
#         print("\t Predictions:", y_pred_prob[sample])
#         
#         
#         if (xgb.num_class  > 2):
#             for i in range(xgb.num_class):               
#                 print("\t \t Explanations for class", i, " (xgboost confidence = ", y_pred_prob[sample][i], ")")
#                 print("\t \t ", shap_values[i][sample])
#         else:
#             i = int(y_pred[sample])
#             print("\t \t Explanations for class", i, " (xgboost confidence = ", y_pred_prob[sample][i], ")")
#             print("\t \t Imact of features", shap_values[sample])
#             
#     #exp.save_to_file("1.html")
#     #plt.savefig("y", dpi=72)