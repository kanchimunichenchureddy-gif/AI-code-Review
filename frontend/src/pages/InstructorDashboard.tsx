import React, { useState, useEffect } from 'react';
import { instructorService, reportService } from '../services/api';

interface InstructorDashboardProps {
  courseId: number;
}

export const InstructorDashboard: React.FC<InstructorDashboardProps> = ({ courseId }) => {
  const [analytics, setAnalytics] = useState<any>(null);
  const [overrideSubId, setOverrideSubId] = useState<number | null>(null);
  const [newScore, setNewScore] = useState<string>('');
  const [reason, setReason] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    async function fetchAnalytics() {
      try {
        setLoading(true);
        const data = await instructorService.getCourseAnalytics(courseId);
        setAnalytics(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    if (courseId) {
      fetchAnalytics();
    }
  }, [courseId]);

  const handleOverrideScore = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!overrideSubId) return;
    try {
      await instructorService.overrideScore(overrideSubId, parseFloat(newScore), reason);
      alert('Score override successful!');
      setOverrideSubId(null);
      setNewScore('');
      setReason('');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to override score');
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-slate-400">Loading Instructor Dashboard...</div>;
  }

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-6 space-y-6">
      {/* Header */}
      <header className="flex justify-between items-center bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-md">
        <div>
          <h1 className="text-2xl font-bold text-sky-400">Instructor Management & Analytics</h1>
          <p className="text-slate-400 text-sm">Course: {analytics?.course_code} - {analytics?.course_title}</p>
        </div>
        <div className="space-x-3">
          <a
            href={reportService.exportGradebookCsvUrl(courseId)}
            className="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold px-4 py-2 rounded-lg text-sm transition"
          >
            Export Gradebook (CSV)
          </a>
        </div>
      </header>

      {/* Analytics Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="bg-slate-800 p-4 rounded-xl border border-slate-700 text-center">
          <span className="text-xs text-slate-400 block">Enrolled Students</span>
          <span className="text-2xl font-bold text-sky-400">{analytics?.total_enrolled_students || 0}</span>
        </div>
        <div className="bg-slate-800 p-4 rounded-xl border border-slate-700 text-center">
          <span className="text-xs text-slate-400 block">Class Average</span>
          <span className="text-2xl font-bold text-emerald-400">{analytics?.class_average_score || 0}%</span>
        </div>
        <div className="bg-slate-800 p-4 rounded-xl border border-slate-700 text-center">
          <span className="text-xs text-slate-400 block">Static Findings</span>
          <span className="text-2xl font-bold text-amber-400">{analytics?.total_static_findings || 0}</span>
        </div>
        <div className="bg-slate-800 p-4 rounded-xl border border-slate-700 text-center">
          <span className="text-xs text-slate-400 block">Security Findings</span>
          <span className="text-2xl font-bold text-rose-400">{analytics?.total_security_findings || 0}</span>
        </div>
        <div className="bg-slate-800 p-4 rounded-xl border border-slate-700 text-center">
          <span className="text-xs text-slate-400 block">Plagiarism Flags</span>
          <span className="text-2xl font-bold text-purple-400">{analytics?.plagiarism_flagged_submissions || 0}</span>
        </div>
      </div>

      {/* Override Score Modal / Form */}
      <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 space-y-4">
        <h2 className="text-lg font-bold text-slate-200 border-b border-slate-700 pb-2">Instructor Grade Adjustment & Audit Log</h2>
        <form onSubmit={handleOverrideScore} className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
          <div>
            <label className="text-xs text-slate-300 block mb-1">Submission ID</label>
            <input
              type="number"
              placeholder="e.g. 1"
              value={overrideSubId || ''}
              onChange={(e) => setOverrideSubId(parseInt(e.target.value))}
              className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-slate-200"
              required
            />
          </div>
          <div>
            <label className="text-xs text-slate-300 block mb-1">New Score</label>
            <input
              type="number"
              step="0.1"
              placeholder="e.g. 95.0"
              value={newScore}
              onChange={(e) => setNewScore(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-slate-200"
              required
            />
          </div>
          <div>
            <label className="text-xs text-slate-300 block mb-1">Audit Reason</label>
            <input
              type="text"
              placeholder="Reason for manual override"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-slate-200"
              required
            />
          </div>
          <button
            type="submit"
            className="bg-sky-600 hover:bg-sky-500 text-white font-semibold p-2 rounded text-sm transition"
          >
            Apply Score Override
          </button>
        </form>
      </div>
    </div>
  );
};
