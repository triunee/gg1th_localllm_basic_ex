import { useState, useEffect } from 'react';
import SettingsPanel from './components/SettingsPanel';
import ChatWindow from './components/ChatWindow';
import { fetchModels } from './api/chatApi';
import { promptModes } from './api/promptModes';
import './App.css';

const DEFAULT_SETTINGS = {
  model: '',
  system_prompt: promptModes.basic.prompt,
  temperature: 0.4,
  top_p: 0.9,
  num_predict: 2000,
};

function App() {
  const [models, setModels] = useState([]);
  const [settings, setSettings] = useState(DEFAULT_SETTINGS);

  useEffect(() => {
    fetchModels()
      .then((list) => {
        setModels(list);
        if (list.length > 0) {
          setSettings((prev) => ({ ...prev, model: list[0] }));
        }
      })
      .catch(() => {
        setModels([]);
      });
  }, []);

  return (
    <div className="app-layout">
      <SettingsPanel
        models={models}
        settings={settings}
        onSettingsChange={setSettings}
      />
      <ChatWindow settings={settings} />
    </div>
  );
}

export default App;
