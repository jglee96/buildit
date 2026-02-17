-- buildit database schema (policy-versioned architecture engine)
-- Compatible with PostgreSQL 16+

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    name TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    name TEXT NOT NULL,
    country_code TEXT NOT NULL,
    jurisdiction_code TEXT NOT NULL,
    occupancy_type TEXT NOT NULL,
    site_geojson JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_projects_jurisdiction ON projects (country_code, jurisdiction_code);

CREATE TABLE IF NOT EXISTS project_requirements (
    id UUID PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    key TEXT NOT NULL,
    min_value DOUBLE PRECISION,
    max_value DOUBLE PRECISION,
    required_value DOUBLE PRECISION,
    unit TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(project_id, key)
);

CREATE TABLE IF NOT EXISTS project_aesthetic_inputs (
    id UUID PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    content TEXT NOT NULL,
    reference_url TEXT,
    weight DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rule_sets (
    id UUID PRIMARY KEY,
    country_code TEXT NOT NULL,
    jurisdiction_code TEXT NOT NULL,
    category TEXT NOT NULL,
    version TEXT NOT NULL,
    source_url TEXT NOT NULL,
    source_hash TEXT,
    published_at TIMESTAMPTZ NOT NULL,
    effective_from DATE NOT NULL,
    effective_to DATE,
    status TEXT NOT NULL CHECK (status IN ('draft', 'active', 'deprecated')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(country_code, jurisdiction_code, category, version)
);

CREATE INDEX IF NOT EXISTS idx_rule_sets_effective
    ON rule_sets (country_code, jurisdiction_code, category, effective_from, effective_to, status);

CREATE TABLE IF NOT EXISTS rule_definitions (
    id UUID PRIMARY KEY,
    rule_set_id UUID NOT NULL REFERENCES rule_sets(id) ON DELETE CASCADE,
    rule_key TEXT NOT NULL,
    rule_type TEXT NOT NULL CHECK (rule_type IN ('hard', 'soft')),
    expression JSONB NOT NULL,
    priority INTEGER NOT NULL DEFAULT 100,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rule_definitions_ruleset ON rule_definitions (rule_set_id, priority);

CREATE TABLE IF NOT EXISTS project_rule_snapshots (
    id UUID PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    evaluation_date DATE NOT NULL,
    frozen_rule_set_ids UUID[] NOT NULL,
    frozen_rule_definition_ids UUID[] NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_project_rule_snapshots_project
    ON project_rule_snapshots (project_id, evaluation_date);

CREATE TABLE IF NOT EXISTS design_runs (
    id UUID PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    snapshot_id UUID NOT NULL REFERENCES project_rule_snapshots(id),
    objective TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('queued', 'running', 'completed', 'failed')),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS design_options (
    id UUID PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES design_runs(id) ON DELETE CASCADE,
    rank INTEGER NOT NULL,
    option_type TEXT NOT NULL,
    score DOUBLE PRECISION NOT NULL,
    parameters JSONB NOT NULL,
    checks JSONB NOT NULL,
    mesh_payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS solar_results (
    id UUID PRIMARY KEY,
    option_id UUID NOT NULL REFERENCES design_options(id) ON DELETE CASCADE,
    timestamp_utc TIMESTAMPTZ NOT NULL,
    sun_altitude DOUBLE PRECISION NOT NULL,
    sun_azimuth DOUBLE PRECISION NOT NULL,
    insolation_kwh_m2 DOUBLE PRECISION NOT NULL,
    shadow_ratio DOUBLE PRECISION NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_solar_results_option_time ON solar_results (option_id, timestamp_utc);
