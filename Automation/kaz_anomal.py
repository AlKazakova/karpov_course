import telegram
import io
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import pandahouse as ph
from statsmodels.tsa.seasonal import STL

#подключение к clickhouse
connection = {
    'host': 'https://clickhouse.lab.karpov.courses/',
    'password': 'dpo_python_2020',
    'user': 'student',
    'database': 'simulator_20240620'
}

default_args = {
    'owner': 'Kazakova_Alena',           
    'depends_on_past': False,            
    'retries': 2,                        
    'retry_delay': timedelta(minutes=5), 
    'start_date': datetime(2024, 7, 1),
}

schedule_interval = '0 0/15 * * *'

my_token = '7433120991:AAFHvx0Q-6kubhleX7GaLKv8UJo5bfuBzNE' 
bot = telegram.Bot(token=my_token) 
chat_id = 428582124

@dag(default_args=default_args, schedule_interval=schedule_interval, catchup=False)
def kazakova_anomalies():
    def anomalies(df,metric, a=3, n=5):
        df['q25'] = df[metric].shift(1).rolling(n).quantile(0.25)
        df['q75'] = df[metric].shift(1).rolling(n).quantile(0.75)
        df['iqr'] = df['q75'] - df['q25']
        df['low'] = df['q25'] - a * df['iqr']
        df['up'] = df['q75'] + a * df['iqr']

        df['low'] = df['low'].rolling(n, center=True, min_periods=1).mean()
        df['up'] = df['up'].rolling(n, center=True, min_periods=1).mean()

        if df[metric].iloc[-1] < df['low'].iloc[-1] or df[metric].iloc[-1] > df['up'].iloc[-1]:
            is_alert = 1
        else:
            is_alert = 0
        return df, is_alert

    def normalize(data, metric, n=5):
        df = pd.DataFrame(data['t15'])
        mean = data[metric].mean()
        std = data[metric].std()
        df[metric] = (data[metric] - mean)/std
        df[metric] = df[metric].rolling(n, min_periods=1).mean()
        return df

    def query_dataset():
        query_feed = '''
            SELECT 
                    toStartOfFifteenMinutes(time) as t15,
                    uniq(user_id) as users_feed,
                    countIf(user_id, action='like') as likes,
                    countIf(user_id, action='view') as views,
                    likes/views as ctr             
            FROM simulator_20240620.feed_actions
            WHERE time >= today() - 2
              AND time < toStartOfFifteenMinutes(now())
            GROUP BY t15
            ORDER BY t15
            '''
        df_feed = ph.read_clickhouse(query_feed, connection=connection)

        query_mes = '''
            SELECT 
                    toStartOfFifteenMinutes(time) as t15,
                    uniq(user_id) as users_mes,
                    count(receiver_id) as sent_mess          
            FROM simulator_20240620.message_actions
            WHERE time >= today() - 2
              AND time < toStartOfFifteenMinutes(now())
            GROUP BY t15
            ORDER BY t15
            '''
        df_mes = ph.read_clickhouse(query_mes, connection=connection)

        data = pd.concat([df_feed, df_mes['users_mes'], df_mes['sent_mess']], axis=1)
        metrics = ['users_feed', 'likes', 'views', 'ctr', 'users_mes', 'sent_mess']

        for metric in metrics:
            df = normalize(data, metric) 
            df, is_alert = anomalies(df, metric)

            current_value = df[metric].iloc[-1]
            previous_value = df[metric].iloc[-2]
            diff = round(1 - (current_value / previous_value), 4) * 100

            if is_alert == 1:
                mess = f'''Аномалия в {metric} \n Текующее значение {previous_value} \n Отклонение от текущего значения {diff}% \n 
                            также можно перейти по ссылке в суперсет https://superset.lab.karpov.courses/superset/dashboard/5694/'''

                plt.tight_layout()
                plt.figure(figsize=(12, 6))
                ax = sns.lineplot(x = df['t15'], y = df[metric], label = metric)
                ax = sns.lineplot(x = df['t15'], y = df['up'], label = 'up')
                ax = sns.lineplot(x = df['t15'], y = df['low'], label = 'low')

                for ind, label in enumerate(ax.get_xticklabels()):
                    if ind % 2 == 0:
                        label.set_visible(True)
                    else:
                        label.set_visible(False)  
            else:
                continue


            plot_object = io.BytesIO()
            plt.savefig(plot_object)
            plot_object.seek(0)
            plot_object.name = f'{metric}.png'
            plt.close()

            bot.sendMessage(chat_id=chat_id, text=mess)
            bot.sendPhoto(chat_id=chat_id, photo=plot_object)
        
    query_dataset = query_dataset()
    
kazakova_anomalies = kazakova_anomalies()