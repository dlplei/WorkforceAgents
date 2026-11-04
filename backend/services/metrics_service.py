"""
Workforce Operations Agent - Prometheus 可观测性与指标收集体系
集中定义与管理系统内部所有的业务监控指标：
1. LLM Token 吞吐量与调用耗时 (Token Throughput & Latency)
2. 生产级 Redis 缓存生命周期 (Hit / Miss / Invalidate / Clear)
3. 双轨安全护栏拦截与快速短路 (Guardrails Blocks & Latency)
4. 原生 HITL 人机协同门禁事件 (Approvals / Rejections / Modifications)
5. LangGraph 状态图各节点耗时追踪 (Graph Node Duration)
"""

from __future__ import annotations
import logging
from typing import Optional

logger = logging.getLogger("workforce.metrics")

try:
    from prometheus_client import (
        Counter,
        Gauge,
        Histogram,
        REGISTRY as DEFAULT_REGISTRY,
    )
    _HAVE_PROM = True
except ImportError:
    _HAVE_PROM = False

    class _NoopMetric:
        def labels(self, *args, **kwargs):
            return self
        def inc(self, amount: float = 1):
            pass
        def dec(self, amount: float = 1):
            pass
        def observe(self, amount: float):
            pass
        def set(self, amount: float):
            pass

    Counter = Histogram = Gauge = lambda *args, **kwargs: _NoopMetric()  # type: ignore
    DEFAULT_REGISTRY = None


def _create_counter(name: str, documentation: str, labelnames: tuple[str, ...] = ()) -> Counter:
    if not _HAVE_PROM:
        return Counter()
    try:
        return Counter(name, documentation, labelnames=labelnames)
    except ValueError:
        return DEFAULT_REGISTRY._names_to_collectors.get(name, Counter())


def _create_histogram(
    name: str,
    documentation: str,
    labelnames: tuple[str, ...] = (),
    buckets: tuple[float, ...] = (0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
) -> Histogram:
    if not _HAVE_PROM:
        return Histogram()
    try:
        return Histogram(name, documentation, labelnames=labelnames, buckets=buckets)
    except ValueError:
        return DEFAULT_REGISTRY._names_to_collectors.get(name, Histogram())


# ── 1. LLM 吞吐量与调用指标 ───────────────────────────────────────────
MET_LLM_TOKENS = _create_counter(
    "workforce_llm_tokens_total",
    "LLM 消耗的总 Token 数量，按方向与模型细分",
    labelnames=("direction", "model", "purpose"),
)

MET_LLM_CALLS = _create_counter(
    "workforce_llm_calls_total",
    "LLM API 调用次数",
    labelnames=("model", "outcome", "purpose"),
)

MET_LLM_LATENCY = _create_histogram(
    "workforce_llm_latency_seconds",
    "LLM API 调用耗时（秒）",
    labelnames=("model", "purpose"),
    buckets=(0.2, 0.5, 1.0, 2.0, 3.5, 5.0, 8.0, 15.0, 30.0),
)

# ── 2. Redis 缓存指标 ────────────────────────────────────────────────────
MET_REDIS_CACHE_EVENTS = _create_counter(
    "workforce_redis_cache_events_total",
    "Redis 缓存事件计数 (hit, miss, put, invalidate, clear)",
    labelnames=("event", "cache_type"),
)

# ── 3. Guardrails 护栏防御与短路指标 ───────────────────────────────────────
MET_GUARDRAIL_BLOCKS = _create_counter(
    "workforce_guardrail_blocks_total",
    "前置双轨护栏拦截与快速短路次数",
    labelnames=("reason", "check_type"),
)

MET_GUARDRAIL_LATENCY = _create_histogram(
    "workforce_guardrail_duration_seconds",
    "护栏审查耗时（秒）",
    labelnames=("check_type",),
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5),
)

# ── 4. HITL 人机协同门禁事件 ──────────────────────────────────────────────
MET_HITL_EVENTS = _create_counter(
    "workforce_hitl_events_total",
    "人机协同门禁触发与交互状态计数",
    labelnames=("event", "tool_name"),
)

# ── 5. LangGraph 状态机节点耗时 ───────────────────────────────────────────
MET_GRAPH_NODE_DURATION = _create_histogram(
    "workforce_graph_node_duration_seconds",
    "LangGraph 状态图各节点执行耗时（秒）",
    labelnames=("node",),
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

def _init_default_metrics() -> None:
    """生产级指标零初始化：确保在无外部流量时，Prometheus 与 Grafana 也能展示基线 0 而非 No Data"""
    try:
        for direction in ("input", "output"):
            MET_LLM_TOKENS.labels(direction=direction, model="qwen-max", purpose="reasoning").inc(0)
        for outcome in ("ok", "error"):
            MET_LLM_CALLS.labels(model="qwen-max", outcome=outcome, purpose="reasoning").inc(0)
        for ev in ("hit", "miss", "put", "invalidate"):
            MET_REDIS_CACHE_EVENTS.labels(event=ev, cache_type="qa").inc(0)
        for reason in ("injection", "off_topic"):
            MET_GUARDRAIL_BLOCKS.labels(reason=reason, check_type="l1_regex").inc(0)
        for hitl_ev in ("triggered", "approved", "rejected"):
            MET_HITL_EVENTS.labels(event=hitl_ev, tool_name="submit_leave_request").inc(0)
    except Exception as e:
        logger.debug(f"Metrics zero-init note: {e}")

_init_default_metrics()


# ── 记录辅助函数 ──────────────────────────────────────────────────────────

def record_llm_usage(
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    model: str = "unknown",
    purpose: str = "reasoning",
    duration_seconds: Optional[float] = None,
    outcome: str = "ok",
) -> None:
    """记录 LLM 调用的 Token、计数及耗时"""
    try:
        if prompt_tokens > 0:
            MET_LLM_TOKENS.labels(direction="input", model=model, purpose=purpose).inc(prompt_tokens)
        if completion_tokens > 0:
            MET_LLM_TOKENS.labels(direction="output", model=model, purpose=purpose).inc(completion_tokens)

        MET_LLM_CALLS.labels(model=model, outcome=outcome, purpose=purpose).inc(1)

        if duration_seconds is not None and duration_seconds > 0:
            MET_LLM_LATENCY.labels(model=model, purpose=purpose).observe(duration_seconds)
    except Exception as e:
        logger.debug(f"Failed to record LLM metrics: {e}")


def record_redis_cache_event(event: str, cache_type: str = "private") -> None:
    """记录 Redis 缓存事件：hit / miss / put / invalidate / clear"""
    try:
        MET_REDIS_CACHE_EVENTS.labels(event=event, cache_type=cache_type).inc(1)
    except Exception as e:
        logger.debug(f"Failed to record Redis cache metric: {e}")


def record_guardrail_block(reason: str, check_type: str = "l1_regex") -> None:
    """记录护栏拦截与快速短路事件"""
    try:
        MET_GUARDRAIL_BLOCKS.labels(reason=reason, check_type=check_type).inc(1)
    except Exception as e:
        logger.debug(f"Failed to record guardrail block metric: {e}")


def record_guardrail_latency(check_type: str, duration_seconds: float) -> None:
    """记录护栏审查耗时"""
    try:
        MET_GUARDRAIL_LATENCY.labels(check_type=check_type).observe(duration_seconds)
    except Exception as e:
        logger.debug(f"Failed to record guardrail latency metric: {e}")


def record_hitl_action(event: str, tool_name: str = "unknown") -> None:
    """记录 HITL 事件：triggered / approved / rejected / modified"""
    try:
        MET_HITL_EVENTS.labels(event=event, tool_name=tool_name).inc(1)
    except Exception as e:
        logger.debug(f"Failed to record HITL metric: {e}")


def record_node_duration(node_name: str, duration_seconds: float) -> None:
    """记录 LangGraph 状态图节点耗时"""
    try:
        MET_GRAPH_NODE_DURATION.labels(node=node_name).observe(duration_seconds)
    except Exception as e:
        logger.debug(f"Failed to record graph node duration metric: {e}")

