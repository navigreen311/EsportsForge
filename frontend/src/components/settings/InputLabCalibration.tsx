'use client';

import { useState } from 'react';

interface InputLabCalibrationProps {
  inputType: 'controller' | 'kbm' | 'fight-stick';
}

type TriggerSensitivity = 'light' | 'standard' | 'heavy';

const TITLES: Record<string, string> = {
  controller: 'Controller Calibration',
  kbm: 'KBM Calibration',
  'fight-stick': 'Fight Stick Calibration',
};

const triggerOptions: { value: TriggerSensitivity; label: string; description: string }[] = [
  { value: 'light', label: 'Light', description: 'Lower activation threshold' },
  { value: 'standard', label: 'Standard', description: 'Default trigger response' },
  { value: 'heavy', label: 'Heavy', description: 'Higher activation threshold' },
];

const pollingRateOptions: { value: number; label: string }[] = [
  { value: 500, label: '500hz' },
  { value: 1000, label: '1000hz' },
];

export default function InputLabCalibration({ inputType }: InputLabCalibrationProps) {
  // Controller state
  const [leftDeadzone, setLeftDeadzone] = useState(8);
  const [rightDeadzone, setRightDeadzone] = useState(5);
  const [triggerSensitivity, setTriggerSensitivity] = useState<TriggerSensitivity>('standard');
  const [vibration, setVibration] = useState(true);

  // KBM state
  const [mouseSensitivity, setMouseSensitivity] = useState(8);
  const [adsSensitivity, setAdsSensitivity] = useState(1.0);
  const [pollingRate, setPollingRate] = useState(1000);

  // Fight stick state
  const [bufferWindow, setBufferWindow] = useState(3);
  const [motionLeniency, setMotionLeniency] = useState(5);

  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
      {/* Header */}
      <div className="mb-6">
        <h3 className="text-sm font-bold text-dark-200">{TITLES[inputType]}</h3>
        <p className="text-xs text-dark-500 mt-1">
          These settings help InputLab accurately detect mechanical leakage vs. hardware variation
        </p>
      </div>

      <div className="space-y-5">
        {/* Controller Settings */}
        {inputType === 'controller' && (
          <>
            {/* Left Stick Deadzone */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-dark-300">Left Stick Deadzone</label>
                <span className="text-sm font-medium text-forge-400">{leftDeadzone}%</span>
              </div>
              <input
                type="range"
                min={0}
                max={30}
                value={leftDeadzone}
                onChange={(e) => setLeftDeadzone(Number(e.target.value))}
                className="w-full accent-forge-500"
              />
              <div className="flex justify-between text-xs text-dark-500 mt-1">
                <span>0%</span>
                <span>30%</span>
              </div>
            </div>

            {/* Right Stick Deadzone */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-dark-300">Right Stick Deadzone</label>
                <span className="text-sm font-medium text-forge-400">{rightDeadzone}%</span>
              </div>
              <input
                type="range"
                min={0}
                max={30}
                value={rightDeadzone}
                onChange={(e) => setRightDeadzone(Number(e.target.value))}
                className="w-full accent-forge-500"
              />
              <div className="flex justify-between text-xs text-dark-500 mt-1">
                <span>0%</span>
                <span>30%</span>
              </div>
            </div>

            {/* Trigger Sensitivity */}
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-3">
                Trigger Sensitivity
              </label>
              <div className="grid grid-cols-3 gap-3">
                {triggerOptions.map((option) => (
                  <button
                    key={option.value}
                    onClick={() => setTriggerSensitivity(option.value)}
                    className={`rounded-lg border p-3 text-left transition-all ${
                      triggerSensitivity === option.value
                        ? 'border-forge-500 bg-forge-500/10 ring-1 ring-forge-500'
                        : 'border-dark-600 bg-dark-800 hover:border-dark-500'
                    }`}
                  >
                    <p
                      className={`text-sm font-medium ${
                        triggerSensitivity === option.value
                          ? 'text-forge-400'
                          : 'text-dark-200'
                      }`}
                    >
                      {option.label}
                    </p>
                    <p className="text-xs text-dark-500 mt-0.5">{option.description}</p>
                  </button>
                ))}
              </div>
            </div>

            {/* Vibration Toggle */}
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-dark-300">Vibration</label>
                <p className="text-xs text-dark-500 mt-0.5">Haptic feedback during gameplay</p>
              </div>
              <button
                onClick={() => setVibration(!vibration)}
                className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors ${
                  vibration ? 'bg-forge-500' : 'bg-dark-600'
                }`}
              >
                <span
                  className={`pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow-sm transition-transform ${
                    vibration ? 'translate-x-5' : 'translate-x-0'
                  }`}
                />
              </button>
            </div>
          </>
        )}

        {/* KBM Settings */}
        {inputType === 'kbm' && (
          <>
            {/* Mouse Sensitivity */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-dark-300">Mouse Sensitivity</label>
                <span className="text-sm font-medium text-forge-400">{mouseSensitivity}</span>
              </div>
              <input
                type="range"
                min={1}
                max={20}
                value={mouseSensitivity}
                onChange={(e) => setMouseSensitivity(Number(e.target.value))}
                className="w-full accent-forge-500"
              />
              <div className="flex justify-between text-xs text-dark-500 mt-1">
                <span>1</span>
                <span>20</span>
              </div>
            </div>

            {/* ADS Sensitivity Multiplier */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-dark-300">ADS Sensitivity Multiplier</label>
                <span className="text-sm font-medium text-forge-400">{adsSensitivity.toFixed(1)}x</span>
              </div>
              <input
                type="range"
                min={5}
                max={20}
                value={adsSensitivity * 10}
                onChange={(e) => setAdsSensitivity(Number(e.target.value) / 10)}
                className="w-full accent-forge-500"
              />
              <div className="flex justify-between text-xs text-dark-500 mt-1">
                <span>0.5x</span>
                <span>2.0x</span>
              </div>
            </div>

            {/* Polling Rate */}
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-3">
                Polling Rate
              </label>
              <div className="grid grid-cols-2 gap-3">
                {pollingRateOptions.map((option) => (
                  <button
                    key={option.value}
                    onClick={() => setPollingRate(option.value)}
                    className={`rounded-lg border p-3 text-center transition-all ${
                      pollingRate === option.value
                        ? 'border-forge-500 bg-forge-500/10 ring-1 ring-forge-500'
                        : 'border-dark-600 bg-dark-800 hover:border-dark-500'
                    }`}
                  >
                    <p
                      className={`text-sm font-medium ${
                        pollingRate === option.value
                          ? 'text-forge-400'
                          : 'text-dark-200'
                      }`}
                    >
                      {option.label}
                    </p>
                  </button>
                ))}
              </div>
            </div>
          </>
        )}

        {/* Fight Stick Settings */}
        {inputType === 'fight-stick' && (
          <>
            {/* Buffer Window */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-dark-300">Buffer Window</label>
                <span className="text-sm font-medium text-forge-400">{bufferWindow} frames</span>
              </div>
              <input
                type="range"
                min={1}
                max={6}
                value={bufferWindow}
                onChange={(e) => setBufferWindow(Number(e.target.value))}
                className="w-full accent-forge-500"
              />
              <div className="flex justify-between text-xs text-dark-500 mt-1">
                <span>1 frame</span>
                <span>6 frames</span>
              </div>
            </div>

            {/* Motion Input Leniency */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-dark-300">Motion Input Leniency</label>
                <span className="text-sm font-medium text-forge-400">{motionLeniency}</span>
              </div>
              <input
                type="range"
                min={1}
                max={10}
                value={motionLeniency}
                onChange={(e) => setMotionLeniency(Number(e.target.value))}
                className="w-full accent-forge-500"
              />
              <div className="flex justify-between text-xs text-dark-500 mt-1">
                <span>1</span>
                <span>10</span>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Test Calibration Button */}
      <div className="mt-6">
        <button className="rounded-lg border border-forge-500 px-4 py-2 text-sm font-medium text-forge-400 transition-colors hover:bg-forge-500/10">
          Test Calibration
        </button>
      </div>
    </div>
  );
}
