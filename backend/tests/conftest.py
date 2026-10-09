"""Force test isolation before any application module is imported."""
import os
os.environ["DATABASE_URL"] = "sqlite:////tmp/portal-tests.db"
os.environ["SEED_DEMO"] = "true"
os.environ["DEMO_ACCOUNTS_ENABLED"] = "true"
