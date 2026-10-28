import React, { useState, useEffect } from 'react';
import { TabType, DatasetMeta } from './types';
import { DatasetService } from './services/api';

import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';

import { DashboardOverview } from './components/dashboard/DashboardOverview';
import { ChatInterface } from './components/chat/ChatInterface';
import { DataExplorer } from './components/datasets/DataExplorer';
import { DatasetUpload } from './components/datasets/DatasetUpload';
import { CleaningStudio } from './components/cleaning/CleaningStudio';
import { ColumnIntelligence } from './components/analytics/ColumnIntelligence';
import { SqlWorkspace } from './components/sql/SqlWorkspace';
import { StatisticalStudio } from './components/analytics/StatisticalStudio';
import { MLForecastingStudio } from './components/analytics/MLForecastingStudio';
import { ExportCenter } from './components/reports/ExportCenter';
import { DatabaseConnectors } from './components/connectors/DatabaseConnectors';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(false);
  
  const [datasets, setDatasets] = useState<DatasetMeta[]>([]);
  const [activeDatasetId, setActiveDatasetId] = useState<string | undefined>(undefined);
  const [activeDataset, setActiveDataset] = useState<DatasetMeta | undefined>(undefined);
  
  const [isUploadOpen, setIsUploadOpen] = useState<boolean>(false);
  const [chatInitialPrompt, setChatInitialPrompt] = useState<string | undefined>(undefined);

  useEffect(() => {
    loadDatasets();
  }, []);

  const loadDatasets = async () => {
    try {
      const res = await DatasetService.list();
      setDatasets(res.datasets || []);
      if (res.active_dataset_id) {
        setActiveDatasetId(res.active_dataset_id);
        const active = res.datasets.find((d: DatasetMeta) => d.id === res.active_dataset_id);
        setActiveDataset(active);
      } else if (res.datasets && res.datasets.length > 0) {
        setActiveDatasetId(res.datasets[0].id);
        setActiveDataset(res.datasets[0]);
      }
    } catch (e) {
      console.error("Failed to load datasets:", e);
    }
  };

  const handleSelectDataset = async (id: string) => {
    try {
      await DatasetService.setActive(id);
      setActiveDatasetId(id);
      const active = datasets.find((d) => d.id === id);
      setActiveDataset(active);
    } catch (e) {
      console.error(e);
    }
  };

  const handleDatasetUploaded = (newDs: DatasetMeta) => {
    setDatasets((prev) => [newDs, ...prev.filter((d) => d.id !== newDs.id)]);
    setActiveDatasetId(newDs.id);
    setActiveDataset(newDs);
  };

  const handleQuickSample = async (sampleType: string) => {
    try {
      const newDs = await DatasetService.generateSample(sampleType);
      handleDatasetUploaded(newDs);
    } catch (e) {
      console.error(e);
    }
  };

  const handleNavigateToChat = (prompt?: string) => {
    if (prompt) {
      setChatInitialPrompt(prompt);
    }
    setActiveTab('chat');
  };

  return (
    <div className="flex h-screen bg-[#09090b] text-[#f4f4f5] overflow-hidden font-sans">
      {/* Sidebar */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        collapsed={sidebarCollapsed}
        setCollapsed={setSidebarCollapsed}
        activeDataset={activeDataset}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Header */}
        <Header
          datasets={datasets}
          activeDataset={activeDataset}
          onSelectDataset={handleSelectDataset}
          onOpenUploadModal={() => setIsUploadOpen(true)}
          onQuickSample={handleQuickSample}
          onNewChat={() => handleNavigateToChat()}
        />

        {/* Tab Views */}
        <main className="flex-1 overflow-y-auto">
          {activeTab === 'overview' && (
            <DashboardOverview
              activeDataset={activeDataset}
              onNavigateToChat={handleNavigateToChat}
            />
          )}

          {activeTab === 'chat' && (
            <ChatInterface
              activeDataset={activeDataset}
              initialPrompt={chatInitialPrompt}
            />
          )}

          {activeTab === 'explorer' && (
            <DataExplorer
              activeDataset={activeDataset}
              onSelectSheet={async (sheet) => {
                // Reload sheet
                if (activeDataset) {
                  try {
                    // Re-read with selected sheet
                    const updated = await DatasetService.get(activeDataset.id);
                    setActiveDataset(updated);
                  } catch (e) {
                    console.error(e);
                  }
                }
              }}
            />
          )}

          {activeTab === 'cleaning' && (
            <CleaningStudio
              activeDataset={activeDataset}
              onDatasetUpdated={(ds) => {
                handleDatasetUploaded(ds);
              }}
            />
          )}

          {activeTab === 'formulas' && (
            <ColumnIntelligence
              activeDataset={activeDataset}
              datasets={datasets}
              onSelectDataset={handleSelectDataset}
            />
          )}

          {activeTab === 'sql' && (
            <SqlWorkspace
              activeDataset={activeDataset}
            />
          )}

          {activeTab === 'analytics' && (
            <StatisticalStudio
              activeDataset={activeDataset}
            />
          )}

          {activeTab === 'ml' && (
            <MLForecastingStudio
              activeDataset={activeDataset}
            />
          )}

          {activeTab === 'reports' && (
            <ExportCenter
              activeDataset={activeDataset}
            />
          )}

          {activeTab === 'connectors' && (
            <DatabaseConnectors
              onDatasetImported={handleDatasetUploaded}
            />
          )}
        </main>
      </div>

      {/* File Upload Modal */}
      <DatasetUpload
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onDatasetUploaded={handleDatasetUploaded}
      />
    </div>
  );
};

export default App;
