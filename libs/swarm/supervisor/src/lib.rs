use pyo3::prelude::*;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct AgentState {
    pub id: String,
    pub confidence: f64,
    pub latency: f64,
    pub activity: String,
}

#[pyclass]
pub struct MetaSupervisor {
    agents: HashMap<String, AgentState>,
}

#[pymethods]
impl MetaSupervisor {
    #[new]
    pub fn new() -> Self {
        MetaSupervisor {
            agents: HashMap::new(),
        }
    }

    pub fn update_agent(&mut self, state_json: String) -> PyResult<()> {
        let state: AgentState = serde_json::from_str(&state_json)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Invalid JSON: {}", e)))?;
        self.agents.insert(state.id.clone(), state);
        Ok(())
    }

    pub fn decide_handoff(&self, current_agent_id: String) -> PyResult<Option<String>> {
        // Meta-reasoning logic: find the agent with highest confidence and lowest relative latency
        // weighting based on some simple heuristics for "proactive coordination"
        
        let current = match self.agents.get(&current_agent_id) {
            Some(a) => a,
            None => return Ok(None),
        };

        if current.confidence > 0.8 {
            return Ok(None); // Current agent is doing well
        }

        let mut best_agent = None;
        let mut max_score = -1.0;

        for (id, state) in &self.agents {
            if id == &current_agent_id {
                continue;
            }

            // Score: confidence / (latency + 0.1)
            let score = state.confidence / (state.latency + 0.1);
            if score > max_score {
                max_score = score;
                best_agent = Some(id.clone());
            }
        }

        Ok(best_agent)
    }

    pub fn get_swarm_status(&self) -> PyResult<String> {
        serde_json::to_string(&self.agents)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))
    }
}

#[pymodule]
fn swarm_supervisor(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<MetaSupervisor>()?;
    Ok(())
}
