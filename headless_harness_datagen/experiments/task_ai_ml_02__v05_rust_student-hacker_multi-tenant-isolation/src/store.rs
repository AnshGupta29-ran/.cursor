use std::collections::HashMap;
use std::sync::Mutex;
use once_cell::sync::Lazy;

use crate::tenant::TenantId;
use crate::experiment::Experiment;

/// Global in‑memory store. All data lives for the duration of the process.
pub struct Store {
    /// Maps tenant id to tenant name.
    tenants: Mutex<HashMap<TenantId, String>>, // id -> name
    /// Reverse lookup: name -> id.
    name_index: Mutex<HashMap<String, TenantId>>, // name -> id
    /// Experiments per tenant.
    experiments: Mutex<HashMap<TenantId, Vec<Experiment>>>,
    /// Counter for generating unique tenant ids.
    next_tenant_id: Mutex<usize>,
}

impl Store {
    /// Returns the singleton instance.
    pub fn global() -> &'static Store {
        static INSTANCE: Lazy<Store> = Lazy::new(|| Store {
            tenants: Mutex::new(HashMap::new()),
            name_index: Mutex::new(HashMap::new()),
            experiments: Mutex::new(HashMap::new()),
            next_tenant_id: Mutex::new(1),
        });
        &INSTANCE
    }

    /// Add a new tenant and return its id.
    pub fn add_tenant(&self, name: &str) -> TenantId {
        let mut id_lock = self.next_tenant_id.lock().unwrap();
        let id = TenantId(*id_lock);
        *id_lock += 1;
        self.tenants.lock().unwrap().insert(id, name.to_string());
        self.name_index.lock().unwrap().insert(name.to_string(), id);
        self.experiments.lock().unwrap().insert(id, Vec::new());
        id
    }

    /// List all tenants as (id, name) pairs.
    pub fn list_tenants(&self) -> Vec<(TenantId, String)> {
        self.tenants
            .lock()
            .unwrap()
            .iter()
            .map(|(&id, name)| (id, name.clone()))
            .collect()
    }

    /// Get a tenant id by its name.
    pub fn get_tenant_by_name(&self, name: &str) -> Option<TenantId> {
        self.name_index.lock().unwrap().get(name).copied()
    }

    /// Record a new experiment for a tenant.
    pub fn add_experiment(&self, tenant_id: TenantId, name: &str, score: f64) {
        let exp = Experiment {
            name: name.to_string(),
            score,
        };
        self.experiments
            .lock()
            .unwrap()
            .entry(tenant_id)
            .or_default()
            .push(exp);
    }

    /// List experiments for a tenant.
    pub fn list_experiments(&self, tenant_id: TenantId) -> Vec<Experiment> {
        self.experiments
            .lock()
            .unwrap()
            .get(&tenant_id)
            .cloned()
            .unwrap_or_default()
    }

    /// Promote the best experiment (highest score) to champion.
    /// Returns the champion experiment if any.
    pub fn promote_champion(&self, tenant_id: TenantId) -> Option<Experiment> {
        let mut exps = self
            .experiments
            .lock()
            .unwrap()
            .get_mut(&tenant_id)?;
        if exps.is_empty() {
            return None;
        }
        // Simple selection: max score.
        let champion = exps.iter().max_by(|a, b| a.score.partial_cmp(&b.score).unwrap());
        champion.cloned()
    }
}
