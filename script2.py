import pandas as pd
from pathlib import Path
import numpy as np
from datetime import datetime
from typing import List

FOLDERS_TO_CHECK = {'Bets': Path('bets'), 'Payments': Path('payments')}


def get_data_from_path(path: Path) -> pd.DataFrame:
    """
        Reads and concatenates all CSV files in the specified path.

        Args:       path: The path containing the CSV files.

        Returns:    A DataFrame containing the concatenated data from the CSV files.
    """
    files_in_path = path.glob('*.csv')
    dfs = []
    for file in files_in_path:
        dfs.append(pd.read_csv(file))
    return pd.concat(dfs, ignore_index=True)


def convert_to_numeric(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """
        Converts specified columns in a DataFrame to numeric data type.

        Args:       df: The DataFrame to convert columns in.
                    columns: A list of column names to convert.

        Returns:    pd.DataFrame with converted columns
    """
    for column in columns:
        df[column] = pd.to_numeric(df[column], errors='coerce', downcast='integer')
    return df


def convert_currency(amount: float, currency: str, target_currency: str) -> float:
    """
        Converts an amount from one currency to another.
        For now it works only with USD, EUR currencies.

        Args:      amount: The amount to convert.
                   currency: The currency of the amount.
                   target_currency: The target currency to convert to.

        Returns:   The converted amount.
    """
    if currency == target_currency:
        return amount
    else:
        return amount / 1.07


def date_handling(date_str: str) -> str:
    """
        Created for formatting "DDMMYYYY ..." type of date to "DD/MM/YYYY ..."

        Args:      date_str: The date string in the original format.
        Returns:   The modified date string.
    """
    return date_str[:2] + '/' + date_str[2:4] + '/' + date_str[4:]


def task1(payments_df: pd.DataFrame, bets_df: pd.DataFrame) -> pd.DataFrame:
    """
        Based on the data in the 'payments' and 'bets' folders, finds a customers who performed the following
        sequence of operations:
            1)Deposit;
            2) Bet for an amount within +/- 10% of the deposit;
            3) Withdrawal within an hour from the deposit using a different system than the deposit.

        Args:      payments_df: The DataFrame containing payment data.
                   bets_df: The DataFrame containing bet data.

        Returns:   A DataFrame containing the results of task.
    """

    grouped = payments_df.groupby('player_id')
    columns = ['player_id',
               'deposit_time',
               'bet_time',
               'withdrawal_time',
               'bet_result',
               'deposit_amount, EUR',
               'bet_amount, EUR']
    result = pd.DataFrame(columns=columns)

    for player_id, group in grouped:

        for i in range(len(group) - 1):

            current_row = group.iloc[i]
            next_row = group.iloc[i + 1]

            time_diff = next_row['Date'] - current_row['Date']
            if (current_row['transaction_type'] == 'deposit') and \
                    (next_row['transaction_type'] in ['withdrawal']) and \
                    (time_diff.total_seconds() <= 3600):

                bet = bets_df.loc[bets_df.accept_time.between(current_row['Date'],
                                                              next_row['Date']) &
                                  (bets_df.player_id == player_id) &
                                  (bets_df.amount_eur.between(current_row['paid_amount_eur'] * 0.9,
                                                              current_row['paid_amount_eur'] * 1.1))]

                if bet.shape[0] > 0:
                    new_rows = pd.DataFrame([[player_id,
                                             current_row['Date'],
                                             bet.iloc[0]['accept_time'],
                                             next_row['Date'],
                                             bet.iloc[0]['result'],
                                             current_row['paid_amount_eur'],
                                             bet.iloc[0]['amount_eur']]],
                                            columns=columns)
                    result = pd.concat([result, new_rows])
    return result


def task2(bets_df: pd.DataFrame) -> pd.DataFrame:
    """
        Based on the data in the 'bets' folder, find a customer who made 5 consecutive
        winning bets with a coefficient greater than 1.5.

        Args:      bets_df: The DataFrame containing bet data.

        Returns:   A DataFrame containing the results of task.
    """
    bets_df['coef'] = np.where(bets_df.result == 'Win', bets_df['payout'] / bets_df['amount'], 0)
    bets_df = bets_df.sort_values(['player_id', 'accept_time'])

    bets_df['result_coef_bool'] = np.where(bets_df['coef'] > 1.5, 1, 0)

    grouper = (bets_df.result_coef_bool != bets_df.result_coef_bool.shift()).cumsum()
    bets_df['winstreak'] = bets_df.result_coef_bool.groupby(grouper).cumsum()

    columns = 'player_id', 'end_streak_time', 'total_streak'
    result = pd.DataFrame(columns=columns)

    grouped = bets_df[bets_df['winstreak'] >= 5].groupby(['player_id'])
    for player_id, group in grouped:
        new_rows = pd.DataFrame([[player_id,
                                 group.loc[group['winstreak'].max() == group['winstreak'], 'accept_time'].values[0],
                                 group.loc[group['winstreak'].max() == group['winstreak'], 'winstreak'].values[0]]],
                                columns=columns)

        result = pd.concat([result, new_rows])
    return result


if __name__ == "__main__":
    payments = get_data_from_path(FOLDERS_TO_CHECK['Payments'])
    payments_columns = ['player_id', 'paid_amount']
    payments = convert_to_numeric(payments, payments_columns)

    payments['paid_amount_eur'] = payments.apply(lambda row: convert_currency(row['paid_amount'],
                                                                              row['paid_currency'],
                                                                              'EUR'), axis=1)
    payments['Date'] = pd.to_datetime(payments['Date'], errors='coerce')
    payments = payments.sort_values('Date')

    bets = get_data_from_path(FOLDERS_TO_CHECK['Bets'])
    bets_columns = ['player_id', 'amount']
    bets = convert_to_numeric(bets, bets_columns)

    bets['amount_eur'] = bets.apply(lambda row: convert_currency(row['amount'], row['currency'], 'EUR'), axis=1)

    bets['accept_time'] = np.where(bets['accept_time'].str.contains('/'),
                                   bets['accept_time'],
                                   bets['accept_time'].apply(lambda x: date_handling(str(x))))

    mask = bets['accept_time'].fillna('').str.contains('M')
    bets.loc[mask, 'accept_time'] = pd.to_datetime(bets.loc[mask, 'accept_time'],
                                                   format='%m/%d/%Y %I:%M %p',
                                                   dayfirst=True)

    bets['accept_time'] = pd.to_datetime(bets['accept_time'])
    bets = bets.sort_values('accept_time')

    now = datetime.now()
    task1(payments, bets).to_csv(f'result/result{now.strftime("%S%M%H%d%m%Y")}.csv')
    task2(bets).to_csv(f'result/bets_result{now.strftime("%S%M%H%d%m%Y")}.csv')
