# Прохождение практики в Карпов курсы
Во время практики я реализовала несколько мини-проектов, каждый из которых был направлен на развитие прикладных навыков аналитики данных и автоматизации процессов:

__1) Папка АB-тест:__ 
- Разработала код для проведения A/B-тестирования, целью которого было оценить эффективность новой функции;
- Реализовала расчет статистической мощности с использованием метода Монте-Карло для оценки вероятности выявления статистически значимых различий между группами, если такие различия действительно существуют  

__Стек:__ Python - numpy, scipy, matplotlib.

__2) Папка Automation:__
- Написала скрипт автоматической ежедневной отправки в виде отчета с основным метрикам приложения (DAU, лайки и просмотры) с ежедневной отправкой в Telegram-бот (Python: pandas, airflow, telegram API);
- Реализовала систему обнаружения аномалий в данных по количеству активных пользователей, лайков и просмотров постов. Для определения использовалась мера межквартального размаха (IQR) для мониторинга резких отклоенений.  

__Стек:__ Python - pandas, airflow, telegram API.

__3) Папка tests:__ 
- Провела A/A-тест для проверки идентичности распределения пользователей между двумя группами перед запуском A/B-теста;
- Реализовала АВ-тест, направленный на оценку эффективности внедрения нового алгоритма.  

__Стек:__ Python - scipy.stats, seaborn.
