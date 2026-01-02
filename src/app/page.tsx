'use client';

import { useState } from 'react';
import { Upload, FileSpreadsheet, BarChart3, FileText, AlertCircle } from 'lucide-react';
import Papa from 'papaparse';
import { RegressionGraph, ResidualPlot } from '@/components/Graphs';

interface AnalysisResult {
  status: string;
  best_model: {
    name: string;
    model_key: string;
    r_squared: number;
    adj_r_squared: number;
    aic: number;
    equation: string;
    latex: string;
    parameters: number[];
    y_predicted?: number[];  // 회귀선 데이터
  };
  residuals: number[];
  data_info: {
    original_count: number;
    used_count: number;
    outliers_removed: number;
  };
  recommended_formulas: any[];
  alternative_models: any[];
}

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [results, setResults] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [xData, setXData] = useState<number[]>([]);
  const [yData, setYData] = useState<number[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>('auto');
  const [selectedTemplate, setSelectedTemplate] = useState<string>('none');

  const modelOptions = [
    { value: 'auto', label: '자동 선택 (AIC 기준)' },
    { value: 'linear', label: '선형 (Linear)' },
    { value: 'quadratic', label: '2차 다항식 (Quadratic)' },
    { value: 'cubic', label: '3차 다항식 (Cubic)' },
    { value: 'exponential', label: '지수 (Exponential)' },
    { value: 'logarithmic', label: '로그 (Logarithmic)' },
    { value: 'power', label: '거듭제곱 (Power)' },
  ];

  const templateOptions = [
    { value: 'none', label: '템플릿 없음 (기본 보고서)' },
    { value: '자유낙하와_포물체운동', label: '자유낙하와 포물체운동' },
    { value: '운동량과_충격량', label: '운동량과 충격량' },
    { value: '원운동과_구심력', label: '원운동과 구심력' },
    { value: '일과_에너지', label: '일과 에너지' },
    { value: '회전_운동', label: '회전 운동' },
    { value: '단순_조화_운동', label: '단순 조화 운동' },
    { value: '물리_진자_비틀림_진자', label: '물리 진자 / 비틀림 진자' },
    { value: '관성모멘트와_각운동량_보존', label: '관성모멘트와 각운동량 보존' },
    { value: '역학적_파동', label: '역학적 파동' },
    { value: '빛의_간섭과_회절', label: '빛의 간섭과 회절' },
    { value: '마이컬슨_간섭계', label: '마이컬슨 간섭계' },
    { value: '밀리컨_기름방울_실험', label: '밀리컨 기름방울 실험' },
    { value: '전자의_em', label: '전자의 e/m' },
    { value: '자기장', label: '자기장' },
    { value: '자기력', label: '자기력' },
    { value: '전자기유도', label: '전자기유도' },
    { value: '회로', label: '회로' },
    { value: '축전기와_전기용량', label: '축전기와 전기용량' },
  ];

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setResults(null);
      setError(null);
      setXData([]);
      setYData([]);
    }
  };

  const handleAnalyze = async () => {
    if (!file) return;

    setAnalyzing(true);
    setError(null);

    try {
      // Parse CSV file
      const text = await file.text();
      const parsed = Papa.parse(text, {
        header: true,
        dynamicTyping: true,
        skipEmptyLines: true,  // 빈 줄 건너뛰기
        delimiter: '',  // 자동 감지 (쉼표, 탭, 세미콜론 등)
      });

      // 경고만 표시하고 계속 진행 (데이터가 있는 경우)
      if (parsed.errors.length > 0 && parsed.data.length === 0) {
        throw new Error('CSV 파일 형식이 잘못되었습니다. 쉼표나 탭으로 구분된 CSV 파일을 사용해주세요.');
      }

      const data = parsed.data as any[];

      // 빈 객체 필터링
      const validData = data.filter(row => {
        return row && Object.keys(row).some(key => row[key] != null && row[key] !== '');
      });

      if (validData.length === 0) {
        throw new Error('CSV 파일에 유효한 데이터가 없습니다');
      }

      // Get column names
      const columns = Object.keys(validData[0]).filter(col => col && col.trim() !== '');
      if (columns.length < 2) {
        throw new Error(`최소 2개의 열이 필요합니다 (현재: ${columns.length}개)`);
      }

      // Extract X and Y data
      const xColumn = columns[0];
      const yColumn = columns[1];

      const xData = validData.map(row => parseFloat(row[xColumn])).filter(v => !isNaN(v));
      const yData = validData.map(row => parseFloat(row[yColumn])).filter(v => !isNaN(v));

      if (xData.length === 0 || yData.length === 0) {
        throw new Error(`유효한 숫자 데이터가 없습니다 (X: ${xData.length}개, Y: ${yData.length}개)`);
      }

      if (xData.length !== yData.length) {
        const minLength = Math.min(xData.length, yData.length);
        xData.length = minLength;
        yData.length = minLength;
      }

      // Store data for graphs
      setXData(xData);
      setYData(yData);

      // Call API (로컬 API 사용)
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          data: {
            x: xData,
            y: yData
          },
          options: {
            remove_outliers: false,
            manual_model: selectedModel === 'auto' ? null : selectedModel,
            return_chart_data: true
          }
        })
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('API Error Response:', errorText);

        // Try to parse structured error message
        try {
          const errorData = JSON.parse(errorText);
          if (errorData.detail && typeof errorData.detail === 'object') {
            // Structured error from backend
            const { error, message, solution, debug_info } = errorData.detail;
            let errorMsg = `❌ ${error || '오류 발생'}\n\n`;
            errorMsg += `${message || '알 수 없는 오류가 발생했습니다.'}\n\n`;
            if (solution) {
              errorMsg += `💡 해결 방법: ${solution}`;
            }
            if (debug_info && process.env.NODE_ENV === 'development') {
              errorMsg += `\n\n🔧 디버그: ${debug_info}`;
            }
            throw new Error(errorMsg);
          }
        } catch (parseError) {
          // Fallback to simple error message
          throw new Error(`API 오류 (${response.status}): ${errorText}`);
        }
      }

      const apiResult = await response.json();

      // 디버깅: API 응답 확인
      console.log('API Response:', apiResult);

      if (apiResult.status === 'success') {
        setResults(apiResult as AnalysisResult);
      } else {
        throw new Error(apiResult.message || 'API 분석 실패');
      }
    } catch (err: any) {
      console.error('Analysis failed:', err);
      setError(err.message || '분석 중 오류가 발생했습니다');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleGenerateReport = async () => {
    if (!results) return;

    try {
      setAnalyzing(true);
      setError(null);

      // 보고서 생성 API 호출
      const response = await fetch('/api/generate-report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          template: selectedTemplate,
          analysis: {
            model: results.best_model.name,
            equation: results.best_model.equation,
            r_squared: results.best_model.r_squared,
            adj_r_squared: results.best_model.adj_r_squared,
            aic: results.best_model.aic,
            parameters: results.best_model.parameters,
          },
          data: {
            x: xData,
            y: yData,
            y_predicted: results.best_model.y_predicted,
            residuals: results.residuals,
          },
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Word 문서 생성 실패');
      }

      // Blob으로 변환
      const blob = await response.blob();

      // 파일 다운로드
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;

      // 파일명 생성
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
      const templateName = selectedTemplate !== 'none' ? selectedTemplate : '실험보고서';
      a.download = `${templateName}_${timestamp}.docx`;

      document.body.appendChild(a);
      a.click();

      // 정리
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      // 성공 알림 (선택사항)
      alert('보고서가 생성되었습니다!');

    } catch (err: any) {
      console.error('Report generation failed:', err);
      setError(err.message || '보고서 생성 중 오류가 발생했습니다');
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-amber-50 via-white to-teal-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center gap-3">
            <div className="bg-sky-400 p-2 rounded-lg shadow-md">
              <FileText className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-orange-600 via-cyan-600 to-purple-600 bg-clip-text text-transparent">
              Lab Report AI
            </h1>
            <span className="text-sm text-gray-500 ml-2">실험 보고서 자동 생성</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Upload Section */}
          <div className="space-y-6">
            <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-100">
              <div className="flex items-center gap-3 mb-6">
                <Upload className="w-6 h-6 text-orange-600" />
                <h2 className="text-xl font-semibold text-gray-900">데이터 업로드</h2>
              </div>

              {/* File Upload */}
              <label className="block">
                <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-cyan-400 hover:bg-gradient-to-br hover:from-orange-50/30 hover:to-purple-50/30 transition-all cursor-pointer">
                  {file ? (
                    <div className="space-y-2">
                      <FileSpreadsheet className="w-12 h-12 mx-auto text-cyan-600" />
                      <p className="text-sm font-medium text-gray-900">{file.name}</p>
                      <p className="text-xs text-gray-500">{(file.size / 1024).toFixed(1)} KB</p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <Upload className="w-12 h-12 mx-auto text-gray-400" />
                      <p className="text-sm text-gray-600">
                        CSV 파일을 드래그하거나 클릭하여 업로드
                      </p>
                      <p className="text-xs text-gray-400">
                        실험 데이터 (시간, 속도, 거리 등)
                      </p>
                    </div>
                  )}
                  <input
                    type="file"
                    accept=".csv"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                </div>
              </label>

              {/* Model Selection */}
              {file && (
                <div className="mt-6">
                  <label className="block">
                    <div className="flex items-center gap-2 mb-2">
                      <BarChart3 className="w-5 h-5 text-purple-600" />
                      <span className="text-sm font-semibold text-gray-900">회귀 모델 선택</span>
                    </div>
                    <select
                      value={selectedModel}
                      onChange={(e) => setSelectedModel(e.target.value)}
                      className="w-full px-4 py-3 rounded-xl border-2 border-gray-300 focus:border-purple-500 focus:ring focus:ring-purple-200 transition-all bg-white text-gray-900 font-medium"
                    >
                      {modelOptions.map(option => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
              )}

              {/* Template Selection */}
              {file && (
                <div className="mt-6">
                  <label className="block">
                    <div className="flex items-center gap-2 mb-2">
                      <FileText className="w-5 h-5 text-orange-600" />
                      <span className="text-sm font-semibold text-gray-900">실험 템플릿 선택</span>
                    </div>
                    <select
                      value={selectedTemplate}
                      onChange={(e) => setSelectedTemplate(e.target.value)}
                      className="w-full px-4 py-3 rounded-xl border-2 border-gray-300 focus:border-orange-500 focus:ring focus:ring-orange-200 transition-all bg-white text-gray-900 font-medium"
                    >
                      {templateOptions.map(option => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                    <p className="text-xs text-gray-500 mt-1">
                      선택한 템플릿에 맞춰 보고서가 생성됩니다
                    </p>
                  </label>
                </div>
              )}

              {/* Analyze Button */}
              {file && (
                <button
                  onClick={handleAnalyze}
                  disabled={analyzing}
                  className="w-full mt-6 bg-rose-400 hover:bg-rose-500 text-white py-3 px-6 rounded-xl font-medium hover:shadow-lg hover:scale-105 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  <BarChart3 className="w-5 h-5" />
                  {analyzing ? '분석 중...' : '회귀 분석 시작'}
                </button>
              )}
            </div>

            {/* Features */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-xl p-4 border border-orange-200 shadow-sm hover:shadow-md hover:scale-105 transition-all">
                <div className="text-3xl mb-2">🤖</div>
                <h3 className="font-semibold text-sm text-orange-900">AI 자동 분석</h3>
                <p className="text-xs text-orange-600 mt-1">6개 물리 모델 자동 피팅</p>
              </div>
              <div className="bg-gradient-to-br from-cyan-50 to-cyan-100 rounded-xl p-4 border border-cyan-200 shadow-sm hover:shadow-md hover:scale-105 transition-all">
                <div className="text-3xl mb-2">📊</div>
                <h3 className="font-semibold text-sm text-cyan-900">실시간 그래프 생성</h3>
                <p className="text-xs text-cyan-600 mt-1">Plotly 인터랙티브 차트</p>
              </div>
              <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-4 border border-purple-200 shadow-sm hover:shadow-md hover:scale-105 transition-all">
                <div className="text-3xl mb-2">📝</div>
                <h3 className="font-semibold text-sm text-purple-900">AI 실험 보고서 생성</h3>
                <p className="text-xs text-purple-600 mt-1">Word/PDF 자동 작성</p>
              </div>
              <div className="bg-gradient-to-br from-pink-50 to-pink-100 rounded-xl p-4 border border-pink-200 shadow-sm hover:shadow-md hover:scale-105 transition-all">
                <div className="text-3xl mb-2">⚡</div>
                <h3 className="font-semibold text-sm text-pink-900">빠른 처리</h3>
                <p className="text-xs text-pink-600 mt-1">Vercel Serverless</p>
              </div>
            </div>
          </div>

          {/* Results Section */}
          <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-100">
            <div className="flex items-center gap-3 mb-6">
              <BarChart3 className="w-6 h-6 text-purple-600" />
              <h2 className="text-xl font-semibold text-gray-900">분석 결과</h2>
            </div>

            {!results && !analyzing && !error && (
              <div className="text-center py-12 text-gray-400">
                <FileSpreadsheet className="w-16 h-16 mx-auto mb-4 opacity-50" />
                <p>데이터를 업로드하고 분석을 시작하세요</p>
              </div>
            )}

            {analyzing && (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-gray-200 border-t-cyan-600 mb-4"></div>
                <p className="text-gray-600">AI가 데이터를 분석하는 중...</p>
              </div>
            )}

            {error && (
              <div className="bg-red-50 border-2 border-red-200 rounded-xl p-6">
                <div className="flex items-start gap-3 mb-2">
                  <AlertCircle className="w-6 h-6 text-red-600 flex-shrink-0 mt-1" />
                  <div className="flex-1">
                    <h3 className="font-semibold text-red-900 mb-2">오류 발생</h3>
                    <div className="text-sm text-red-700 whitespace-pre-line">{error}</div>
                  </div>
                </div>
              </div>
            )}

            {results && results.best_model && (
              <div className="space-y-6">
                <div className="bg-gradient-to-br from-orange-50 via-cyan-50 to-purple-50 rounded-xl p-6 border-2 border-transparent bg-clip-padding" style={{ borderImage: "linear-gradient(to right, rgb(249 115 22), rgb(6 182 212), rgb(168 85 247)) 1" }}>
                  <div className="text-sm text-gray-600 mb-1">최적 모델</div>
                  <div className="text-2xl font-bold text-gray-900">{results.best_model.name || 'Unknown'}</div>
                  {results.best_model.latex && (
                    <div className="mt-3 p-3 bg-white rounded-lg border border-gray-200">
                      <div className="text-xs text-gray-500 mb-1">피팅된 수식</div>
                      <div className="text-lg font-mono text-cyan-700">{results.best_model.latex}</div>
                    </div>
                  )}
                </div>

                <div className="grid grid-cols-3 gap-3">
                  <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg p-4 border-2 border-orange-300">
                    <div className="text-xs text-orange-700 mb-1 font-semibold">R²</div>
                    <div className="text-lg font-bold text-orange-800">
                      {results.best_model.r_squared != null ? results.best_model.r_squared.toFixed(4) : 'N/A'}
                    </div>
                  </div>
                  <div className="bg-gradient-to-br from-cyan-50 to-cyan-100 rounded-lg p-4 border-2 border-cyan-300">
                    <div className="text-xs text-cyan-700 mb-1 font-semibold">Adj R²</div>
                    <div className="text-lg font-bold text-cyan-800">
                      {results.best_model.adj_r_squared != null ? results.best_model.adj_r_squared.toFixed(4) : 'N/A'}
                    </div>
                  </div>
                  <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4 border-2 border-purple-300">
                    <div className="text-xs text-purple-700 mb-1 font-semibold">AIC</div>
                    <div className="text-lg font-bold text-purple-800">
                      {results.best_model.aic != null ? results.best_model.aic.toFixed(2) : 'N/A'}
                    </div>
                  </div>
                </div>

                <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                  <div className="text-xs text-gray-600 mb-1 font-semibold">수식</div>
                  <div className="text-sm font-mono text-gray-900 font-medium">{results.best_model.equation || 'N/A'}</div>
                </div>

                {/* Graphs */}
                {results.best_model && xData && yData && (
                  <div className="space-y-4">
                    <RegressionGraph
                      xData={xData}
                      yData={yData}
                      yPredicted={results.best_model.y_predicted}
                      xLabel="X"
                      yLabel="Y"
                    />

                    {results.residuals && (
                      <ResidualPlot
                        xData={xData}
                        yData={yData}
                        residuals={results.residuals}
                        xLabel="X"
                      />
                    )}
                  </div>
                )}

                <button
                  onClick={handleGenerateReport}
                  disabled={analyzing}
                  className="w-full bg-violet-600 hover:bg-violet-700 text-white py-3 px-6 rounded-xl font-bold hover:shadow-lg hover:scale-105 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  📄 보고서 생성
                </button>
              </div>
            )}
          </div>
        </div>
      </div >
    </main >
  );
}
