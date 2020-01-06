import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
import q_credentials.db_risk_cred as db_risk_cred

   
def create_db(db_credential_info):
    """
    create a new database if it does not exist in the PostgreSQL database
    will use method 'check_db_exists' before creating a new database
    args:
        db_credential_info: database credentials including host, user, password and db name, type array
    returns:
        NoneType
    """
    db_host, db_user, db_password, db_name = db_credential_info
    
    if check_db_exists(db_credential_info):
        pass
    else:
        print('Creating new database.')
        conn = psycopg2.connect(host=db_host, database='postgres', user=db_user, password=db_password)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        cur.execute("CREATE DATABASE %s  ;" % db_name)
        cur.close()

        
def check_db_exists(db_credential_info):
    """
    checks to see if a database already exists in the PostgreSQL database
    args:
        db_credential_info: database credentials including host, user, password and db name, type array
    returns:
        boolean value (True or False)
    """
    db_host, db_user, db_password, db_name = db_credential_info
    try:
        conn = psycopg2.connect(host=db_host, database=db_name, user=db_user, password=db_password)
        cur = conn.cursor()
        cur.close()
        print('Database exists.')
        return True
    except:
        print("Database does not exist.")
        return False

       
def create_risk_tables(db_credential_info):
    """
    create table in designated PostgreSQL database
    will use method 'check_db_exists' before creating table
    args:
        db_credential_info: database credentials including host, user, password and db name, type array
    returns:
        NoneType
    """
    db_host, db_user, db_password, db_name = db_credential_info
    conn = None
    
    if check_db_exists(db_credential_info):
        commands = (
                    """
                    CREATE TABLE run_information (
                        run_id SERIAL PRIMARY KEY,
                        run_type TEXT NOT NULL,
                        recorded_time TIMESTAMP NOT NULL NOT NULL,
                        start_time TIMESTAMP NOT NULL NOT NULL,
                        end_time TIMESTAMP NULL,
                        strategy TEXT NOT NULL,
                        tickers TEXT NOT NULL,
                        indicators TEXT NULL,
                        frequency TEXT NOT NULL,
                        account TEXT NULL,
                        log_file TEXT NULL
                        )
                    """,
                    """
                    CREATE TABLE position_performance (
                        id SERIAL PRIMARY KEY,
                        run_id INTEGER NOT NULL,
                        recorded_time TIMESTAMP NOT NULL,
                        strategy TEXT NOT NULL,
                        ref INTEGER NULL,
                        direction TEXT NOT NULL,
                        ticker TEXT NOT NULL,
                        datein TIMESTAMP NOT NULL,
                        pricein NUMERIC NOT NULL,
                        dateout TIMESTAMP NOT NULL,
                        priceout NUMERIC NOT NULL,
                        change_percentage NUMERIC NULL,
                        pnl NUMERIC NOT NULL,
                        pnl_percentage NUMERIC NULL,
                        size NUMERIC NOT NULL,
                        value NUMERIC NOT NULL,
                        cumpnl NUMERIC NOT NULL,
                        nbars INTEGER NOT NULL,
                        pnl_per_bar NUMERIC NULL,
                        mfe_percentage  NUMERIC NULL,
                        mae_percentage NUMERIC NULL,
                        FOREIGN KEY (run_id) REFERENCES run_information(run_id)
                        )
                    """,
                                       """
                    CREATE TABLE strategy_performance (
                        id SERIAL PRIMARY KEY,
                        run_id INTEGER NOT NULL,
                        total_open NUMERIC NULL,
                        total_closed NUMERIC NULL,
                        total_won NUMERIC NULL,
                        total_lost NUMERIC NULL,
                        win_streak NUMERIC NULL,
                        lose_streak NUMERIC NULL,
                        pnl_net NUMERIC NULL,
                        strike_rate NUMERIC NULL,
                        sqn NUMERIC NULL,
                        total_compound_return NUMERIC NULL,
                        avg_return NUMERIC NULL,
                        annual_norm_return NUMERIC NULL,
                        max_draw_per NUMERIC NULL,
                        max_draw_val NUMERIC NULL,
                        max_draw_len NUMERIC NULL,
                        FOREIGN KEY (run_id) REFERENCES run_information(run_id)
                        )
                    """,
                    """
                    CREATE TABLE positions (
                        id SERIAL PRIMARY KEY,
                        run_id INTEGER NOT NULL,
                        recorded_time TIMESTAMP NOT NULL,
                        strategy TEXT NOT NULL,
                        transaction_date TIMESTAMP NOT NULL,
                        size NUMERIC NULL,
                        price NUMERIC NULL,
                        sid INTEGER NOT NULL,
                        ticker TEXT NOT NULL,
                        value NUMERIC NULL,
                        FOREIGN KEY (run_id) REFERENCES run_information(run_id)
                        )
                    """
                    )
        try:
            for command in commands:
                print('Building tables.')
                conn = psycopg2.connect(host=db_host,database=db_name, user=db_user, password=db_password)
                cur = conn.cursor()
                cur.execute(command)
                # need to commit this change
                conn.commit()
                cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            cur.close()
        finally:
            if conn:
                conn.close()
    else:
        pass

def main():
    
    # create our instance variables for host, username, password and database name
    db_host=db_risk_cred.dbHost 
    db_user=db_risk_cred.dbUser
    db_password=db_risk_cred.dbPWD
    db_name=db_risk_cred.dbName
    
    # first lets create our database from postgres
    create_db([db_host, db_user, db_password, db_name])
    
    # second lets create our tables for our new database
    create_risk_tables([db_host, db_user, db_password, db_name])

    
if __name__ == "__main__":
    main()