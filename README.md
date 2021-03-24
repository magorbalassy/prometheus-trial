# Prometheus demo

## Overview
---
A Prometheus usage demo. Analyze Rsync server logs and create metrics from it.


## Additional resources
---
`pip install prometheus-client`



## Metrics
---
I've setup metrics for the size, duration and number of the Rsync events.  
**We define 3 metrics, duration, size, and nr of requests counter**
```
duration_summary = Summary('rsync_tasks_seconds', 'Duration of rsync tasks',
                 ['source', 'dataset'])

size_summary = Summary('rsync_tasks_size', 'Size of rsync tasks',
                 ['source', 'dataset'])    
event_counter = Counter('rsync_requests', 'Number of requests received and finished')
```

Counter : `rsync_requests_total`  
Sizes which are 0 are attempts to fetch non-existing rsync endpoints.

## Possible other metrics
---
Important metrics to monitor would be latency, traffic, errors, and saturation.
- we could measure the number of errors (events without start or end or interpretable error messages)
- we could set up metrics for the server (disk i/o) or network load, etc.v
