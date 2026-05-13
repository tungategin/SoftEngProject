import React, { useMemo, useState } from 'react';
import Button from '../components/Button';
import StatusBadge from '../components/StatusBadge';
import { changeStudentPassword } from '../api/authApi';
import { getActivity, tutorChat } from '../api/studentApi';
import { useAuth } from '../context/AuthContext';
import { formatValidationErrors, mapErrorCodeToMessage, safeInt } from '../utils/helpers';

const UI_DEBUG = String(import.meta.env.VITE_UI_DEBUG || 'true').toLowerCase() === 'true';

function ChatBubble({ role, text }) {
  return (
    <div className={role === 'student' ? 'chat-bubble chat-student' : 'chat-bubble chat-assistant'}>
      <span className="bubble-role">{role === 'student' ? 'You' : 'Tutor'}</span>
      <p>{text}</p>
    </div>
  );
}

export default function StudentActivityPage() {
  const { user, updateUser } = useAuth();

  const [courseId, setCourseId] = useState('');
  const [activityNo, setActivityNo] = useState('1');

  const [activity, setActivity] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatBusy, setChatBusy] = useState(false);
  const [chatStarted, setChatStarted] = useState(false);
  const [activityCompleted, setActivityCompleted] = useState(false);
  const [miniLesson, setMiniLesson] = useState('');

  const [currentScore, setCurrentScore] = useState(0);
  const [completedObjectives, setCompletedObjectives] = useState(0);
  const [totalObjectives, setTotalObjectives] = useState(0);

  const [banner, setBanner] = useState(null);

  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [passwordBusy, setPasswordBusy] = useState(false);

  const credentials = useMemo(
    () => ({
      email: user ? user.email : '',
      password: user ? user.password : '',
    }),
    [user],
  );

  const handleError = (result) => {
    if (!result) {
      setBanner({ type: 'error', text: 'Unknown error.' });
      return;
    }

    if (result.error === 'validation_error') {
      setBanner({ type: 'error', text: formatValidationErrors(result.validation) });
      return;
    }

    setBanner({ type: 'error', text: mapErrorCodeToMessage(result.error) });
  };

  const resetTutorState = () => {
    setChatMessages([]);
    setChatInput('');
    setChatStarted(false);
    setActivityCompleted(false);
    setMiniLesson('');
    setCurrentScore(0);
    setCompletedObjectives(0);
    setTotalObjectives(0);
  };

  const onLoadActivity = async (event) => {
    event.preventDefault();
    setBanner(null);

    const no = safeInt(activityNo, null);
    if (!courseId.trim() || !no) {
      setBanner({ type: 'error', text: 'Course ID and valid activity number are required.' });
      return;
    }

    setChatBusy(true);
    const result = await getActivity(credentials.email, credentials.password, courseId.trim(), no);
    if (UI_DEBUG) {
      console.log('[DEBUG][UI][StudentActivityPage] loadActivity result:', result);
    }
    if (!result.ok) {
      handleError(result);
      setChatBusy(false);
      return;
    }

    const loadedActivity = result.data.activity || null;
    const progress = result.data && result.data.progress ? result.data.progress : {};
    if (UI_DEBUG) {
      console.log('[DEBUG][UI][StudentActivityPage] progress after load:', progress);
    }
    setActivity(loadedActivity);
    resetTutorState();
    setCurrentScore(typeof progress.current_score === 'number' ? progress.current_score : 0);
    setCompletedObjectives(typeof progress.completed_count === 'number' ? progress.completed_count : 0);
    setTotalObjectives(typeof progress.total_objectives === 'number' ? progress.total_objectives : 0);
    setActivityCompleted(Boolean(progress.is_completed));
    setBanner({ type: 'success', text: 'Activity loaded. Start tutoring when ready.' });
    setChatBusy(false);
  };

  const applyToolResult = (toolResult) => {
    if (!toolResult || typeof toolResult !== 'object') {
      return;
    }

    if (toolResult.ok === true) {
      if (typeof toolResult.current_score === 'number') {
        setCurrentScore(toolResult.current_score);
      }
      if (typeof toolResult.completed_objectives === 'number') {
        setCompletedObjectives(toolResult.completed_objectives);
      }
      if (typeof toolResult.total_objectives === 'number') {
        setTotalObjectives(toolResult.total_objectives);
      }

      if (Number(toolResult.score_added || 0) > 0) {
        setBanner({
          type: 'success',
          text: `+${toolResult.score_added} point earned. Current score: ${toolResult.current_score}`,
        });
      } else if (toolResult.duplicate_objective === true) {
        setBanner({ type: 'info', text: 'Objective already scored before. No additional point added.' });
      }

      if (toolResult.activity_completed === true) {
        setActivityCompleted(true);
      }
    } else if (toolResult.error) {
      setBanner({ type: 'error', text: mapErrorCodeToMessage(toolResult.error) });
    }
  };

  const requestTutor = async (message, skipStudentBubble) => {
    if (!activity) {
      return false;
    }

    const no = safeInt(activityNo, null);
    if (!no) {
      return false;
    }

    const cleanMessage = String(message || '').trim();
    if (!cleanMessage) {
      return false;
    }

    setChatBusy(true);
    setBanner(null);

    if (!skipStudentBubble) {
      setChatMessages((prev) => [...prev, { role: 'student', text: cleanMessage }]);
    }

    const progressContext = {
      current_score: currentScore,
      completed_count: completedObjectives,
      total_objectives: totalObjectives,
      is_completed: activityCompleted,
    };

    const result = await tutorChat(
      credentials.email,
      credentials.password,
      courseId.trim(),
      no,
      cleanMessage,
      progressContext,
    );

    if (!result.ok) {
      handleError(result);
      if (result.error === 'activity_not_active' || result.error === 'activity_completed') {
        setActivityCompleted(true);
      }
      setChatBusy(false);
      return false;
    }

    const payload = result.data || {};
    const assistantResponse = payload.response ? String(payload.response) : 'No response text.';
    setChatMessages((prev) => [...prev, { role: 'assistant', text: assistantResponse }]);

    const nestedData = payload.data && typeof payload.data === 'object' ? payload.data : {};
    if (nestedData.mini_lesson) {
      setMiniLesson(String(nestedData.mini_lesson));
    }

    if (nestedData.tool_result) {
      applyToolResult(nestedData.tool_result);
    }

    if (nestedData.completed === true) {
      setActivityCompleted(true);
    }

    if (assistantResponse.toLowerCase().includes('activity is now complete')) {
      setActivityCompleted(true);
    }

    setChatBusy(false);
    return true;
  };

  const onStartTutoring = async () => {
    if (!activity || chatStarted) {
      return;
    }
    setChatStarted(true);
    const ok = await requestTutor('I am ready to start the activity. Please ask the first question.', true);
    if (!ok) {
      setChatStarted(false);
    }
  };

  const onSendMessage = async (event) => {
    event.preventDefault();
    if (!chatInput.trim()) {
      return;
    }

    const message = chatInput.trim();
    setChatInput('');
    await requestTutor(message, false);
  };

  const onChangePassword = async (event) => {
    event.preventDefault();
    setBanner(null);

    if (!oldPassword || !newPassword) {
      setBanner({ type: 'error', text: 'Old and new password are required.' });
      return;
    }

    setPasswordBusy(true);
    const result = await changeStudentPassword(
      credentials.email,
      credentials.password,
      oldPassword,
      newPassword,
    );

    if (!result.ok) {
      handleError(result);
      setPasswordBusy(false);
      return;
    }

    updateUser({ password: newPassword });
    setOldPassword('');
    setNewPassword('');
    setBanner({ type: 'success', text: 'Password updated. Session password refreshed.' });
    setPasswordBusy(false);
  };

  return (
    <div className="workspace-grid">
      {banner ? (
        <div className={`alert ${banner.type === 'error' ? 'alert-error' : banner.type === 'success' ? 'alert-success' : 'alert-info'}`}>
          {banner.text}
        </div>
      ) : null}

      <section className="panel panel-span-2">
        <div className="panel-header">
          <h3>Activity Access</h3>
          {activity ? <StatusBadge status={activity.status} /> : null}
        </div>

        <form className="row row-gap" onSubmit={onLoadActivity}>
          <label className="field grow">
            <span>Course ID</span>
            <input
              value={courseId}
              onChange={(event) => setCourseId(event.target.value)}
              placeholder="22222222-2222-2222-2222-222222222222"
              required
            />
          </label>

          <label className="field">
            <span>Activity No</span>
            <input
              value={activityNo}
              onChange={(event) => setActivityNo(event.target.value)}
              placeholder="1"
              required
            />
          </label>

          <div className="button-row">
            <Button type="submit" loading={chatBusy}>
              Load Activity
            </Button>
          </div>
        </form>

        {activity ? (
          <div className="activity-card">
            <h4>Activity Text</h4>
            <p>{activity.text}</p>
            <p className="muted">
              Learning objectives are intentionally hidden in student UI during tutoring.
            </p>
          </div>
        ) : null}
      </section>

      <section className="panel">
        <div className="panel-header">
          <h3>Progress</h3>
        </div>

        <div className="metric-grid">
          <div className="metric-item">
            <span>Current Score</span>
            <strong>{currentScore}</strong>
          </div>
          <div className="metric-item">
            <span>Objectives Covered</span>
            <strong>{completedObjectives}</strong>
          </div>
          <div className="metric-item">
            <span>Total Objectives</span>
            <strong>{totalObjectives}</strong>
          </div>
          <div className="metric-item">
            <span>Activity Completed</span>
            <strong>{activityCompleted ? 'Yes' : 'No'}</strong>
          </div>
        </div>

        {miniLesson ? (
          <div className="mini-lesson">
            <h4>Mini Lesson</h4>
            <p>{miniLesson}</p>
          </div>
        ) : null}
      </section>

      <section className="panel panel-span-2">
        <div className="panel-header">
          <h3>Tutoring Chat</h3>
          <div className="button-row">
            <Button
              variant="secondary"
              onClick={onStartTutoring}
              disabled={!activity || chatStarted || activityCompleted}
              loading={chatBusy}
            >
              Start Tutoring
            </Button>
          </div>
        </div>

        <div className="chat-box">
          {chatMessages.length === 0 ? (
            <div className="chat-empty">Load activity and click Start Tutoring to begin.</div>
          ) : (
            chatMessages.map((item, idx) => (
              <ChatBubble key={`msg-${idx}`} role={item.role} text={item.text} />
            ))
          )}
        </div>

        <form className="chat-form" onSubmit={onSendMessage}>
          <input
            value={chatInput}
            onChange={(event) => setChatInput(event.target.value)}
            placeholder={activityCompleted ? 'Activity completed.' : 'Type your answer...'}
            disabled={!activity || !chatStarted || activityCompleted || chatBusy}
          />
          <Button type="submit" disabled={!activity || !chatStarted || activityCompleted} loading={chatBusy}>
            Send
          </Button>
        </form>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h3>Change Password</h3>
        </div>

        <form className="form-grid" onSubmit={onChangePassword}>
          <label className="field">
            <span>Old Password</span>
            <input
              type="password"
              value={oldPassword}
              onChange={(event) => setOldPassword(event.target.value)}
              required
            />
          </label>

          <label className="field">
            <span>New Password</span>
            <input
              type="password"
              value={newPassword}
              onChange={(event) => setNewPassword(event.target.value)}
              required
            />
          </label>

          <Button type="submit" loading={passwordBusy}>
            Update Password
          </Button>
        </form>
      </section>
    </div>
  );
}
