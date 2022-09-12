import time
import typing
import logging
import pyodbc  # https://github.com/mkleehammer/pyodbc/wiki


class DbManager:

    def __init__(self, adb_hostname: str, oracle_sid: str, user: str = None, password: str = None):
        _odbc_connection_string = (f"DATA SOURCE={adb_hostname}:1521/adb;"
                                   f"PERSIST SECURITY INFO=True;USER ID={user};"
                                   f"password={password};Pooling=False;")


        self.conn = pyodbc.connect(_odbc_connection_string)
        self.conn.autocommit = True

    def query_rows(self, query: str, *query_params):
        cursor = self.conn.cursor()
        if query_params:
            cursor.execute(query, *query_params)
        else:
            cursor.execute(query)
        yield from cursor.fetchall()

    def call_stored_procedure(self,
                              procedure_name: str,
                              params: typing.List[tuple],
                              schema: str = 'dbo',
                              commit: bool = True,
                              fast_executemany: bool = False):
        logging.info(f'Executing {procedure_name} for {len(params)} parameter sets...')
        time_start = time.time()
        _params_string = ''
        if len(params[0]) == 1:
            _params_string = '?'
        elif len(params[0]) > 1:
            _params_string = '?,' * len(params[0])
        self._executemany(
            execute_string=f'{{CALL[{schema}].[{procedure_name}] ({_params_string})}}',
            params=params,
            commit=commit,
            fast_executemany=fast_executemany)
        time_result = time.time() - time_start
        logging.info(
            f'\t done in total {time_result:.2f} seconds, or {len(params) / time_result:.2f} paramsets per second')

    def _executemany(self, **kwargs):
        cursor = self.conn.cursor()
        old_autocommit = self.conn.autocommit
        old_fast_executemany = cursor.fast_executemany
        try:
            self.conn.autocommit = False
            cursor.fast_executemany = kwargs['fast_executemany']
            cursor.executemany(kwargs['execute_string'], kwargs['params'])
        except pyodbc.DatabaseError as e:
            self.conn.rollback()
            print(e)
        else:
            if kwargs['commit']:
                self.conn.commit()
        finally:
            self.conn.autocommit = old_autocommit
            cursor.fast_executemany = old_fast_executemany
