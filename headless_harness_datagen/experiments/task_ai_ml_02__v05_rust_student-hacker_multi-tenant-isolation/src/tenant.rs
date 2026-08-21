use serde::{Deserialize, Serialize};

/// Identifier for a tenant. Newtype wrapper around usize for type safety.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct TenantId(pub usize);
