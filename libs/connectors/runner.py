import wasmtime
from typing import Any, Dict, Optional
import threading

class WasmConnectorRunner:
    """
    Executes third-party connectors as sandboxed WebAssembly modules
    using Wasmtime, isolated per tenant.
    """
    def __init__(self, engine_config: Optional[Dict[str, Any]] = None) -> None:
        config = wasmtime.Config()
        if engine_config:
            # Apply configuration for resource isolation etc.
            if engine_config.get("memory_limit"):
                 config.memory_max = engine_config["memory_limit"]
        
        self.engine = wasmtime.Engine(config)
        self.store = wasmtime.Store(self.engine)
        self.linker = wasmtime.Linker(self.engine)
        self.linker.define_wasi()
        self.store.set_wasi(wasmtime.WasiConfig())

    def run_connector(self, wasm_bytes: bytes, function_name: str, *args: Any) -> Any:
        """
        Loads and executes a Wasm module in a sandboxed environment.
        """
        module = wasmtime.Module(self.engine, wasm_bytes)
        instance = self.linker.instantiate(self.store, module)
        
        func = instance.exports(self.store).get(function_name)
        if not func:
            raise ValueError(f"Function {function_name} not found in Wasm module")
        
        return func(self.store, *args)

class TenantIsolationManager:
    """
    Manages Wasmtime runtimes isolated per tenant.
    """
    def __init__(self) -> None:
        self._tenants: Dict[str, WasmConnectorRunner] = {}
        self._lock = threading.Lock()

    def get_runner(self, tenant_id: str) -> WasmConnectorRunner:
        with self._lock:
            if tenant_id not in self._tenants:
                # Configure isolation parameters for this tenant
                config = {
                    "memory_limit": 512 * 1024 * 1024, # 512MB
                }
                self._tenants[tenant_id] = WasmConnectorRunner(config)
            return self._tenants[tenant_id]
