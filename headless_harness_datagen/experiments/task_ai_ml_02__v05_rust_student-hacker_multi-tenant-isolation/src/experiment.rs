use serde::{Deserialize, Serialize};

/// Simple experiment record stored per tenant.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Experiment {
    pub name: String,
    pub score: f64,
}
