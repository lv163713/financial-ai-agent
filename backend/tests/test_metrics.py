from services.metrics import MetricsStore


def test_metrics_store_snapshot():
    store = MetricsStore()
    store.record_query(processing_ms=120, fallback_attempted=True, quality_passed=False)
    store.record_query(processing_ms=80, fallback_attempted=False, quality_passed=True)
    store.record_ingest_batch(total=4, success_count=3, failed_count=1)
    store.record_daily_job(failed=False)
    snapshot = store.snapshot()
    assert snapshot["query_total"] == 2
    assert snapshot["query_avg_processing_ms"] == 100
    assert snapshot["query_fallback_rate"] == 0.5
    assert snapshot["query_quality_pass_rate"] == 0.5
    assert snapshot["ingest_item_total"] == 4
    assert snapshot["ingest_success_rate"] == 0.75
    assert snapshot["daily_job_total"] == 1
