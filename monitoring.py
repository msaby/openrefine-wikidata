import time

class Monitoring(object):
    def __init__(self, redis_client):
        self.req_rate_bucket_durations = [3600,60]
        self.r = redis_client

    def redis_bucket(self, duration):
        return ('openrefine_wikidata:monitoring:%d:%d' %
                (duration,time.time() // duration))

    def log_request(self, queries, processing_time):
        for duration in self.req_rate_bucket_durations:
            key = self.redis_bucket(duration)
            self.r.incr(key+':req_count')
            self.r.expire(key+':req_count', duration)
            self.r.incrby(key+':query_count', queries)
            self.r.expire(key+':query_count', duration)
            self.r.incrbyfloat(key+':processing_time', processing_time)
            self.r.expire(key+':processing_time', duration)

    def get_rates(self):
        rates = []
        for duration in self.req_rate_bucket_durations:
            key = self.redis_bucket(duration)
            req_count = float(self.r.get(key+':req_count') or 0)
            query_count = float(self.r.get(key+':query_count') or 0)
            processing_time = float(self.r.get(key+':processing_time') or 0)
            rates.append({
                'request_rate': req_count / duration,
                'query_rate': query_count / duration,
                'processing_time_per_query': processing_time / query_count if query_count > 0 else None,
                'measure_duration': duration,
            })
        return rates
