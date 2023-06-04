#   Test task. Data Engineer. Kovalenko Oleksandr

####  Python
  Script1.py під час роботи спостерігає за станом папок bets і payments, слідкуючи за додаванням/видаленням файлів. Процес перевірки стану відбувається кожної секунди. В разі помічених змін запускається script2.py за допомогою бібліотеки subprocess. 

  Script2.py спочатку завантажує дані з папок bets та payments в 2 окремі датафрейми. Так як деякі колонки(player_id, paid_amount, amount) мають різні типи значень(а саме int та str), що не дозволяє виконувати ряд процедур, вони перетворюються на int. 
  
  До обох датафреймів додається колонка (paid_amount_eur for payments and amount_eur for bets) для коректного порівняння цін в одній валюті. 
  
  Особливої уваги довелося приділити колонкам з датами, через різноманістність форматів. 
  
  Після необхідних перетворень виконується пошук гравця, який виконав таку послідовність дій:
  1) депозит;
  2) ставка на суму депозита +-10%;
  3) вивід через систему, відмінну від депозиту.
 
 Хотілося б відзначити такі проблеми:
 1) В таблиці payments колонка Status для всіх transaction_type='deposit' має статуси тільки: ['Approved', 'Issued', 'Failed']. За такою логікою, жоден депозит не був Завершеним(Completed), а в найкращому випадку міг бути тільки Підтвердженим(Accepted). В той самий час transaction_type=='withdrawal' і transaction_type=='write-off' можуть мати статус Завершено(Completed). На цьому етапі вже можна сказати, що ми знайдемо жодного гравця, який би відповідав початковим вимогам. Для того, щоб ми мали хоча б якісь результати, схожі на необхідні нам, я не додавав додаткову умову status='Completed'. 
 2) Порівнювання коштів з різними валютами було улагоджене повним переведенням до EUR. Застосований варіант не є найкращим, бо введене відношення USD-EUR є аткуальним тільки на цей момент. Коректніше було б використовувати онлайн значення через якусь АРІ, наприклад https://www.exchangerate-api.com/docs/python-currency-api. 
 3) "вивід через систему, відмінну від депозиту" могло б бути реалізовано через "withdrawal" та "write-off". Я вирішив застосовувати тільки "withdrawal", бо це буквально означає виведення коштів, тоді як "write-off" означає списання.

  Загальний алгоритм був виконаний таким чином: знайти депозит і виведення в рамках однієї години. Після цього вже знаходити, чи існує в даному проміжку ставка від даного гравця, яка б була +-10% від депозиту. Результат записується в датафрейм з такими колонками: ['player_id', 'deposit_time', 'bet_time', 'withdrawal_time', 'bet_result', 'deposit_amount, EUR', 'bet_amount, EUR'] і потім в файл з таймстемпом.
  
  Далі слідує завдання 2 з пошуку гравця, який виграв 5 ставок поспіль з коефіцієнтом більше 1.5.
  
  Алгоритм був побудований таким чином:
  1) Була створена колонка з коефіцієнтом. Для програних ставок було відразу виставлено 0.
  2) Була створена колонка result_coef_bool, яка містить 1, якщо coef>1.5 і 0 в інших випадках. Таким чином ми позначили ті рядки, які підходять під наші умови. Лишилося тільки відтворити winsterak, який би підраховував значення 1, які йдуть один за одним.
  3) Таблиця відсіюється, беручи тільки гравців, які мають вінстрік >=5.
  4) Дані записуються в результуючу таблицю і згодом в файл з таймстемпом.
  
  
  
  ####  SQL Task

  Code: 
```
WITH grouped_descr AS (
    SELECT pe_description, COUNT(*) AS count_issues
    FROM los_angeles_restaurant_health_inspections
    WHERE facility_name ILIKE '%cafe%' 
    OR facility_name ILIKE '%tea%' 
    OR facility_name ILIKE '%juice%'
    GROUP BY pe_description
    ORDER BY COUNT(*) DESC
),
third_count_iss AS (
    SELECT count_issues
    FROM grouped_descr
    OFFSET 2
    LIMIT 1
),
pe_desc_third_issued AS (
    SELECT pe_description
    FROM grouped_descr
    WHERE count_issues = (SELECT count_issues FROM third_count_iss)
)
SELECT facility_name
FROM los_angeles_restaurant_health_inspections AS la
WHERE pe_description IN (SELECT pe_description FROM pe_desc_third_issued)
and (facility_name ILIKE '%cafe%' 
OR facility_name ILIKE '%tea%' 
OR facility_name ILIKE '%juice%');
```

Пояснення до реалізації:
1) Було використано 3 CTE:

&emsp; 1.1) grouped_descr відображає pe_description та кількість випадків, де назва закладу має в собі "cafe", "tea", або "juice", згруповане по колонці pe_description.

&emsp; 1.2) third_count_iss містить кількість випадків для третьої за частотою pe_description з попередньої CTE. Для визначення третьої дані були відсортовані за частотою, відкинуті 2 перші рядки(OFFSET 2) і показано лише перше значення(LIMIT 1).

&emsp; 1.3) pe_desc_third_issued містить в собі назви pe_description, кількість випадків яких співпадає з кількістю випадків третьої за частотою pe_description(тобто числу з попередньої CTE)

2) Основний SELECT відображає назви закладів, pe_description яких є в переліку, який дає третя CTE (pe_desc_third_issued)
