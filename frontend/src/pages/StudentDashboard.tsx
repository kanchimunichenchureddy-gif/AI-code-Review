import React, { useEffect, useRef, useState } from 'react';
import { AlertTriangle, CheckCircle2, FileCode2, FolderOpen, Paperclip, Play, Upload } from 'lucide-react';
import { authService, getApiErrorMessage, submissionService, systemService } from '../services/api';

interface StudentDashboardProps {
  submissionId: number;
  onSubmissionSelected?: (submissionId: number) => void;
}

interface CodeUploadFile {
  filename: string;
  content: string;
  language: string;
}

const starterCode = `def calculate_discount(price, user_role):
    a = 100
    if price > 1000:
        if user_role == "student":
            return price * 0.8
        return price * 0.9
    return price
`;

const languageOptions = ['python', 'javascript', 'java', 'c', 'cpp', 'csharp'];
const maxReviewFiles = 500;
const maxTotalSourceBytes = 10_000_000;
const maxSingleFileBytes = 1_000_000;
const maxZipBytes = 50_000_000;
const ignoredPathSegments = new Set([
  '.git',
  '.hg',
  '.svn',
  '.next',
  '.nuxt',
  '.cache',
  '.pytest_cache',
  '__pycache__',
  'node_modules',
  'dist',
  'build',
  'coverage',
  'target',
  '.venv',
  'venv',
  'env',
]);

const directoryInputProps = {
  webkitdirectory: '',
  directory: '',
} as React.InputHTMLAttributes<HTMLInputElement> & {
  webkitdirectory?: string;
  directory?: string;
};

export const StudentDashboard: React.FC<StudentDashboardProps> = ({ submissionId, onSubmissionSelected }) => {
  const [activeSubmissionId, setActiveSubmissionId] = useState<number>(submissionId);
  const [assignmentId, setAssignmentId] = useState<number>(1);
  const [filename, setFilename] = useState<string>('solution.py');
  const [language, setLanguage] = useState<string>('python');
  const [code, setCode] = useState<string>(starterCode);
  const [submission, setSubmission] = useState<any>(null);
  const [rubricEval, setRubricEval] = useState<any>(null);
  const [feedbackCards, setFeedbackCards] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [reviewing, setReviewing] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string>('');
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [selectedCodeFiles, setSelectedCodeFiles] = useState<CodeUploadFile[]>([]);
  const [selectedZipFile, setSelectedZipFile] = useState<File | null>(null);
  const [selectedFolderFiles, setSelectedFolderFiles] = useState<CodeUploadFile[]>([]);
  const [activeFileIndex, setActiveFileIndex] = useState<number>(0);
  const [isDraggingUpload, setIsDraggingUpload] = useState<boolean>(false);
  const [uploadNotice, setUploadNotice] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setActiveSubmissionId(submissionId);
  }, [submissionId]);

  useEffect(() => {
    if (activeSubmissionId) {
      loadSubmission(activeSubmissionId);
    }
  }, [activeSubmissionId]);

  const loadSubmission = async (id: number) => {
    try {
      setLoading(true);
      setErrorMessage('');
      const subData = await submissionService.getSubmissionDetail(id);
      setSubmission(subData);

      try {
        const rEval = await submissionService.getRubricEvaluation(id);
        setRubricEval(rEval);
      } catch {
        setRubricEval(null);
      }

      try {
        const fbData = await submissionService.getFeedback(id);
        setFeedbackCards(fbData);
      } catch {
        setFeedbackCards(subData.feedback || []);
      }
    } catch (err: any) {
      setSubmission(null);
      setRubricEval(null);
      setFeedbackCards([]);
      setErrorMessage(getApiErrorMessage(err) || 'Submission not found. Login and submit code to start a review.');
    } finally {
      setLoading(false);
    }
  };

  const handleSourceFiles = async (fileList: FileList | null) => {
    const files = Array.from(fileList || []);
    if (!files.length) return;

    const zip = files.find((file) => file.name.toLowerCase().endsWith('.zip'));
    if (zip) {
      if (!validateZipFile(zip, setErrorMessage)) return;
      setSelectedZipFile(zip);
      setFilename(zip.name);
      setStatusMessage(`ZIP selected: ${zip.name}. Click Upload ZIP & Review.`);
      setErrorMessage('');
      return;
    }

    const { uploadFiles, notice } = await readCodeFiles(files);
    if (!uploadFiles.length) {
      setErrorMessage(notice || 'No supported source files were selected.');
      return;
    }

    setUploadNotice(notice);
    setSelectedCodeFiles(uploadFiles);
    setSelectedZipFile(null);
    setSelectedFolderFiles([]);
    setActiveFileIndex(0);
    setFilename(uploadFiles[0].filename);
    setCode(uploadFiles[0].content);
    setLanguage(uploadFiles[0].language);
    setStatusMessage(`${uploadFiles.length} source file${uploadFiles.length === 1 ? '' : 's'} selected.${notice ? ` ${notice}` : ''}`);
    setErrorMessage('');
  };

  const handleFolderFiles = async (fileList: FileList | null) => {
    const files = Array.from(fileList || []);
    if (!files.length) return;

    const { uploadFiles, notice } = await readCodeFiles(files, true);
    if (!uploadFiles.length) {
      setErrorMessage(notice || 'No supported source files were found in that folder.');
      return;
    }

    setUploadNotice(notice);
    setSelectedFolderFiles(uploadFiles);
    setSelectedCodeFiles(uploadFiles);
    setSelectedZipFile(null);
    setActiveFileIndex(0);
    setFilename(uploadFiles[0].filename);
    setCode(uploadFiles[0].content);
    setLanguage(uploadFiles[0].language);
    setStatusMessage(`Folder selected with ${uploadFiles.length} supported source file${uploadFiles.length === 1 ? '' : 's'}.${notice ? ` ${notice}` : ''}`);
    setErrorMessage('');
  };

  const handleDropUpload = async (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDraggingUpload(false);

    try {
      const droppedFiles = await getDroppedFiles(event.dataTransfer);
      if (!droppedFiles.length) {
        setErrorMessage('No files were found in the drop.');
        return;
      }

      const zip = droppedFiles.find((file) => file.name.toLowerCase().endsWith('.zip'));
      if (zip) {
        if (!validateZipFile(zip, setErrorMessage)) return;
        setSelectedZipFile(zip);
        setSelectedCodeFiles([]);
        setSelectedFolderFiles([]);
        setFilename(zip.name);
        setStatusMessage(`ZIP selected: ${zip.name}. Click Upload ZIP & Review.`);
        setErrorMessage('');
        return;
      }

      const { uploadFiles, notice } = await readCodeFiles(droppedFiles, true);
      if (!uploadFiles.length) {
        setErrorMessage(notice || 'No supported source files were found. Supported: Python, JavaScript, Java, C, C++, C#.');
        return;
      }

      setUploadNotice(notice);
      setSelectedCodeFiles(uploadFiles);
      setSelectedFolderFiles(uploadFiles);
      setSelectedZipFile(null);
      setActiveFileIndex(0);
      setFilename(uploadFiles[0].filename);
      setCode(uploadFiles[0].content);
      setLanguage(uploadFiles[0].language);
      setStatusMessage(`Ready to review ${uploadFiles.length} file${uploadFiles.length === 1 ? '' : 's'}.${notice ? ` ${notice}` : ''}`);
      setErrorMessage('');
    } catch (err: any) {
      setErrorMessage(err.message || 'Could not read dropped files.');
    }
  };

  const selectUploadFile = (index: number) => {
    const selected = selectedCodeFiles[index];
    if (!selected) return;
    setActiveFileIndex(index);
    setFilename(selected.filename);
    setCode(selected.content);
    setLanguage(selected.language);
  };

  const updateCurrentFileCode = (nextCode: string) => {
    setCode(nextCode);
    if (!selectedCodeFiles.length) return;

    setSelectedCodeFiles((files) =>
      files.map((file, index) =>
        index === activeFileIndex ? { ...file, content: nextCode } : file
      )
    );
  };

  const prepareReviewSession = async () => {
    setStatusMessage('Checking backend, MySQL, and login session...');
    const health = await systemService.health();
    if (health?.status !== 'healthy') {
      throw new Error(`Backend health check failed: database ${health?.database || 'unknown'}, storage ${health?.storage || 'unknown'}.`);
    }

    const token = localStorage.getItem('access_token');
    if (!token) {
      await authService.demoLogin('student');
      setStatusMessage('Demo student session created. Preparing review...');
      return;
    }

    try {
      await authService.getMe();
    } catch (err: any) {
      if (err.response?.status === 401 || err.response?.status === 403) {
        await authService.demoLogin('student');
        setStatusMessage('Demo student session refreshed. Preparing review...');
        return;
      }
      throw err;
    }
  };

  const handleSubmitCode = async (event: React.FormEvent) => {
    event.preventDefault();
    if (reviewing) return;
    if (!selectedCodeFiles.length && !code.trim()) {
      setErrorMessage('Paste code or choose a source file before running review.');
      return;
    }

    try {
      setReviewing(true);
      setErrorMessage('');
      await prepareReviewSession();
      setStatusMessage(`Submitting ${selectedCodeFiles.length || 1} file${(selectedCodeFiles.length || 1) === 1 ? '' : 's'}...`);

      const filesToSubmit = selectedCodeFiles.length > 0
        ? selectedCodeFiles
        : [{ filename, content: code, language }];

      const created = await submissionService.createSubmission(assignmentId, filesToSubmit);

      setStatusMessage('Running deterministic analysis: parsing AST, checking complexity, static rules, and security...');
      const analyzed = await submissionService.runFullAnalysis(created.id);

      setStatusMessage('Generating evidence-bound feedback...');
      const feedback = await submissionService.generateAIFeedback(created.id);

      setActiveSubmissionId(analyzed.id);
      onSubmissionSelected?.(analyzed.id);
      setSubmission(analyzed);
      setFeedbackCards(feedback);

      try {
        const rEval = await submissionService.getRubricEvaluation(analyzed.id);
        setRubricEval(rEval);
      } catch {
        setRubricEval(null);
      }

      setStatusMessage(`Review complete for submission #${analyzed.id}.`);
    } catch (err: any) {
      setErrorMessage(getApiErrorMessage(err) || 'Review failed. Check backend server and login state.');
    } finally {
      setReviewing(false);
    }
  };

  const handleSubmitZip = async (file: File | null) => {
    if (reviewing) return;
    if (!file) {
      setErrorMessage('Choose a .zip archive first, then click Upload ZIP & Review.');
      return;
    }
    if (!validateZipFile(file, setErrorMessage)) return;

    try {
      setReviewing(true);
      setErrorMessage('');
      await prepareReviewSession();
      setStatusMessage('Uploading ZIP archive and extracting source files...');

      const created = await submissionService.uploadZipSubmission(assignmentId, file);
      setStatusMessage(`Running deterministic analysis for submission #${created.id}...`);
      const analyzed = await submissionService.runFullAnalysis(created.id);
      setStatusMessage('Generating final code review feedback...');
      const feedback = await submissionService.generateAIFeedback(created.id);

      setActiveSubmissionId(analyzed.id);
      onSubmissionSelected?.(analyzed.id);
      setSubmission(analyzed);
      setFeedbackCards(feedback);
      try {
        const rEval = await submissionService.getRubricEvaluation(analyzed.id);
        setRubricEval(rEval);
      } catch {
        setRubricEval(null);
      }
      setStatusMessage(`ZIP review complete for submission #${analyzed.id}.`);
    } catch (err: any) {
      setErrorMessage(getApiErrorMessage(err) || 'ZIP review failed.');
    } finally {
      setReviewing(false);
    }
  };

  const staticFindings = submission?.findings || [];
  const securityFindings = submission?.security_findings || [];
  const complexityMetrics = submission?.complexity_metrics || [];
  const analyzedFileCount = submission?.files?.length || selectedCodeFiles.length || 0;
  const totalFindingCount = staticFindings.length + securityFindings.length;
  const riskLevel = securityFindings.some((finding: any) => finding.severity === 'CRITICAL' || finding.severity === 'HIGH')
    ? 'Needs attention'
    : totalFindingCount > 10
      ? 'Moderate'
      : 'Stable';

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-6 space-y-6">
      <section className="bg-slate-800 p-6 rounded-lg border border-slate-700 shadow-md space-y-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-sky-400">Student Code Review Workspace</h1>
            <p className="text-slate-400 text-sm mt-1">
              Submit code, run deterministic analysis, and inspect evidence-linked feedback.
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-300 bg-slate-900 px-3 py-2 rounded border border-slate-700">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            AI explains findings only after static evidence exists
          </div>
        </div>

        <form onSubmit={handleSubmitCode} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <label className="space-y-1">
              <span className="text-xs text-slate-300">Assignment ID</span>
              <input
                type="number"
                value={assignmentId}
                min={1}
                onChange={(e) => setAssignmentId(Number(e.target.value) || 1)}
                className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-sm text-slate-100"
              />
            </label>

            <label className="space-y-1">
              <span className="text-xs text-slate-300">Language</span>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-sm text-slate-100"
              >
                {languageOptions.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </label>

            <label className="space-y-1 md:col-span-2">
              <span className="text-xs text-slate-300">Filename</span>
              <input
                value={filename}
                onChange={(e) => setFilename(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-sm text-slate-100"
              />
            </label>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-[260px_minmax(0,1fr)] gap-4">
            <aside className="bg-slate-900 border border-slate-700 rounded p-3 space-y-3">
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2 text-sm font-semibold text-sky-300">
                  <FolderOpen className="w-4 h-4" />
                  Files
                </div>
                <span className="text-xs text-slate-400">{selectedCodeFiles.length || submission?.files?.length || 1}</span>
              </div>

              <div className="max-h-[320px] overflow-y-auto space-y-1">
                {selectedCodeFiles.length > 0 ? (
                  selectedCodeFiles.map((file, index) => (
                    <button
                      key={`${file.filename}-${index}`}
                      type="button"
                      onClick={() => selectUploadFile(index)}
                      className={`w-full text-left rounded px-2 py-2 text-xs border transition ${
                        index === activeFileIndex
                          ? 'bg-sky-950 border-sky-600 text-sky-100'
                          : 'bg-slate-950 border-slate-800 text-slate-300 hover:border-slate-600'
                      }`}
                    >
                      <span className="block truncate">{file.filename}</span>
                      <span className="text-[10px] text-slate-500">{file.language}</span>
                    </button>
                  ))
                ) : submission?.files?.length > 0 ? (
                  submission.files.map((file: any) => (
                    <div key={file.id} className="rounded bg-slate-950 border border-slate-800 px-2 py-2 text-xs text-slate-300">
                      <span className="block truncate">{file.filename}</span>
                      <span className="text-[10px] text-slate-500">{file.language}</span>
                    </div>
                  ))
                ) : (
                  <div className="rounded bg-slate-950 border border-slate-800 px-2 py-2 text-xs text-slate-400">
                    solution.py
                  </div>
                )}
              </div>
            </aside>

            <div className="space-y-2">
              <label className="text-xs text-slate-300">Code preview and edits</label>
              <textarea
                value={code}
                onChange={(e) => updateCurrentFileCode(e.target.value)}
                spellCheck={false}
                className="w-full min-h-[260px] bg-slate-950 border border-slate-700 rounded p-4 text-sm text-slate-100 font-mono resize-y"
              />
            </div>
          </div>

          <div
            onDragEnter={(event) => {
              event.preventDefault();
              setIsDraggingUpload(true);
            }}
            onDragOver={(event) => {
              event.preventDefault();
              setIsDraggingUpload(true);
            }}
            onDragLeave={(event) => {
              if (event.currentTarget === event.target) {
                setIsDraggingUpload(false);
              }
            }}
            onDrop={handleDropUpload}
            className={`rounded-lg border p-4 transition ${
              isDraggingUpload
                ? 'border-sky-400 bg-sky-950/50'
                : 'border-slate-700 bg-slate-900'
            }`}
          >
            <div className="flex flex-col lg:flex-row lg:items-center gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 text-sky-300 font-semibold">
                  <Paperclip className="w-4 h-4" />
                  Upload anything for review
                </div>
                <p className="text-sm text-slate-400 mt-1">
                  Drag and drop source files, a project folder, or a source-only ZIP archive here.
                </p>
                <p className="text-xs text-slate-500 mt-2">
                  Selected: {selectedCodeFiles.length} source file{selectedCodeFiles.length === 1 ? '' : 's'}
                  {selectedFolderFiles.length > 0 ? ` from folder (${selectedFolderFiles.length})` : ''}
                  {selectedZipFile ? ` - ZIP: ${selectedZipFile.name}` : ''}
                </p>
                {uploadNotice && (
                  <p className="text-xs text-amber-300 mt-2">{uploadNotice}</p>
                )}
              </div>

              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="rounded bg-sky-600 px-3 py-2 text-sm font-semibold text-white hover:bg-sky-500"
                >
                  Files or ZIP
                </button>
                <button
                  type="button"
                  onClick={() => folderInputRef.current?.click()}
                  className="rounded bg-indigo-600 px-3 py-2 text-sm font-semibold text-white hover:bg-indigo-500"
                >
                  Folder
                </button>
              </div>
            </div>

            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".py,.js,.jsx,.ts,.tsx,.java,.c,.h,.cpp,.hpp,.cc,.cs,.zip"
              onChange={(e) => handleSourceFiles(e.target.files)}
              className="hidden"
            />
            <input
              ref={folderInputRef}
              type="file"
              multiple
              {...directoryInputProps}
              onChange={(e) => handleFolderFiles(e.target.files)}
              className="hidden"
            />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_220px] gap-4">
              <div className="bg-slate-900 border border-slate-700 rounded p-4 space-y-3 text-sm text-slate-300">
                <div className="flex items-center gap-2 text-sky-300 font-semibold">
                  <FileCode2 className="w-4 h-4" />
                  Review pipeline
                </div>
                <p>1. Store submitted files securely.</p>
                <p>2. Parse AST and language structure.</p>
                <p>3. Run static, security, complexity, and rubric checks.</p>
                <p>4. Generate feedback only from validated evidence.</p>
              </div>

            <div className="space-y-3">
              <button
                type="submit"
                disabled={reviewing}
                className="w-full inline-flex items-center justify-center gap-2 bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white font-semibold px-4 py-3 rounded transition"
              >
                <Play className="w-4 h-4" />
                {reviewing ? 'Reviewing...' : 'Submit & Run Review'}
              </button>

              <button
                type="button"
                disabled={reviewing}
                onClick={() => handleSubmitZip(selectedZipFile)}
                className="w-full inline-flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-semibold px-4 py-3 rounded transition"
              >
                <Upload className="w-4 h-4" />
                Upload ZIP & Review
              </button>
            </div>
          </div>
        </form>

        {(statusMessage || errorMessage) && (
          <div className={`text-sm rounded border px-4 py-3 ${errorMessage ? 'bg-rose-950/40 border-rose-800 text-rose-200' : 'bg-emerald-950/40 border-emerald-800 text-emerald-200'}`}>
            {errorMessage || statusMessage}
          </div>
        )}
      </section>

      {loading ? (
        <div className="p-8 text-center text-slate-400">Loading review results...</div>
      ) : !submission ? (
        <div className="p-8 text-center text-rose-300 bg-slate-800 border border-slate-700 rounded-lg">
          {errorMessage || 'No submission loaded yet.'}
        </div>
      ) : (
        <>
          <header className="flex flex-wrap justify-between items-center bg-slate-800 p-6 rounded-lg border border-slate-700 shadow-md gap-4">
            <div>
              <h2 className="text-xl font-bold text-sky-400">Review Results</h2>
              <p className="text-slate-400 text-sm">
                Submission #{submission.id} - Attempt #{submission.attempt_number} - Status:{' '}
                <span className="font-semibold text-emerald-400">{submission.status}</span>
              </p>
            </div>
            <div className="text-right">
              <div className="text-3xl font-extrabold text-emerald-400">
                {submission.score !== null ? `${submission.score} / 100` : 'Pending'}
              </div>
              <p className="text-xs text-slate-400">Rubric-adjusted score draft</p>
            </div>
          </header>

          <section className="grid grid-cols-2 lg:grid-cols-5 gap-4">
            <ReportStat label="Files analyzed" value={analyzedFileCount} tone="text-sky-300" />
            <ReportStat label="Static findings" value={staticFindings.length} tone="text-amber-300" />
            <ReportStat label="Security issues" value={securityFindings.length} tone="text-rose-300" />
            <ReportStat label="Feedback cards" value={feedbackCards.length} tone="text-emerald-300" />
            <ReportStat label="Project status" value={riskLevel} tone={riskLevel === 'Needs attention' ? 'text-rose-300' : 'text-emerald-300'} />
          </section>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <section className="bg-slate-800 p-6 rounded-lg border border-slate-700 space-y-4">
              <h2 className="text-lg font-semibold text-slate-200 border-b border-slate-700 pb-2">Complexity Metrics</h2>
              <MetricGrid metrics={complexityMetrics[0]} />
            </section>

            <section className="bg-slate-800 p-6 rounded-lg border border-slate-700 space-y-4 md:col-span-2">
              <h2 className="text-lg font-semibold text-slate-200 border-b border-slate-700 pb-2">Rubric Breakdown</h2>
              {rubricEval ? (
                <div className="space-y-3">
                  {rubricEval.rule_results.map((r: any, idx: number) => (
                    <div key={idx} className="flex justify-between items-center bg-slate-900 p-3 rounded border border-slate-700 gap-3">
                      <div>
                        <span className="font-semibold text-sky-300">{r.rule_code}</span>
                        <span className="text-xs text-slate-400 ml-2">({r.category})</span>
                        <p className="text-xs text-slate-400">{r.details}</p>
                      </div>
                      <span className={`text-sm font-bold whitespace-nowrap ${r.passed ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {r.score} / {r.weight}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-slate-400 text-sm">No custom rubric is defined for this assignment.</p>
              )}
            </section>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <FindingsPanel title="Static Findings" findings={staticFindings} type="static" />
            <FindingsPanel title="Security Findings" findings={securityFindings} type="security" />
          </div>

          <section className="bg-slate-800 p-6 rounded-lg border border-slate-700 space-y-4">
            <h2 className="text-xl font-bold text-sky-400 border-b border-slate-700 pb-2">Evidence-Bound Educational Feedback</h2>
            {feedbackCards.length > 0 ? (
              <div className="space-y-4">
                {feedbackCards.map((card, idx) => (
                  <div key={idx} className="bg-slate-900 p-5 rounded border border-slate-700 space-y-3">
                    <div className="flex justify-between items-start gap-3">
                      <h3 className="text-base font-semibold text-emerald-300">{card.title}</h3>
                      <span className="text-xs bg-slate-800 px-3 py-1 rounded-full text-slate-300 border border-slate-700 whitespace-nowrap">
                        {card.category} {card.line_number && `Line ${card.line_number}`}
                      </span>
                    </div>
                    <div className="text-sm space-y-2">
                      <p><strong className="text-slate-300">What:</strong> <span className="text-slate-400">{card.what_text}</span></p>
                      <p><strong className="text-slate-300">Why it matters:</strong> <span className="text-slate-400">{card.why_text}</span></p>
                      <p><strong className="text-slate-300">How to fix:</strong> <span className="text-slate-400">{card.how_to_fix_text}</span></p>
                    </div>
                    {card.example_code && (
                      <pre className="bg-slate-950 p-3 rounded text-xs font-mono text-emerald-400 overflow-x-auto border border-slate-800">
                        {card.example_code}
                      </pre>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-slate-400 text-sm">No feedback cards were generated for this submission.</p>
            )}
          </section>
        </>
      )}
    </div>
  );
};

const MetricGrid: React.FC<{ metrics: any }> = ({ metrics }) => {
  const values = [
    ['Cyclomatic', metrics?.cyclomatic_complexity ?? 1, 'text-cyan-400'],
    ['Cognitive', metrics?.cognitive_complexity ?? 0, 'text-amber-400'],
    ['Maintainability', metrics?.maintainability_index ?? 100, 'text-emerald-400'],
    ['Lines of Code', metrics?.lines_of_code ?? 0, 'text-indigo-400'],
  ];

  return (
    <div className="grid grid-cols-2 gap-4">
      {values.map(([label, value, color]) => (
        <div key={String(label)} className="bg-slate-900 p-4 rounded text-center border border-slate-700">
          <span className="text-xs text-slate-400 block">{label}</span>
          <span className={`text-xl font-bold ${color}`}>{value}</span>
        </div>
      ))}
    </div>
  );
};

const FindingsPanel: React.FC<{ title: string; findings: any[]; type: 'static' | 'security' }> = ({ title, findings, type }) => (
  <section className="bg-slate-800 p-6 rounded-lg border border-slate-700 space-y-4">
    <h2 className="text-lg font-semibold text-slate-200 border-b border-slate-700 pb-2">{title}</h2>
    {findings.length > 0 ? (
      <div className="space-y-3">
        {findings.map((finding, idx) => {
          const line = type === 'static' ? finding.line_start : finding.line_number;
          const rule = type === 'static' ? finding.rule_id : finding.cve_or_rule;
          const message = type === 'static' ? finding.message : finding.description;
          return (
            <div key={`${rule}-${idx}`} className="bg-slate-900 border border-slate-700 rounded p-4 space-y-2">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="font-semibold text-sky-300">{rule}</span>
                <span className="text-xs text-slate-300 bg-slate-800 border border-slate-700 px-2 py-1 rounded">
                  {finding.severity} - line {line}
                </span>
              </div>
              <p className="text-sm text-slate-300">{message}</p>
              {finding.evidence_snippet && (
                <pre className="bg-slate-950 border border-slate-800 rounded p-2 text-xs text-amber-200 overflow-x-auto">
                  {finding.evidence_snippet}
                </pre>
              )}
            </div>
          );
        })}
      </div>
    ) : (
      <div className="flex items-center gap-2 text-sm text-slate-400">
        <AlertTriangle className="w-4 h-4 text-slate-500" />
        No findings in this category.
      </div>
    )}
  </section>
);

const ReportStat: React.FC<{ label: string; value: React.ReactNode; tone: string }> = ({ label, value, tone }) => (
  <div className="bg-slate-800 border border-slate-700 rounded p-4">
    <span className="block text-xs text-slate-400">{label}</span>
    <span className={`block mt-1 text-xl font-bold ${tone}`}>{value}</span>
  </div>
);

function inferLanguage(name: string): string | null {
  const lowerName = name.toLowerCase();
  if (lowerName.endsWith('.py')) return 'python';
  if (lowerName.endsWith('.js') || lowerName.endsWith('.jsx') || lowerName.endsWith('.ts') || lowerName.endsWith('.tsx')) return 'javascript';
  if (lowerName.endsWith('.java')) return 'java';
  if (lowerName.endsWith('.c') || lowerName.endsWith('.h')) return 'c';
  if (lowerName.endsWith('.cpp') || lowerName.endsWith('.hpp') || lowerName.endsWith('.cc')) return 'cpp';
  if (lowerName.endsWith('.cs')) return 'csharp';
  return null;
}

type BrowserFileEntry = {
  isFile: boolean;
  isDirectory: boolean;
  name: string;
  fullPath?: string;
  file: (success: (file: File) => void, error?: (error: DOMException) => void) => void;
  createReader?: () => {
    readEntries: (
      success: (entries: BrowserFileEntry[]) => void,
      error?: (error: DOMException) => void
    ) => void;
  };
};

async function getDroppedFiles(dataTransfer: DataTransfer): Promise<File[]> {
  const itemEntries = Array.from(dataTransfer.items || [])
    .map((item) => {
      const maybeEntry = item as DataTransferItem & {
        webkitGetAsEntry?: () => BrowserFileEntry | null;
      };
      return (maybeEntry.webkitGetAsEntry?.() || null) as BrowserFileEntry | null;
    })
    .filter((entry): entry is BrowserFileEntry => Boolean(entry));

  if (!itemEntries.length) {
    return Array.from(dataTransfer.files || []);
  }

  const nestedFiles = await Promise.all(itemEntries.map((entry) => readEntryFiles(entry)));
  return nestedFiles.flat();
}

async function readEntryFiles(entry: BrowserFileEntry, parentPath = ''): Promise<File[]> {
  if (entry.isFile) {
    return [await readEntryFile(entry, parentPath)];
  }

  if (!entry.isDirectory || !entry.createReader) {
    return [];
  }

  const childEntries = await readAllDirectoryEntries(entry);
  const entryPath = parentPath ? `${parentPath}/${entry.name}` : entry.name;
  const childFiles = await Promise.all(childEntries.map((child) => readEntryFiles(child, entryPath)));
  return childFiles.flat();
}

function readEntryFile(entry: BrowserFileEntry, parentPath: string): Promise<File> {
  return new Promise((resolve, reject) => {
    entry.file(
      (file) => {
        const relativePath = parentPath ? `${parentPath}/${file.name}` : file.name;
        Object.defineProperty(file, 'webkitRelativePath', {
          configurable: true,
          value: relativePath,
        });
        resolve(file);
      },
      reject
    );
  });
}

function readAllDirectoryEntries(entry: BrowserFileEntry): Promise<BrowserFileEntry[]> {
  const reader = entry.createReader?.();
  if (!reader) return Promise.resolve([]);

  return new Promise((resolve, reject) => {
    const allEntries: BrowserFileEntry[] = [];
    const readBatch = () => {
      reader.readEntries(
        (entries) => {
          if (!entries.length) {
            resolve(allEntries);
            return;
          }
          allEntries.push(...entries);
          readBatch();
        },
        reject
      );
    };
    readBatch();
  });
}

async function readCodeFiles(
  files: File[],
  preserveRelativePath = false
): Promise<{ uploadFiles: CodeUploadFile[]; notice: string }> {
  const candidates = files
    .map((file) => ({
      file,
      relativePath: preserveRelativePath ? getRelativeFilePath(file) : file.name,
    }))
    .filter(({ file, relativePath }) => {
      if (!inferLanguage(file.name) || file.name.toLowerCase().endsWith('.zip')) return false;
      if (file.size > maxSingleFileBytes) return false;
      return !isIgnoredProjectPath(relativePath);
    });

  const limitedCandidates: typeof candidates = [];
  let totalBytes = 0;
  for (const candidate of candidates) {
    if (limitedCandidates.length >= maxReviewFiles) break;
    if (totalBytes + candidate.file.size > maxTotalSourceBytes) break;
    limitedCandidates.push(candidate);
    totalBytes += candidate.file.size;
  }

  const uploadFiles = await Promise.all(
    limitedCandidates.map(async ({ file, relativePath }) => ({
      filename: relativePath,
      content: await file.text(),
      language: inferLanguage(file.name) || 'python',
    }))
  );

  const skippedCount = Math.max(0, files.length - uploadFiles.length);
  const notice = skippedCount > 0
    ? `Skipped ${skippedCount} unsupported, generated, vendor, or oversized file${skippedCount === 1 ? '' : 's'}. Review limit: ${maxReviewFiles} files / ${Math.round(maxTotalSourceBytes / 1_000_000)} MB of source.`
    : '';

  return { uploadFiles, notice };
}

function getRelativeFilePath(file: File): string {
  const relativePath = (file as File & { webkitRelativePath?: string }).webkitRelativePath;
  return relativePath || file.name;
}

function isIgnoredProjectPath(path: string): boolean {
  return path
    .split(/[\\/]/)
    .some((segment) => ignoredPathSegments.has(segment));
}

function validateZipFile(file: File, setErrorMessage: (message: string) => void): boolean {
  if (!file.name.toLowerCase().endsWith('.zip')) {
    setErrorMessage('Choose a .zip archive for ZIP review.');
    return false;
  }

  if (file.size > maxZipBytes) {
    setErrorMessage(
      `ZIP is too large (${Math.round(file.size / 1_000_000)} MB). Limit is ${Math.round(maxZipBytes / 1_000_000)} MB. Create a source-only ZIP without dependencies, node_modules, dist/build, virtualenv, or cache folders.`
    );
    return false;
  }

  return true;
}
