import axios from 'axios';
import { DatasetMeta, DashboardConfig, FormulaFunctionInfo } from '../types';

const api = axios.create({
  baseURL: '/api'
});

export const DatasetService = {
  list: async () => {
    const res = await api.get('/datasets/');
    return res.data;
  },
  get: async (id: string) => {
    const res = await api.get<DatasetMeta>(`/datasets/${id}`);
    return res.data;
  },
  setActive: async (id: string) => {
    const res = await api.post(`/datasets/active/${id}`);
    return res.data;
  },
  upload: async (file: File, sheetName?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (sheetName) {
      formData.append('sheet_name', sheetName);
    }
    const res = await api.post<DatasetMeta>('/datasets/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return res.data;
  },
  generateSample: async (sampleType: string = 'retail_sales', rowCount: number = 5000) => {
    const res = await api.post<DatasetMeta>('/datasets/sample', {
      sample_type: sampleType,
      row_count: rowCount
    });
    return res.data;
  },
  getData: async (datasetId: string, page = 1, pageSize = 50, sortBy?: string, sortDesc = false, search?: string) => {
    const params: any = { page, page_size: pageSize, sort_desc: sortDesc };
    if (sortBy) params.sort_by = sortBy;
    if (search) params.search = search;
    const res = await api.get(`/datasets/${datasetId}/data`, { params });
    return res.data;
  }
};

export const ChatService = {
  ask: async (query: string, sessionId = 'default_session', datasetId?: string) => {
    const res = await api.post('/chat/ask', {
      query,
      session_id: sessionId,
      dataset_id: datasetId
    });
    return res.data;
  }
};

export const DashboardService = {
  generate: async (datasetId?: string, title?: string, measures?: string[], dimensions?: string[]) => {
    const res = await api.post<DashboardConfig>('/dashboard/generate', {
      dataset_id: datasetId,
      title,
      selected_measures: measures,
      selected_dimensions: dimensions
    });
    return res.data;
  }
};

export const CleaningService = {
  quality: async (datasetId: string) => {
    const res = await api.get(`/cleaning/quality/${datasetId}`);
    return res.data;
  },
  reset: async (datasetId: string) => {
    const res = await api.post(`/cleaning/reset/${datasetId}`);
    return res.data;
  },
  previewDuplicates: async (datasetId?: string, subsetCols?: string[]) => {
    const res = await api.post('/cleaning/duplicates/preview', {
      dataset_id: datasetId,
      subset_columns: subsetCols
    });
    return res.data;
  },
  applyDuplicates: async (datasetId?: string, subsetCols?: string[], keep = 'first') => {
    const res = await api.post('/cleaning/duplicates/apply', {
      dataset_id: datasetId,
      subset_columns: subsetCols,
      keep
    });
    return res.data;
  },
  previewImpute: async (column: string, strategy = 'mean', fillValue?: any, datasetId?: string) => {
    const res = await api.post('/cleaning/impute/preview', {
      column,
      strategy,
      fill_value: fillValue,
      dataset_id: datasetId
    });
    return res.data;
  },
  applyImpute: async (column: string, strategy = 'mean', fillValue?: any, datasetId?: string) => {
    const res = await api.post('/cleaning/impute/apply', {
      column,
      strategy,
      fill_value: fillValue,
      dataset_id: datasetId
    });
    return res.data;
  },
  previewOutliers: async (column: string, method = 'iqr', threshold = 1.5, datasetId?: string) => {
    const res = await api.post('/cleaning/outliers/preview', {
      column,
      method,
      threshold,
      dataset_id: datasetId
    });
    return res.data;
  },
  applyOutliers: async (column: string, action = 'cap', method = 'iqr', threshold = 1.5, datasetId?: string) => {
    const res = await api.post('/cleaning/outliers/apply', {
      column,
      action,
      method,
      threshold,
      dataset_id: datasetId
    });
    return res.data;
  },
  standardizeDates: async (column: string, datasetId?: string) => {
    const res = await api.post(`/cleaning/dates/standardize?column=${encodeURIComponent(column)}${datasetId ? `&dataset_id=${datasetId}` : ''}`);
    return res.data;
  },
  normalizeText: async (column: string, operation = 'trim', datasetId?: string) => {
    const res = await api.post(`/cleaning/text/normalize?column=${encodeURIComponent(column)}&operation=${operation}${datasetId ? `&dataset_id=${datasetId}` : ''}`);
    return res.data;
  },
  undo: async (datasetId: string) => {
    const res = await api.post(`/cleaning/undo/${datasetId}`);
    return res.data;
  },
  redo: async (datasetId: string) => {
    const res = await api.post(`/cleaning/redo/${datasetId}`);
    return res.data;
  },
  getHistory: async (datasetId: string) => {
    const res = await api.get(`/cleaning/history/${datasetId}`);
    return res.data;
  }
};

export const FormulaService = {
  getRegistry: async () => {
    const res = await api.get('/formulas/registry');
    return res.data;
  },
  evaluate: async (formula: string, datasetId?: string) => {
    const res = await api.post('/formulas/evaluate', {
      formula,
      dataset_id: datasetId
    });
    return res.data;
  },
  mapNL: async (query: string, datasetId?: string) => {
    const res = await api.post('/formulas/map-natural-language', {
      query,
      dataset_id: datasetId
    });
    return res.data;
  }
};

export const SQLService = {
  execute: async (query: string, maxRows = 500, enforceReadonly = true) => {
    const res = await api.post('/sql/execute', {
      query,
      max_rows: maxRows,
      enforce_readonly: enforceReadonly
    });
    return res.data;
  },
  explain: async (query: string) => {
    const res = await api.post('/sql/explain', { query });
    return res.data;
  },
  tables: async () => {
    const res = await api.get('/sql/tables');
    return res.data;
  },
  schema: async (tableName: string) => {
    const res = await api.get(`/sql/schema/${tableName}`);
    return res.data;
  }
};

export const AnalyticsService = {
  automatic: async (datasetId: string, columns: string[], objective = 'auto', dateColumn?: string, dateFrom?: string, dateTo?: string) => {
    const res = await api.post('/analytics/automatic', {
      dataset_id: datasetId,
      columns,
      objective,
      date_column: dateColumn || undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined
    });
    return res.data;
  },
  descriptive: async (datasetId: string) => {
    const res = await api.get(`/analytics/descriptive/${datasetId}`);
    return res.data;
  },
  correlation: async (datasetId: string) => {
    const res = await api.get(`/analytics/correlation/${datasetId}`);
    return res.data;
  },
  pareto: async (datasetId: string, dimension: string, measure: string) => {
    const res = await api.get(`/analytics/pareto/${datasetId}`, {
      params: { dimension, measure }
    });
    return res.data;
  },
  anomalies: async (datasetId: string, measure: string, threshold = 3.0) => {
    const res = await api.get(`/analytics/anomalies/${datasetId}`, {
      params: { measure, threshold }
    });
    return res.data;
  }
};

export const MLService = {
  forecast: async (datasetId: string, targetMeasure: string, dateColumn: string, periodsAhead = 6) => {
    const res = await api.post('/ml/forecast', {
      dataset_id: datasetId,
      target_measure: targetMeasure,
      date_column: dateColumn,
      periods_ahead: periodsAhead
    });
    return res.data;
  },
  segmentation: async (datasetId: string, features: string[], nClusters = 3) => {
    const res = await api.post('/ml/segmentation', {
      dataset_id: datasetId,
      features,
      n_clusters: nClusters
    });
    return res.data;
  }
};

export const ReportsService = {
  getExcelUrl: (datasetId: string) => `/api/reports/export/excel/${datasetId}`,
  getCsvUrl: (datasetId: string) => `/api/reports/export/csv/${datasetId}`,
  exportPdf: async (datasetId: string, title: string, narrative?: any, kpis?: any[]) => {
    const res = await api.post(`/reports/export/pdf/${datasetId}`, {
      title,
      narrative,
      kpis
    }, { responseType: 'blob' });
    return res.data;
  }
};

export const ConnectorsService = {
  test: async (dbType: string, database: string, host = 'localhost', port?: number, user = '', password = '') => {
    const res = await api.post('/connectors/test', {
      db_type: dbType,
      database,
      host,
      port,
      username: user,
      password
    });
    return res.data;
  },
  import: async (dbType: string, database: string, tableName: string, host = 'localhost', port?: number, user = '', password = '', maxRows = 50000) => {
    const res = await api.post('/connectors/import', {
      db_type: dbType,
      database,
      table_name: tableName,
      host,
      port,
      username: user,
      password,
      max_rows: maxRows
    });
    return res.data;
  }
};
