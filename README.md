# Conn
Open several connections for HTTP/HTTPS load test. For the list of options, try `./conn.py --help`.

## Examples - Single URL

* Test a single URL with 10 simultaneous threads on a single process.

    Requests: **10**; Max Simultaneous Requests: **10**

        ./conn.py -i http://example.com -t 10

* Test a single URL with 10 simultaneous threads on a single process and repeat the process 3 times.
    Note each process will only open after the previous one finished (All 10 threads must end).

    Requests: **30**; Max Simultaneous Requests: **10**

        ./conn.py -i http://example.com -t 10 -r 3
    
* Test a single URL with 10 simultaneous threads per process (up to 5 processes. This is limited by `-r` if defined).

    Requests: **50**; Max Simultaneous Requests: **50**

        ./conn.py -i http://example.com -t 10 -p 5

* Test a single URL with 10 simultaneous threads per process (up to 5 simultaneous processes and a total of 7).

    Requests: **70**; Max Simultaneous Requests: **50**

        ./conn.py -i http://example.com -t 10 -p 5 -r 7
    
    When `-r` is less than `-p`, the number of simultaneous processes will be limited by `-r`.
    
## Examples - Multiple URLs

Create a file with one URL per line (`example.txt`) and add `-f` option. *The URLs in this file are accessed in a cycle*.
So, if the user requests 10 connections and the file has 8 items, the first two items will be replayed.

* Open the first 10 URLs on separated threads

        ./conn.py -f -i example.txt -t 10
    
* When opening multiple processes, each one will read the list from the beginning so the first command below
will test the first 10 URLs 5 times while the second one will offset each process by 10 elements, testing a
total of 50 different URLs (if the file have that many items).

        ./conn.py -f -i example.txt -t 10 -p 5
        ./conn.py -f -i example.txt -t 10 -p 5 --offset 10

* Skip the first 50 elements of the list (Actually they will be moved to the end of the list because of
the cycle behavior):

        ./conn.py -fi example.txt -t 10 --skip 50

* Shuffle the list of URLs before each process start.

        ./conn.py -fi example.txt -t 10 -p 5 --shuffle

    Although this option can be used alongside with `--skip` and `--offset`, it makes little sense because the list
    order is now random.
