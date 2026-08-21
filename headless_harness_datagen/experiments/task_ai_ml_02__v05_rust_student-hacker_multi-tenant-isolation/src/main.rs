use clap::{Parser, Subcommand};
use epoch_ledger::store::Store;
use epoch_ledger::tenant::TenantId;

#[derive(Parser)]
#[command(name = "epoch_ledger")]
#[command(about = "Offline‑first ML experiment journal with multi‑tenant isolation", long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Manage tenants
    Tenant {
        #[command(subcommand)]
        action: TenantAction,
    },
    /// Manage experiments inside a tenant
    Experiment {
        #[command(subcommand)]
        action: ExperimentAction,
    },
}

#[derive(Subcommand)]
enum TenantAction {
    /// Add a new tenant (creates isolated namespace)
    Add { name: String },
    /// List all tenants
    List,
}

#[derive(Subcommand)]
enum ExperimentAction {
    /// Record a new experiment result for a tenant
    Run {
        #[arg(short, long)]
        tenant: String,
        #[arg(short, long)]
        name: String,
        #[arg(short, long, default_value = "0")]
        score: f64,
    },
    /// List experiments for a tenant
    List { #[arg(short, long)] tenant: String },
    /// Promote the best experiment to champion (simple max score)
    PromoteChampion { #[arg(short, long)] tenant: String },
}

fn main() {
    let cli = Cli::parse();
    let store = Store::global();
    match cli.command {
        Commands::Tenant { action } => match action {
            TenantAction::Add { name } => {
                let id = store.add_tenant(&name);
                println!("Created tenant '{}' with id {}", name, id);
            }
            TenantAction::List => {
                for (id, name) in store.list_tenants() {
                    println!("{}: {}", id, name);
                }
            }
        },
        Commands::Experiment { action } => match action {
            ExperimentAction::Run { tenant, name, score } => {
                let tenant_id = store.get_tenant_by_name(&tenant);
                match tenant_id {
                    Some(id) => {
                        store.add_experiment(id, &name, score);
                        println!("Recorded experiment '{}' with score {} for tenant {}", name, score, tenant);
                    }
                    None => eprintln!("Tenant '{}' not found", tenant),
                }
            }
            ExperimentAction::List { tenant } => {
                let tenant_id = store.get_tenant_by_name(&tenant);
                match tenant_id {
                    Some(id) => {
                        for exp in store.list_experiments(id) {
                            println!("{} - score {:.2}", exp.name, exp.score);
                        }
                    }
                    None => eprintln!("Tenant '{}' not found", tenant),
                }
            }
            ExperimentAction::PromoteChampion { tenant } => {
                let tenant_id = store.get_tenant_by_name(&tenant);
                match tenant_id {
                    Some(id) => {
                        if let Some(champ) = store.promote_champion(id) {
                            println!("Champion for tenant {} is '{}' with score {:.2}", tenant, champ.name, champ.score);
                        } else {
                            println!("No experiments to promote for tenant {}", tenant);
                        }
                    }
                    None => eprintln!("Tenant '{}' not found", tenant),
                }
            }
        },
    }
}
