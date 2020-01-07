<p align="center">
    <a target="_blank"><img width="200" height="50" src="public/images/logo_0.PNG" alt="MBATS Logo"></a>
    <br />
    <br />
    <b>Microservices Based Algorithmic Trading System</b>
    <br />
    <br />
</p>

[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)

---

MBATS is a docker based platform for developing, testing and deploying Algorthmic Trading strategies with a focus on Machine Learning based algorithms.

MBATS aim to make a Quant's life a lot easier by providing a modular easy to setup trading infrastrucutre based on open source tools that can get his/her trading strategy from idea to production within few minutes.

Using MBATS, you can easily create Trading Strategies in Backtrader, manage Machine Learning models with MLflow, use Postgres database with pgAdmin for storing and querying Market data. Store files and objects in Minio and use Superset to visualize performance of backtested and live strategies. And tie all the different components together and orchestrate jobs using Airflow and many more features to help you get started from idea to live trading faster and with least effort.


[Linkedin Article about MBATS](https://www.linkedin.com/post/edit/6619730514188267520/)

![MBATS](public/images/components.png)

Table of Contents:

- [Quickstart](#Quickstart)
- [Getting Started](#getting-started)
  - [Backtrader](#Backtrader)
  - [MLflow](#MLflow)
  - [Airflow](#Apache-Airflow)
  - [Superset](#Apache-Superset)
  - [Minio](#Minio)
  - [PostgreSQL](#Postgres)
- [Cloud](#Cloud)
- [Current Features](#Current-Features)
- [Planned Features](#Planned-Features)
- [Contributing](#Contributing)
- [License](#License)
- [Authors](#Authors)
- [Acknowledgments](#Acknowledgments)
      
## Quickstart
Check out the video below to see the platform in action  
[<img src="https://img.youtube.com/vi/hLSGgW4-WC8/hqdefault.jpg" width="80%">](https://youtu.be/hLSGgW4-WC8)


MBATS is based on Docker containers. Running your Infrastructure is as easy as running one command from your terminal. You can either run MBATS on your local machine or on the cloud using docker-compose. The easiest way to setup MBATS is by running the docker-compose file. Before running the installation command make sure you have [Docker](https://www.docker.com/products/docker-desktop) installed on your machine. 


1. Downlod/Clone the Github Repository (Make sure your Docker Machine has access to the location):  
  ```git clone https://github.com/saeed349/Microservices-Based-Algorithmic-Trading-System.git```
2. Update the 'WD' variable in .env file to the location of the Cloned directory.
3. Run docker compose:  
 ```docker-compose up -d --build```  
First run would take some time as all the Docker base images need to be downloaded.  
Once its is running, you can access the following components from the webaddress
    * Jupyter Notebook:http://localhost:8888
    * Airflow: http://localhost:8080
    * MLflow: http://localhost:5500
    * PgAdmin: http://localhost:1234
    * Superset: http://localhost:8088
    * Minio: http://localhost:9000

4. Run the script to setup up the database schema   
```.\starter_script.bat```
5. All the infrastructure and business logic is in *Storage* folder and the necessary components are shared across containers.  
    - [Trading Strategies](./Storage/q_pack/q_strategies)
    - [Analyzers](./Storage/q_pack/q_analyzers)
    - [Datafeed Connectors](./Storage/q_pack/q_datafeeds)
    - [Airflow DAGS](./Storage/airflow/dags)
    - [Supporting files for Airflow](./Storage/minio/storage/airflow-files)
    - [Minio Storage](./Storage/minio)
    - [DB Schema builder code](./Storage/q_pack/db_pack)
    - [Machine Learning input files](./Storage/minio/storage/model-support-files)(./Storage/minio/storage/model-support-files)
    - [MLflow artifacts](./Storage/minio/storage/mlflow-models)
    
6. You can choose what Securities to download by listing it in [*interested_tickers.xlsx*](./Storage/minio/storage/airflow-files/)
The *daily* tab for listing the Securities for which EOD data is to be downloaded and *minute* tab for downloading at 1 minute interval. 
7. Turn on the [*fx_data_download*](./Storage/airflow/dags/dag_fx_data_download.py)  DAG in Airflow(http://localhost:8080) and this will download the Daily and Minute data for Securities you have set in the *interested_tickers.xlsx*
8. Go to Jupyter Notebook (http://localhost:8888) and use the Notebook [*Example.ipynb*](./Storage/notebooks/Example.ipynb) to run through the example strategy implementation where you can 
    - Run Backtrader trading strategies (Backtest or Live)
    - Preprocess the logs (Market Data and Indicator for each run) for preparing for Machine Learning model. 
    - Run Machine Learning models on the preprocessed data and track it to MLflow.
    - Serve the Machine Learning Artifcat(model) via MLflow
    - Bonus features of MLflow (Packaging and Serving via Rest API)
9. To check the Backtest or Live trading results go to Superset:http://localhost:8088
10. You can schedule Live trading strategies by using the [strategy.csv](./Storage/minio/storage/airflow-files) and the dynamic DAG [dag_strategy_dynamic](./Storage/airflow/dags/dag_strategy_dynamic.py) 



## Architecture

![MBATS Architecture](public/images/architecture.png)

MBATS is a collection of 9 docker containers acting synchronously to create an environment to develop and productionise trading strategies with ease. The main parts of MBATS are as follows.

### [Backtrader](https://www.backtrader.com/)
Backtrader is a python based opensource event-driven trading strategy backtester with support for live trading. The reason why I choose Backtrader over other opensource backtesters like  [Zipline](https://github.com/quantopian/zipline) and [QuantConnect](https://github.com/QuantConnect/Lean) is because of the good documentation and its community support.
Here's a list of submodules I have written for this project that are derived from Backtrader package. 
* [**Run**](./Storage/q_pack/q_run/run_BT.py) - Script that combines the strategy, analyzers and the datafeeds. 
* [**Strategy**](./Storage/q_pack/q_strategies/simple_strategy_2.py) - A simple Daily trading strategy that initiates bracket orders based on RSI and Stochastic Indicator.
* [**Logger Analyzer**](./Storage/q_pack/q_analyzers/bt_logger_analyzer.py) - Logs the price data and the indicator which is then used for training the Machine Learning model
* [**Strategy Performance Analyzer**](./Storage/q_pack/q_analyzers/bt_strat_perform_analyzer.py) - Measures  the performance of the strategy and save it in the database which is later consumed in BI tool (Superset).
* [**Round trip trade Performance Analyzer**](./Storage/q_pack/q_analyzers/bt_pos_perform_analyzer.py) - Measures difference performance metrics of round trip trades and save it in the database which is later consumed in BI tool (Superset).
* [**Transaction Analyzer**](./Storage/q_pack/q_analyzers/bt_pos_perform_analyzer.py) - Records the executed orders into the database. 
* [**Stategy ID Analyzer**](h./Storage/q_pack/q_analyzers/bt_pos_perform_analyzer.py) - Keep a record of the metadata of the backtest or live strategy ran.
* [**Oanda Broker Store**](https://github.com/ftomassetti/backtrader-oandav20) - Oanda Broker Integration for Backtrader live trading
* [**Postgress Data Feed**](./Storage/q_pack/q_datafeeds/bt_datafeed_postgres.py)

<p align="center"><img src="public/images/backtrader.png" width="700" height="500"/></p>


### [MLflow](https://MLflow.org/)

Anyone who has worked in the Datascience field would have heard about [Spark](https://spark.apache.org/), well the founders of Spark have brought a similar disruptive tool to revolutionize the Machine Learning landscape and that is MLflow. MLflow is an open source platform to manage the ML lifecycle, including experimentation, reproducibility and deployment. It currently offers four components:
* MLflow Tracking
* MLflow Projects
* MLflow Models
* MLflow Registry

There are a few other organizations that try to address this problem but what seperates MLflow from the likes of [Google-TFX](https://www.tensorflow.org/tfx), [Facebook-FBLearner Flow](https://engineering.fb.com/core-data/introducing-fblearner-flow-facebook-s-ai-backbone/) and [Uber-Michelangelo](https://eng.uber.com/michelangelo/) is that MLflow try to address the concerns of the crowd rather than a single organization and therefore they are universal and community driven to an extend that [AWS](https://aws.amazon.com/blogs/machine-learning/build-end-to-end-machine-learning-workflows-with-amazon-sagemaker-and-apache-airflow/) and [Azure](https://docs.microsoft.com/en-us/azure/machine-learning/how-to-use-MLflow) has provided integration for MLflow. 

In this project all the ML model can be tracked by the MLflow Tracker and the model artifacts are stored in Minio, the main reason for doing so is that later on I can swap Minio for a Cloud object store like S3. The ML models are then served using MLflow pyfunc. We also have the option to serve the model as Rest API using MLflow (code in sample jupyter notebook)
    
## [Apache Airflow](https://airflow.apache.org/)
Apache Airflow is an open-source workflow management platform, basically Chron on steroids and it has wide array of integration with popular platforms and data stores. 
In this this project we use airflow for scheduling two tasks mainly. One [DAG](./Storage/airflow/dags/dag_fx_data_download.py) for downloading daily and minute data into the Database controlled by an excel file and another [Dynamic DAG](./Storage/airflow/dags/dag_strategy_dynamic.py) for schedulling live strategies controlled by a csv file. 

## [Apache Superset](https://superset.apache.org/)
From the creators of Apache Airflow, Apache Superset is a Data Visualization tool initially designed by Airbnb and later open sourced for the community.
Superset is an interactive Data Exploration tool that will let you slice, dice and visualize data. Why pay for Tableau and PowerBi when you can use something that is opensource. We use Superset to visualize Backtesting and Live trading performance.  

Username:guest  
Password:guest 

The dashboards and user details are stored in Storage/superset/superset.db   
If you want to reset the credentials and create reset, just delete this sqlite [superset.db](./Storage/superset/) and create a new one with  
```touch superset.db```  
Then once the container is up and running execute  
```docker exec -it superset superset-init```

![Superset Dashboard](public/images/superset2.PNG)
## [Minio](https://min.io/)
MinIO is pioneering high performance object storage. With READ/WRITE speeds of 55 GB/s and 35 GB/s on standard hardware, object storage can operate as the primary storage tier for a diverse set of workloads. Amazon’s S3 API is the defacto standard in the object storage world and represents the most modern storage API in the market. MinIO adopted S3 compatibiity early on and was the first to extend it to support S3 Select. Because of this S3 Compatibility by using Minio we have an upper hand of moving this object store towards cloud (AWS S3, Google Cloud Storage, Azure Storage) with minimal change to the codebase.

## [PostgreSQL](https://www.postgresql.org/)
We have 2 Databases in our PosgresSQL server, 1 is the Security Master database that stores the Daily and Minute data for Forex Symbols in 2 seperate tables. 
Another Database is used for storing the position information and the performance metrics. 
The Databases can be managed through PgAdmin  
Username:guest  
Pass:guest

## Cloud
MEvery technology used in this project has a analogues managed service offered in the cloud. And the best part of scaling a microservices based architecture is that you can approach it in many ways to fits your need. Whether you want to move one functionality to the cloud or if you want to offload the workload of a component to the Cloud but keep all the critical parts on premise, the migration is quite easy when compared to a monolithic architecture. Moreover if the Cloud service is using the same technology then the migration is effortless. A simple example for this is GCP Cloud Composer which is built on top of Apache Airflow and Kubernetes which means that all the tasks/DAG's that we are using in this project can be used in Cloud Composer as well. In general I have found GCP has a better strategy and technology in place for building a hybrid Cloud infrastructure and for that reason here's an architecture if this project has to be transferred entirely into the GCP platform.
![MBATS Cloud Architecture](public/images/architecture-cloud.png)

## Current-Features
* Infrastructure as Code – less than 5 minutes from scratch to a fully functional trading infrastructure.
* Backtesting and Live trading Forex using Oanda Broker API (Can be easily be modified to accommodate IB for Equity).
* Machine Learning model development and deployment using MLflow.
* Multiple symbol strategy support.
* Multiple strategy support.
* Superset BI Dashboard for real-time monitoring of Live trading and backtesting performance results.
* Easily extensible to support any kind of structured data.
* Full code base in Python except for docker-compose setup.


## Planned-Features

* Support for Equity Database (Backtrader supports [Interactive Brokers out of the box](https://www.backtrader.com/docu/live/ib/ib/))
* Celery/Kubernetes cluster support for Airflow
* More performance and trade analytics dashboards on Superset 
* Dynamic DAG for model retraining.
* More Backtrader Examples involving -
    - Custom Indicators.
    - Alternative Data (Unstructured Data Pipeline)
    - [Reinforcement Learning](https://github.com/saeed349/Deep-Reinforcement-Learning-in-Trading).
* Use [MLflow Model Registry](https://www.MLflow.org/docs/latest/model-registry.html).
* Integrate [Alpaca API Store](https://alpaca.markets/)
* Automatic Model Selection for Strategies based on ML performance metrics.

## Built With
This project has been devloped and tested on 2 Docker environments
* [WSL](https://docs.microsoft.com/en-us/windows/wsl/about)
* [Docker Toolbox](https://docs.docker.com/toolbox/toolbox_install_windows/). 
* IDE - Visual Studio Code: Main reason being the [Container Debugger Feature](https://code.visualstudio.com/docs/remote/containers#_debugging-in-a-container) 


## Contributing

All code contributions must go through a pull request and approved by a core developer before being merged. This is to ensure proper review of all the code.

## License

This repository is available under the [BSD 3-Clause License](./LICENSE).

## Authors

* **Saeed Rahman** - [LinkedIn](https://www.linkedin.com/in/saeed-349/)


## Acknowledgments

* [Backtrader community](https://community.backtrader.com/)
* [Backtest-rookies](https://backtest-rookies.com/category/backtrader/)  
* [Backtrader Oanda V20 Store](https://github.com/ftomassetti/backtrader-oandav20)
* [Beyond Jupyter notebook - Udemy course](https://www.udemy.com/course/beyond-jupyter-notebooks/)
* [Quantstart](https://www.quantstart.com/)
