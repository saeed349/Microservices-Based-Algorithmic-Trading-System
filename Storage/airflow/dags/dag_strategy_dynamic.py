#https://bigdata-etl.com/apache-airflow-create-dynamic-dag/

from airflow.models import DAG
from datetime import datetime, timedelta
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.bash_operator import BashOperator
from datetime import date, timedelta, datetime
import json
import pandas as pd
import boto3


def create_dag(dag_id,
               schedule,
               default_args,
               conf):
    dag = DAG(dag_id, default_args=default_args, schedule_interval=schedule)
    with dag:
        init = BashOperator(
            bash_command='echo START' ,
            task_id='Init',
            dag=dag
        )
        clear = BashOperator(
            bash_command='echo STOPPING',
            task_id='clear',
            dag=dag
        )
        for i,row in df.iterrows():
            command={}
            command['--strat_name']=row['Strategy']
            command['--mode']=str(row['Mode'])
            command['--tickers']=row['Securities']
            command['--broker_token']=row['Token']
            command['--broker_account']=row['Account']
            if row['Model ID']!="" or row["Strategy Parameters"]!="":
                command['--strat_param']=("model_uri="+row['Model ID']+","+row["Strategy Parameters"]) if row["Strategy Parameters"]!="" else ("model_uri="+row['Model ID'])
            final_commmand='python /usr/local/airflow/dags/q_pack/q_run/run_BT.py '+' '.join([(k+"="+v) for k, v in command.items() if v!=''])
            tab = BashOperator(
                bash_command=final_commmand,
                task_id=(str(i)+"_"+row['Strategy']),
                dag=dag
            )
            init >> tab >> clear
        return dag
schedule = None #"@daily"
dag_id = "strategy_dynamic_DAG"
s3 = boto3.client('s3',endpoint_url="http://minio-image:9000",aws_access_key_id="minio-image",aws_secret_access_key="minio-image-pass")
Bucket="airflow-files"
Key="strategy.csv"
read_file = s3.get_object(Bucket=Bucket, Key=Key)
df = pd.read_csv(read_file['Body'],sep=',')

df.fillna('', inplace=True)
args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date':datetime(2019,1,1),
    # 'start_date': datetime.now(),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
    'concurrency': 1,
    'max_active_runs': 1
}
globals()[dag_id] = create_dag(dag_id, schedule, args, df)
