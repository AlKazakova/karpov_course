import pandahouse as ph
from airflow.decorators import dag, task
from datetime import timedelta, datetime
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np
import telegram
import io

#подключение к clickhouse
connection = {
    'host': 'https://clickhouse.lab.karpov.courses/',
    'password': 'dpo_python_2020',
    'user': 'student',
    'database': 'simulator_20240620'
}

default_args = {
    'owner': 'Kazakova_Alena',           # Владелец операции
    'depends_on_past': False,            # Зависимость от прошлых запусков
    'retries': 2,                        # Кол-во попыток выполнить DAG
    'retry_delay': timedelta(minutes=5), # Промежуток между перезапусками
    'start_date': datetime(2024, 7, 22), # Дата начала выполнения DAG
}

schedule_interval = '0 11 * * *' # cron-выражение

@dag(default_args=default_args, schedule_interval=schedule_interval, catchup=False)
def kazakova_bot_report():
    @task
    # Выгружаем данные из бд
    def query():
        q = '''
            select  toDate(time) as date,
                    uniq(user_id) as dau,
                    countIf(action = 'like') as likes,
                    countIf(action = 'view') as views,
                    likes/views as ctr
            from simulator_20240620.feed_actions
            where toDate(time) between today()-7 and today()-1
            group by toDate(time)
            order by toDate(time)
                '''
        df = ph.read_clickhouse(q, connection=connection)
        return df
    
    @task
    # Выводим основные метрки за день
    def text_yesterday(df):
        my_token = '1987162789:AAFgHNqBv-v5VXPQcS0btoxtXECUvw8akMs'
        bot = telegram.Bot(token=my_token)
        chat_id = 428582124
        day = df['date'].loc[len(df)-1].strftime('%d/%m/%Y')
        dau = df['dau'].loc[len(df)-1]
        likes = df['likes'].loc[len(df)-1]
        views = df['views'].loc[len(df)-1]
        ctr = round(df['ctr'].loc[len(df)-1], 2)
        text = f'''
        Отчет за {day}
        Количество уникальных пользователей: {dau} 
        Количество лайков: {likes}
        Количество просмотров: {views}
        Коэффициент кликабельности: {ctr}'''
        bot.sendMessage(chat_id=chat_id, text=text)

    @task
    # Нарисуем dau, активность пользователей и ctr за неделю
    def figure_weeksmetrics(df):
        my_token = '1987162789:AAFgHNqBv-v5VXPQcS0btoxtXECUvw8akMs'
        bot = telegram.Bot(token=my_token)
        chat_id = 428582124
        #Текст
        yesterday = df['date'].loc[len(df)-1].strftime('%d/%m/%Y')
        seven_days_ago = df['date'].loc[0].strftime('%d/%m/%Y')
        msg = f'Недельный отчет c {seven_days_ago} по {yesterday}\n'
        bot.sendMessage(chat_id=chat_id, text=msg)
        
        # Нарисуем dau
        plt.subplots(figsize=(8, 5))
        sns.lineplot(df, x='date', y='dau', color='r')
        plt.grid()
        # добавим надписи
        plt.title('Уникальные пользователи', fontsize=16)
        plt.ylabel('dau', fontsize=13)
        plt.xlabel('date', fontsize=13)
        
        plot_object = io.BytesIO()
        plt.savefig(plot_object)
        plot_object.seek(0)
        plot_object.name = 'DAU.png'
        plt.close()
        bot.sendPhoto(chat_id=chat_id, photo=plot_object)
    
        # Нарисуем активность пользователей
        N = len(df['date'])
        ind = np.arange(N)  # the x locations for the groups
        width = 0.35       # the width of the bars
        date = df.loc[:, 'date'].astype('str')

        fig, ax = plt.subplots(figsize=(15, 5))
        likes_week = ax.bar(ind, df['likes'], width, color='pink')
        views_week = ax.bar(ind+width, df['views'], width, color='c')

        # добавим надписи
        ax.set_title('Активность пользователей', fontsize=16)
        ax.set_xticks(ind + width / 2)
        ax.set_xticklabels(date)

        ax.legend((likes_week[0], views_week[0]), ('Likes', 'Views'))
        # Рисуем кол-во лайков и просмотров над столбцом
        def autolabel(reaction):
            for i in reaction:
                height = i.get_height()
                ax.text(i.get_x() + i.get_width()/2., height,
                        '%d' % int(height),
                        ha='center', va='bottom')

        autolabel(likes_week)
        autolabel(views_week)
        
        plot_object = io.BytesIO()
        plt.savefig(plot_object)
        plot_object.seek(0)
        plot_object.name = 'likes and views.png'
        plt.close()
        bot.sendPhoto(chat_id=chat_id, photo=plot_object)
    
        # Нарисуем ctr
        plt.subplots(figsize=(8, 5))
        sns.lineplot(df, x='date', y='ctr', color='b')
        plt.grid()
        # добавим надписи
        plt.title('Кликабельность', fontsize=16)
        plt.ylabel('Коэффициент кликабельности', fontsize=13)
        plt.xlabel('date', fontsize=13)
        
        plot_object = io.BytesIO()
        plt.savefig(plot_object)
        plot_object.seek(0)
        plot_object.name = 'ctr.png'
        plt.close()
        bot.sendPhoto(chat_id=chat_id, photo=plot_object)
    
    df = query()
    text_yesterday(df)
    figure_weeksmetrics(df)
    
kazakova_bot_report = kazakova_bot_report()