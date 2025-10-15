import Fetch_Scripts.get_nbm_multiple_grib as get_nbm
import Fetch_Scripts.getHrefProb as get_href
import os
from concurrent.futures import ThreadPoolExecutor

# Maybe add multithread runtime to speed this process up too, might need to see if it will or not
def fetch_all():
    get_nbm.main()
    get_href.main()

    

if __name__ == "__main__":
    fetch_all()