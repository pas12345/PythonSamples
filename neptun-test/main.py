import time
import requests
from osiris.core.azure_client_authorization import ClientAuthorization
tenant_id = 'f7619355-6c67-4100-9a78-1847f30742e2'
client_id = 'dd7b1bd3-06d6-4ea2-9cd6-2716eabfdb90'
client_secret = 'KXV+234(ok123456'
egress_api = 'https://dp-prod.westeurope.cloudapp.azure.com/osiris-egress'
neptun_1h = '0d80b6fc-fcfb-4848-1153-08d925bcbaf2'

def main():
    credential = ClientAuthorization(tenant_id, client_id, client_secret)
    def test_call(url):
        token = credential.get_access_token()
        headers = {'Authorization': token}
        time_start = time.time()
        resp = requests.get(url, headers=headers)
        time_total = time.time() - time_start
        print(resp.content)
        print(f'Total time: {time_total}\n')
    def case_get_all_available_coords_for_weather_type():
        print('>>> Get available coordinates for `radiation_diffus` type')
        url = 'http://127.0.0.1:8000/dmi/radiation_diffus/'
        test_call(url)
    def case_get_all_available_years_for_weather_type_and_coords():
        print('>>> Get available years for `radiation_diffus` at coordinates xx')
        url = 'http://127.0.0.1:8000/dmi/radiation_diffus/57.89/10.69/'
        test_call(url)
    def case_get_file_from_type_and_coord_dataset():
        print('>>> Get 2018 `radiation_diffus` file from specific coordinate')
        url = 'http://127.0.0.1:8000/dmi/radiation_diffus/57.89/10.69/2018'
        test_call(url)
    def case_get_file_from_datetime_and_type_dataset():
        print('>>> Get `radiation_diffus` file from specific datetime')
        url = 'http://127.0.0.1:8000/dmi/2018/01/4/0/radiation_diffus'
        test_call(url)

    #case_get_all_available_coords_for_weather_type()
    #case_get_all_available_years_for_weather_type_and_coords()
    #case_get_file_from_type_and_coord_dataset()
    #case_get_file_from_datetime_and_type_dataset()


    url = f'{egress_api}/{neptun_1h}/json'

    test_call(url)


if __name__ == '__main__':
    main()