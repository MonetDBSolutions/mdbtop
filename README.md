`mdbtop` displays and logs system resource utilization for MonetDB process (mserver5, monetdbd)
## Dependencies
 - psutil
 - poetry

# Usage
From command line
```bash
mdbtop --interval=3 --log-file=<path> --dbpath=<database_path>
```
, or import it in your python code
```python
from mdbtop import Monitor
m = Monitor(interval=3)
try:
    m.start()
    # do some work
    #...
finaly:
    m.stop()

```
