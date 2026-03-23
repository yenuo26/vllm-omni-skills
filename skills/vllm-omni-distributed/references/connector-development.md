# OmniConnector Development

## When to Read This

Use this reference when the task is about building or modifying an OmniConnector backend, wiring it into stage configs, or validating connector behavior. For general distributed deployment and Ray setup, stay with `SKILL.md` and `ray-execution.md`.

## Connector Contract

Every connector must subclass `OmniConnectorBase` and implement:

- `put(from_stage, to_stage, put_key, data) -> (success, size, metadata)`
- `get(from_stage, to_stage, get_key, metadata=None) -> (data, size) | None`
- `cleanup(request_id)`
- `health()`
- `close()`

Choose connector transport based on the memory path and transport model: serializer-based object transfer is fine for control-heavy paths, while tensor-dominant high-throughput paths should minimize serialization and preserve raw tensor or buffer transport when possible.

Common implementation templates:

- `SharedMemoryConnector`: simplest metadata-driven local transport
- `MooncakeStoreConnector` or `YuanrongConnector`: store-backed serialized transport
- `MooncakeTransferEngineConnector`: role-aware high-performance transport with memory-pool and side-channel management

Register every new backend in `OmniConnectorFactory`. A connector is not usable from YAML until factory registration exists.

## Config Wiring

Define reusable connectors under top-level `runtime.connectors` and reference them from stage edges:

```yaml
runtime:
  connectors:
    my_connector:
      name: MyConnector
      extra:
        host: "127.0.0.1"

stage_args:
  - stage_id: 0
    output_connectors:
      to_stage_1: my_connector

  - stage_id: 1
    input_connectors:
      from_stage_0: my_connector
```

Keep edge-level config role-neutral. `load_omni_transfer_config()` resolves stage-level connector declarations into `(from_stage, to_stage)` edges, and `get_connectors_config_for_stage()` injects sender or receiver role for role-aware transports.

Important invariants:

- both sides of one edge must resolve to the same connector type
- undefined connector references should fail fast
- auto-created `SharedMemoryConnector` is a fallback for uncovered edges, not the main way to validate a new backend

## KV Cache Compatibility

KV transfer is configured separately through `omni_kv_config`, usually inside `engine_args`. If the connector is meant to support KV transfer, confirm it works with:

- `need_send_cache`
- `need_recv_cache`
- consistent put/get keys across stages
- receive timeout behavior

Do not assume stage payload forwarding and KV cache transfer use the same runtime fields.

## Validation Sequence

Validate connector work in this order:

1. serialization and basic `put/get`
2. factory creation and config loading
3. stage-to-stage payload flow
4. KV cache flow, if supported
5. backend-specific benchmark or environment checks

Mirror existing tests under `tests/distributed/omni_connectors/`, especially:

- `test_basic_connectors.py`
- `test_adapter_and_flow.py`
- `test_kv_flow.py`
- `test_omni_connector_configs.py`

For high-performance transports such as RDMA backends, also use:

- `test_mooncake_transfer_engine_buffer.py`
- `test_mooncake_transfer_engine_rdma.py`
- `benchmarks/distributed/omni_connectors/README.md`

## Review Checklist

- Could an existing connector solve the problem with config changes only?
- Is returned metadata stable and sufficient for `get()` or queue consumers?
- Are retries, timeouts, and cleanup explicit?
- Does teardown remain safe after partial initialization or repeated `close()`?
- Are performance claims backed by benchmarks rather than implementation intent?
