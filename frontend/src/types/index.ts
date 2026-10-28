export type TabType = 
  | 'overview' 
  | 'chat' 
  | 'explorer' 
  | 'cleaning' 
  | 'formulas' 
  | 'sql' 
  | 'analytics' 
  | 'ml' 
  | 'reports' 
  | 'connectors' 
  | 'settings';

export interface ColumnProfile {
  name: string;
  inferred_type: string;
  raw_dtype: string;
  role: 'measure' | 'dimension' | 'date' | 'identifier';
  missing_count: number;
  missing_percentage: number;
  distinct_count: number;
  is_primary_key_candidate: boolean;
  sample_values: any[];
  stats: {
    min?: number;
    max?: number;
    mean?: number;
    median?: number;
    std?: number;
  };
}

export interface QualitySummary {
  overall_score: number;
  completeness_score: number;
  uniqueness_score: number;
  consistency_score: number;
  total_rows: number;
  total_columns: number;
  duplicate_rows: number;
  duplicate_percentage: number;
  total_missing_cells: number;
  missing_cells_percentage: number;
}

export interface Recommendation {
  type: string;
  title: string;
  description: string;
  chart_type?: string;
  x_axis?: string;
  y_axis?: string;
  target_column?: string;
  date_column?: string;
  action?: string;
}

export interface DatasetMeta {
  id: string;
  table_name: string;
  filename: string;
  file_path: string;
  file_size_bytes: number;
  format: string;
  selected_sheet?: string;
  available_sheets: string[];
  row_count: number;
  column_count: number;
  created_at: number;
  last_updated_at?: number;
  last_action?: string;
  has_multiple_sheets?: boolean;
  profile: {
    table_name: string;
    row_count: number;
    column_count: number;
    columns: ColumnProfile[];
    candidate_primary_keys: string[];
    candidate_measures: string[];
    candidate_dimensions: string[];
    candidate_dates: string[];
    quality_summary: QualitySummary;
    recommendations: Recommendation[];
  };
}

export interface KPICard {
  id?: string;
  label: string;
  value: any;
  formatted_value: string;
  change_pct?: string;
  trend?: 'up' | 'down' | 'neutral';
  highlight?: boolean;
}

export interface DashboardChart {
  id: string;
  type: 'bar' | 'line' | 'area' | 'donut' | 'scatter' | 'histogram';
  title: string;
  description?: string;
  data: any[];
  x_key?: string;
  y_keys?: string[];
  name_key?: string;
  value_key?: string;
  play_key?: string;
  color?: string;
}

export interface DashboardConfig {
  id: string;
  dataset_id: string;
  title: string;
  kpis: KPICard[];
  charts: DashboardChart[];
  filters: Array<{
    column: string;
    label: string;
    type: string;
    options: string[];
  }>;
  available_dimensions: string[];
  available_measures: string[];
}

export interface VerificationTrace {
  formula?: string;
  sql?: string;
  execution_engine?: string;
  rows_processed?: number;
  execution_time_ms?: number;
  filter?: string;
  correlation?: number;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  timestamp: string;
  text: string;
  kpis?: KPICard[];
  chart?: {
    type: string;
    title: string;
    data: any[];
    x_key?: string;
    y_key?: string;
    play_key?: string;
  };
  narrative?: {
    executive_summary?: string;
    what_happened?: string;
    magnitude_of_change?: string;
    top_contributors?: string;
    risks_and_anomalies?: string;
    recommended_actions?: string;
  };
  verification?: VerificationTrace;
  suggested_followups?: string[];
  requires_action?: boolean;
  action_type?: string;
  cleaning_preview?: any;
}

export interface FormulaFunctionInfo {
  name: string;
  family: string;
  syntax: string;
  description: string;
  status: 'fully_supported' | 'partially_supported' | 'unsupported';
}
