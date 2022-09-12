import pytz
import json
import typing
import logging
import requests
import datetime as dt


class EDS:
    """
    Class to operate the EDS api.
    """

    def __init__(self, base_url: str = None, auth: str = None):
        """
        :param base_url: The base EDS url.
        :param auth: password.
        """
        self.base_url = base_url
        self.auth = auth

    def localtime_to_utc(datetime: dt.datetime, tzname: str) -> dt.datetime:
        """ Converts a localized or unaware datetime (that is assumed local) into UTC-time.

        :param datetime: Localized or unaware datetime
        :type datetime: dt.datetime
        :param tzname: String name of the time zone
        :type tzname: str
        :return: A TZ aware datetime in UTC
        :rtype: dt.datetime
        """
        tz = pytz.timezone(tzname)
        dt = tz.normalize(tz.localize(datetime))
        return dt.astimezone(pytz.utc)

    def sql_query(self, sql_query: str) -> typing.Dict:
        """ Executes the SQL query on the EDS "datastore_search_sql" endpoint and returns the response as a dictionary object.

        Raises `ValueError` if response has no records.
        Raises `RequestException` if response status code is non-OK.

        :param sql_query: The SQL query to execute on EDS.
        :type sql_query: str
        :return: Response dict. The `.['success']` will be True if the endpoint returned data as expected, and the data will be in `.['result']['records']`.
        :rtype: dict
        """
        sql_query = ' '.join(sql_query.split())  # Removes redundant whitespace in query
        logging.debug(self.base_url)
        logging.debug(sql_query)
        sql_dict = {'sql': sql_query}
        response = requests.get(self.base_url + "/datastore_search_sql", params=sql_dict)

        if response.ok:
            _json = response.json()

            # EDS error
            if _json.get('error'):
                raise requests.exceptions.RequestException(_json['error']['message'])

            # Sanity check: if there are no fields, it's probably a ValueError from user input
            if _json.get('result'):
                if len(_json['result']['records']) > 0:
                    return _json['result']['records']
            raise ValueError('Response contains no records. Make sure parameters are valid.')

        else:
            raise requests.exceptions.RequestException(response.reason)

    def sql_delete(self, resource_id: str, ids: dict) -> int:
        """ Delete records

        Raises `ValueError` if response has no records.
        Raises `RequestException` if response status code is non-OK.

        :param resource_id: The SQL query to execute on EDS.
        :type sql_query: str
        :ids: Response dict. The `.['success']` will be True if the endpoint returned data as expected, and the data will be in `.['result']['records']`.
        :rtype: dict
        """

        data = {
            "resource_id": resource_id,
            "force": True,
            "filters": {
                "_id": ids
            }
        }
        headers = {
                    'Content-type': 'application/json',
                    'Authorization': self.auth
        }
        response = requests.post(self.base_url + "/datastore_delete",
                                 headers=headers, data=json.dumps(data))

        if response.ok:
            _json = response.json()
            return 1

        # EDS error
        #if _json.get('error'):
        return -1
           #raise requests.exceptions.RequestException(_json['error']['message'])


    def sql_resource_id(self, alias: str) -> str:
        """ Executes the SQL query on the EDS "datastore_search_sql" endpoint and returns the response as a dictionary object.

        Raises `ValueError` if response has no records.
        Raises `RequestException` if response status code is non-OK.

        :param alias: The SQL query to execute on EDS.
        :type alias: str
        :return: Response str. The `.['success']` will be True if the endpoint returned data as expected, and the data will be in `.['result']['records']`.
        :rtype: str
        """
        sql_dict = {'id': alias}
        response = requests.get(self.base_url + "/package_show", params=sql_dict)

        if response.ok:
            _json = response.json()

            # EDS error
            if _json.get('error'):
                raise requests.exceptions.RequestException(_json['error']['message'])

            # Sanity check: if there are no fields, it's probably a ValueError from user input
            if _json.get('result'):
                return _json['result']['resources'][0]['id']

            raise ValueError('Response contains no resource.')

        else:
            raise requests.exceptions.RequestException(response.reason)
