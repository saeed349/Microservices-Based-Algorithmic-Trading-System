import pandas as pd
import boto3
from io import StringIO

def ml_preprocessing(input_file,bucket="model-support-files",fwd_returns=5):
    s3 = boto3.client('s3',endpoint_url="http://minio-image:9000",aws_access_key_id="minio-image",aws_secret_access_key="minio-image-pass")
    Bucket=bucket
    Key=input_file
    read_file = s3.get_object(Bucket=Bucket, Key=Key)
    df = pd.read_csv(read_file['Body'],sep=',',index_col=['datetime'],parse_dates=True)
    df=df.loc[:, df.columns != 'ATR'] # Removing the ATR indicator if it exists
    df['fwd_returns']=df.groupby("security")["close"].pct_change(5)
    df.sort_values(by='datetime',inplace=True)
    df=df.reset_index().drop(columns=['datetime','security','close'])
    csv_buffer = StringIO()
    df.dropna(inplace=True)
    df.to_csv(csv_buffer,index=False)
    s3.put_object(Bucket=Bucket, Key=("processed_"+Key),Body=csv_buffer.getvalue())
    return ("processed_"+Key)