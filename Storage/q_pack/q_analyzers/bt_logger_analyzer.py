import backtrader as bt
import datetime
import pandas as pd
import os

import boto3
from io import StringIO

class logger_analyzer(bt.Analyzer):

    def get_analysis(self):
        return None

    def stop(self):
        ml_list=[]
        data_size=len(self.data)
        num_of_sec=len(self.datas)
        if self.strategy.p.backtest:   
            for i, d in enumerate(self.datas):
                ml_dict={}
                data_size=len(d)
                ml_dict["security"]=[d._name]*data_size
                ml_dict["datetime"]=[self.data.num2date(x) for x in d.datetime.get(size=data_size)]#self.data
                ml_dict["open"]=d.open.get(size=data_size)
                ml_dict["high"]=d.high.get(size=data_size)
                ml_dict["low"]=d.low.get(size=data_size)
                ml_dict["close"]=d.close.get(size=data_size)
                # ml_dict["close"]=d.get(size=data_size)
                num_of_indicators=int(len(self.strategy.getindicators())/len(self.strategy.datas))
                for j in range(num_of_indicators):
                    ml_dict[self.strategy.getindicators()[j*num_of_sec+i].aliased]=self.strategy.getindicators()[j*num_of_sec+i].get(size=data_size) # tested for 3 conditions , indicators >,<,= securities
                ml_list.append(pd.DataFrame(ml_dict))  
            ml_df = pd.concat(ml_list,axis=0)
            s3 = boto3.client('s3',endpoint_url="http://minio-image:9000",aws_access_key_id="minio-image",aws_secret_access_key="minio-image-pass")
            Bucket="model-support-files"
            Key=str(self.strategy.db_run_id)+"_ml_log.csv"
            csv_buffer = StringIO()
            ml_df.to_csv(csv_buffer,index=False)
            s3.put_object(Bucket=Bucket, Key=Key,Body=csv_buffer.getvalue())
            print("ML Log Saved in Minio Bucket:",Bucket,"as",Key)
            
