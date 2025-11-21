import Fetch_Scripts.get_nbm as nbm
import Fetch_Scripts.get_href as href
import Fetch_Scripts.get_refs as refs
from concurrent.futures import ThreadPoolExecutor

MAX_THREADS = 10
def fetch_all():
    """Runs all model fetch scripts (NBM, HREF, REFS) and multithreads the processes"""

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