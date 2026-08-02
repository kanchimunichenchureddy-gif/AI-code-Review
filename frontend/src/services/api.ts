import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export function getApiErrorMessage(error: any): string {
  if (error.code === 'ECONNABORTED') {
    return 'The backend did not finish in time. Upload a source-only ZIP/folder without dependencies or build output, and confirm the backend/MySQL are running.';
  }
  if (error.response?.status === 401) {
    return 'Your session is not logged in. Click Login as Demo Student, or run review again to refresh the demo session.';
  }
  if (error.response?.data?.detail) {
    return error.response.data.detail;
  }
  if (error.message === 'Network Error') {
    return 'Backend is not reachable at http://localhost:8000. Start the FastAPI server and MySQL, then try again.';
  }
  return error.message || 'Request failed.';
}

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authService = {
  demoLogin: async (role: 'student' | 'instructor' = 'student') => {
    const res = await apiClient.post(`/auth/demo-login?role=${role}`);
    localStorage.setItem('access_token', res.data.access_token);
    return res.data;
  },
  login: async (formData: FormData) => {
    const res = await apiClient.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return res.data;
  },
  getMe: async () => {
    const res = await apiClient.get('/auth/me');
    return res.data;
  },
};

export const systemService = {
  health: async () => {
    const res = await apiClient.get('/health/');
    return res.data;
  },
};

export const submissionService = {
  createSubmission: async (
    assignmentId: number,
    files: Array<{ filename: string; content: string; language: string }>
  ) => {
    const res = await apiClient.post(`/submissions/assignment/${assignmentId}`, { files });
    return res.data;
  },
  uploadZipSubmission: async (assignmentId: number, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await apiClient.post(`/submissions/assignment/${assignmentId}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
  getSubmissionDetail: async (id: number) => {
    const res = await apiClient.get(`/submissions/${id}`);
    return res.data;
  },
  runFullAnalysis: async (id: number) => {
    const res = await apiClient.post(`/submissions/${id}/analyze`);
    return res.data;
  },
  getRubricEvaluation: async (id: number) => {
    const res = await apiClient.get(`/submissions/${id}/rubric-evaluation`);
    return res.data;
  },
  generateAIFeedback: async (id: number) => {
    const res = await apiClient.post(`/submissions/${id}/generate-feedback`);
    return res.data;
  },
  getFeedback: async (id: number) => {
    const res = await apiClient.get(`/submissions/${id}/feedback`);
    return res.data;
  },
  getPlagiarismReport: async (id: number) => {
    const res = await apiClient.get(`/submissions/${id}/plagiarism`);
    return res.data;
  },
};

export const instructorService = {
  getCourseAnalytics: async (courseId: number) => {
    const res = await apiClient.get(`/instructor/courses/${courseId}/analytics`);
    return res.data;
  },
  overrideScore: async (submissionId: number, newScore: number, reason: string) => {
    const res = await apiClient.post(`/instructor/submissions/${submissionId}/override-score`, {
      new_score: newScore,
      reason,
    });
    return res.data;
  },
  runPlagiarismCheck: async (assignmentId: number) => {
    const res = await apiClient.post(`/submissions/assignment/${assignmentId}/check-plagiarism`);
    return res.data;
  },
};

export const reportService = {
  exportGradebookCsvUrl: (courseId: number) => `${API_BASE_URL}/reports/course/${courseId}/gradebook`,
  exportSubmissionJson: async (submissionId: number) => {
    const res = await apiClient.get(`/reports/submission/${submissionId}/export`);
    return res.data;
  },
};
