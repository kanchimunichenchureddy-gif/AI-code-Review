import React, { useState, useEffect } from 'react';
import { StudentDashboard } from './pages/StudentDashboard';
import { InstructorDashboard } from './pages/InstructorDashboard';
import { apiClient } from './services/api';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'student' | 'instructor'>('student');
  const [submissionId, setSubmissionId] = useState<number>(1);
  const [courseId, setCourseId] = useState<number>(1);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(!!localStorage.getItem('access_token'));
  const [userRole, setUserRole] = useState<string>('Guest');
  const [loadingAuth, setLoadingAuth] = useState<boolean>(false);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      setIsAuthenticated(true);
      apiClient.get('/auth/me')
        .then((res) => setUserRole(res.data.role || 'User'))
        .catch(() => {
          localStorage.removeItem('access_token');
          setIsAuthenticated(false);
        });
    }
  }, []);

  const handleDemoLogin = async (role: 'student' | 'instructor') => {
    setLoadingAuth(true);
    try {
      // Call dedicated demo-login endpoint
      const res = await apiClient.post(`/auth/demo-login?role=${role}`);
      const token = res.data.access_token;

      localStorage.setItem('access_token', token);
      setIsAuthenticated(true);
      setUserRole(role.toUpperCase());

      alert(`Successfully logged in as ${role.toUpperCase()}! Reloading dashboard...`);
      window.location.reload();
    } catch (err: any) {
      alert(`Login error: ${err.response?.data?.detail || err.message}`);
    } finally {
      setLoadingAuth(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    setIsAuthenticated(false);
    setUserRole('Guest');
    window.location.reload();
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col font-sans">
      {/* Top Navigation Bar */}
      <nav className="bg-slate-800 border-b border-slate-700 px-6 py-4 flex flex-wrap justify-between items-center shadow-lg gap-4">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-sky-500 flex items-center justify-center font-bold text-white shadow-md">
            AI
          </div>
          <span className="text-xl font-extrabold bg-gradient-to-r from-sky-400 to-emerald-400 bg-clip-text text-transparent">
            AI Code Reviewer & Feedback System
          </span>
        </div>

        {/* View Switcher Tabs */}
        <div className="flex bg-slate-900 p-1 rounded-lg border border-slate-700 space-x-1">
          <button
            onClick={() => setActiveTab('student')}
            className={`px-4 py-2 text-sm font-semibold rounded-md transition ${
              activeTab === 'student'
                ? 'bg-sky-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Student View
          </button>
          <button
            onClick={() => setActiveTab('instructor')}
            className={`px-4 py-2 text-sm font-semibold rounded-md transition ${
              activeTab === 'instructor'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Instructor View
          </button>
        </div>

        {/* Authentication Controls */}
        <div className="flex items-center space-x-3 text-xs">
          {isAuthenticated ? (
            <div className="flex items-center space-x-3 bg-slate-900 px-3 py-1.5 rounded border border-slate-700">
              <span className="text-slate-300">Logged in: <strong className="text-emerald-400">{userRole}</strong></span>
              <button
                onClick={handleLogout}
                className="bg-rose-700 hover:bg-rose-600 text-white font-semibold px-2 py-1 rounded transition"
              >
                Logout
              </button>
            </div>
          ) : (
            <div className="flex items-center space-x-2">
              <button
                onClick={() => handleDemoLogin('student')}
                disabled={loadingAuth}
                className="bg-sky-600 hover:bg-sky-500 text-white font-semibold px-3 py-1.5 rounded transition disabled:opacity-50"
              >
                {loadingAuth ? 'Logging in...' : 'Login as Demo Student'}
              </button>
              <button
                onClick={() => handleDemoLogin('instructor')}
                disabled={loadingAuth}
                className="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold px-3 py-1.5 rounded transition disabled:opacity-50"
              >
                {loadingAuth ? 'Logging in...' : 'Login as Demo Instructor'}
              </button>
            </div>
          )}

          {/* Sub/Course Selector Controls */}
          {activeTab === 'student' ? (
            <div className="flex items-center space-x-2 bg-slate-900 px-3 py-1.5 rounded border border-slate-700">
              <label className="text-slate-300">Sub ID:</label>
              <input
                type="number"
                value={submissionId}
                onChange={(e) => setSubmissionId(Number(e.target.value) || 1)}
                className="w-12 bg-slate-800 border border-slate-600 rounded px-1 py-0.5 text-center font-bold text-sky-400"
              />
            </div>
          ) : (
            <div className="flex items-center space-x-2 bg-slate-900 px-3 py-1.5 rounded border border-slate-700">
              <label className="text-slate-300">Course ID:</label>
              <input
                type="number"
                value={courseId}
                onChange={(e) => setCourseId(Number(e.target.value) || 1)}
                className="w-12 bg-slate-800 border border-slate-600 rounded px-1 py-0.5 text-center font-bold text-emerald-400"
              />
            </div>
          )}
        </div>
      </nav>

      {/* Authentication Banner Warning if not logged in */}
      {!isAuthenticated && (
        <div className="bg-amber-900/40 border-b border-amber-600/50 p-3 text-center text-amber-200 text-xs flex justify-center items-center space-x-2">
          <span>⚠️ <strong>Authentication Required:</strong> Please click </span>
          <button onClick={() => handleDemoLogin('student')} className="underline font-bold hover:text-white">"Login as Demo Student"</button>
          <span> or </span>
          <button onClick={() => handleDemoLogin('instructor')} className="underline font-bold hover:text-white">"Login as Demo Instructor"</button>
          <span> above to authorize your browser session automatically.</span>
        </div>
      )}

      {/* Main Content View */}
      <main className="flex-1">
        {activeTab === 'student' ? (
          <StudentDashboard submissionId={submissionId} onSubmissionSelected={setSubmissionId} />
        ) : (
          <InstructorDashboard courseId={courseId} />
        )}
      </main>
    </div>
  );
};

export default App;
