import Fetch_Scripts.get_nbm as nbm
import Fetch_Scripts.get_href as href
import Fetch_Scripts.get_refs as refs
import os
import time
from concurrent.futures import ThreadPoolExecutor

MAX_THREADS = 10

# Maybe add multithread runtime to speed this process up too, might need to see if it will or not
def fetch_all():
    nbm.main()
    href.main()
    refs.main()

    

if __name__ == "__main__":
   with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = [
            executor.submit(nbm.main),
            executor.submit(href.main),
            executor.submit(refs.main)
        ]
        for future in futures:
            future.result()