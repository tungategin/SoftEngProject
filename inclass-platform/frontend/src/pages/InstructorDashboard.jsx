import React, { useEffect, useMemo, useState } from 'react';
import Button from '../components/Button';
import StatusBadge from '../components/StatusBadge';
import {
  createActivity,
  endActivity,
  exportScores,
  listActivities,
  listCourses,
  manualGrade,
  resetActivity,
  startActivity,
  updateActivity,
} from '../api/instructorApi';
import { useAuth } from '../context/AuthContext';
import {
  downloadTextFile,
  formatValidationErrors,
  mapErrorCodeToMessage,
  parseObjectives,
  safeInt,
  safeJsonObject,
} from '../utils/helpers';

const COURSE_ID_PLACEHOLDER = '00000000-0000-0000-0000-000000000000';
const UI_DEBUG = String(import.meta.env.VITE_UI_DEBUG || 'true').toLowerCase() === 'true';

function getCourseName(course) {
  if (!course || typeof course !== 'object') {
    return 'Unknown course';
  }
  if (course.title) {
    return String(course.title);
  }
  if (course.course_code) {
    return `${course.course_code}${course.section ? ` / ${course.section}` : ''}`;
  }
  if (course.id) {
    return String(course.id);
  }
  return 'Untitled course';
}

export default function InstructorDashboard() {
  const { user } = useAuth();

  const [courses, setCourses] = useState([]);
  const [selectedCourseId, setSelectedCourseId] = useState('');
  const [activities, setActivities] = useState([]);
  const [selectedActivityNo, setSelectedActivityNo] = useState('');

  const [createText, setCreateText] = useState('');
  const [createObjectives, setCreateObjectives] = useState('');
  const [createActivityNo, setCreateActivityNo] = useState('');

  const [updateActivityNo, setUpdateActivityNo] = useState('');
  const [updateText, setUpdateText] = useState('');
  const [updateObjectives, setUpdateObjectives] = useState('');
  const [updateStatus, setUpdateStatus] = useState('');

  const [manualActivityNo, setManualActivityNo] = useState('');
  const [manualStudentEmail, setManualStudentEmail] = useState('');
  const [manualScore, setManualScore] = useState('1');
  const [manualReason, setManualReason] = useState('');
  const [manualMeta, setManualMeta] = useState('');

  const [exportRows, setExportRows] = useState([]);

  const [busyAction, setBusyAction] = useState('');
  const [banner, setBanner] = useState(null);

  const credentials = useMemo(
    () => ({
      email: user ? user.email : '',
      password: user ? user.password : '',
    }),
    [user],
  );

  const setErrorBanner = (result) => {
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

  const refreshCourses = async () => {
    if (!credentials.email || !credentials.password) {
      if (UI_DEBUG) {
        console.log('[DEBUG][UI][InstructorDashboard] refreshCourses skipped: missing credentials');
      }
      return;
    }

    setBusyAction('courses');
    if (UI_DEBUG) {
      console.log('[DEBUG][UI][InstructorDashboard] refreshCourses request', {
        email: credentials.email,
        selectedCourseId,
        placeholderUsed: !selectedCourseId,
      });
    }
    const result = await listCourses(
      credentials.email,
      credentials.password,
      selectedCourseId || COURSE_ID_PLACEHOLDER,
    );
    if (UI_DEBUG) {
      console.log('[DEBUG][UI][InstructorDashboard] refreshCourses response', result);
    }

    if (!result.ok) {
      setErrorBanner(result);
      setBusyAction('');
      return;
    }

    const loadedCourses = Array.isArray(result.data.courses) ? result.data.courses : [];
    if (UI_DEBUG) {
      console.log('[DEBUG][UI][InstructorDashboard] loadedCourses count', loadedCourses.length, loadedCourses);
    }
    setCourses(loadedCourses);

    if (!selectedCourseId && loadedCourses.length > 0) {
      const firstId = loadedCourses[0] && loadedCourses[0].id ? String(loadedCourses[0].id) : '';
      setSelectedCourseId(firstId);
      if (UI_DEBUG) {
        console.log('[DEBUG][UI][InstructorDashboard] auto-selected first course', firstId);
      }
    }

    if (loadedCourses.length === 0) {
      setBanner({
        type: 'info',
        text: 'No authorized courses returned for this instructor. Check backend course_authorizations data.',
      });
    }

    setBusyAction('');
  };

  const refreshActivities = async (courseId) => {
    if (!courseId || !credentials.email || !credentials.password) {
      if (UI_DEBUG) {
        console.log('[DEBUG][UI][InstructorDashboard] refreshActivities skipped', {
          courseId,
          hasEmail: Boolean(credentials.email),
          hasPassword: Boolean(credentials.password),
        });
      }
      setActivities([]);
      return;
    }

    setBusyAction('activities');
    if (UI_DEBUG) {
      console.log('[DEBUG][UI][InstructorDashboard] refreshActivities request', {
        email: credentials.email,
        courseId,
      });
    }
    const result = await listActivities(credentials.email, credentials.password, courseId);
    if (UI_DEBUG) {
      console.log('[DEBUG][UI][InstructorDashboard] refreshActivities response', result);
    }

    if (!result.ok) {
      setErrorBanner(result);
      setBusyAction('');
      return;
    }

    const loadedActivities = Array.isArray(result.data.activities) ? result.data.activities : [];
    if (UI_DEBUG) {
      console.log('[DEBUG][UI][InstructorDashboard] loadedActivities count', loadedActivities.length, loadedActivities);
    }
    setActivities(loadedActivities);
    setBusyAction('');
  };

  const refreshExportPreview = async (courseId, activityNo) => {
    const parsedActivityNo = safeInt(activityNo, null);
    if (!courseId || !parsedActivityNo || !credentials.email || !credentials.password) {
      return;
    }

    if (UI_DEBUG) {
      console.log('[DEBUG][UI][InstructorDashboard] refreshExportPreview request', {
        courseId,
        activityNo: parsedActivityNo,
      });
    }

    const result = await exportScores(
      credentials.email,
      credentials.password,
      courseId,
      parsedActivityNo,
    );

    if (UI_DEBUG) {
      console.log('[DEBUG][UI][InstructorDashboard] refreshExportPreview response', result);
    }

    if (!result.ok) {
      return;
    }

    const rows = Array.isArray(result.data.rows) ? result.data.rows : [];
    setExportRows(rows);
  };

  useEffect(() => {
    void refreshCourses();
  }, []);

  useEffect(() => {
    if (selectedCourseId) {
      void refreshActivities(selectedCourseId);
    }
  }, [selectedCourseId]);

  const onSelectActivity = (activity) => {
    if (!activity) {
      return;
    }

    const no = String(activity.activity_no || '');
    setSelectedActivityNo(no);
    setUpdateActivityNo(no);
    setManualActivityNo(no);
    setUpdateText(activity.text ? String(activity.text) : '');
    setUpdateObjectives(Array.isArray(activity.learning_objectives) ? activity.learning_objectives.join('\n') : '');
    setUpdateStatus(activity.status ? String(activity.status) : '');
    void refreshExportPreview(selectedCourseId, no);
  };

  const onCreateActivity = async (event) => {
    event.preventDefault();
    setBanner(null);

    if (!selectedCourseId) {
      setBanner({ type: 'error', text: 'Select a course first.' });
      return;
    }

    const objectives = parseObjectives(createObjectives);
    if (!createText.trim() || objectives.length === 0) {
      setBanner({ type: 'error', text: 'Activity text and at least one objective are required.' });
      return;
    }

    const noOptional = createActivityNo.trim() ? safeInt(createActivityNo, null) : null;

    setBusyAction('create');
    const result = await createActivity(
      credentials.email,
      credentials.password,
      selectedCourseId,
      createText.trim(),
      objectives,
      noOptional,
    );

    if (!result.ok) {
      setErrorBanner(result);
      setBusyAction('');
      return;
    }

    setBanner({ type: 'success', text: 'Activity created successfully.' });
    setCreateText('');
    setCreateObjectives('');
    setCreateActivityNo('');
    await refreshActivities(selectedCourseId);
    setBusyAction('');
  };

  const onUpdateActivity = async (event) => {
    event.preventDefault();
    setBanner(null);

    const activityNo = safeInt(updateActivityNo, null);
    if (!selectedCourseId || !activityNo) {
      setBanner({ type: 'error', text: 'Select course and valid activity number.' });
      return;
    }

    const patch = {};
    if (updateText.trim()) {
      patch.text = updateText.trim();
    }
    if (updateObjectives.trim()) {
      patch.learning_objectives = parseObjectives(updateObjectives);
    }
    if (updateStatus) {
      patch.status = updateStatus;
    }

    if (Object.keys(patch).length === 0) {
      setBanner({ type: 'error', text: 'Provide at least one field for patch.' });
      return;
    }

    setBusyAction('update');
    const result = await updateActivity(
      credentials.email,
      credentials.password,
      selectedCourseId,
      activityNo,
      patch,
    );

    if (!result.ok) {
      setErrorBanner(result);
      setBusyAction('');
      return;
    }

    setBanner({ type: 'success', text: 'Activity updated.' });
    await refreshActivities(selectedCourseId);
    setBusyAction('');
  };

  const runActivityAction = async (actionType) => {
    const activityNo = safeInt(selectedActivityNo, null);

    if (!selectedCourseId || !activityNo) {
      setBanner({ type: 'error', text: 'Select an activity first.' });
      return;
    }

    if (actionType === 'reset') {
      const confirmed = window.confirm('Reset activity will delete score logs and close the activity. Continue?');
      if (!confirmed) {
        return;
      }
    }

    setBusyAction(actionType);

    let result;
    if (actionType === 'start') {
      result = await startActivity(credentials.email, credentials.password, selectedCourseId, activityNo);
    } else if (actionType === 'end') {
      result = await endActivity(credentials.email, credentials.password, selectedCourseId, activityNo);
    } else if (actionType === 'reset') {
      result = await resetActivity(credentials.email, credentials.password, selectedCourseId, activityNo);
    } else if (actionType === 'export') {
      result = await exportScores(credentials.email, credentials.password, selectedCourseId, activityNo);
    }

    if (!result || !result.ok) {
      setErrorBanner(result);
      setBusyAction('');
      return;
    }

    if (actionType === 'export') {
      const csv = result.data.csv || '';
      const rows = Array.isArray(result.data.rows) ? result.data.rows : [];
      setExportRows(rows);
      downloadTextFile(`scores-course-${selectedCourseId}-activity-${activityNo}.csv`, csv);
      setBanner({ type: 'success', text: 'Scores exported and download started.' });
    } else if (actionType === 'reset') {
      setBanner({
        type: 'success',
        text: `Reset complete. Deleted ${result.data.deleted_count || 0} score logs.`,
      });
      setExportRows([]);
      await refreshActivities(selectedCourseId);
    } else {
      setBanner({
        type: 'success',
        text: actionType === 'start' ? 'Activity started.' : 'Activity ended.',
      });
      await refreshActivities(selectedCourseId);
    }

    setBusyAction('');
  };

  const onManualGrade = async (event) => {
    event.preventDefault();
    setBanner(null);

    const activityNo = safeInt(manualActivityNo || selectedActivityNo, null);
    const scoreValue = safeInt(manualScore, null);

    if (!selectedCourseId || !activityNo) {
      if (UI_DEBUG) {
        console.log('[DEBUG][UI][InstructorDashboard] manualGrade blocked: missing course/activity', {
          selectedCourseId,
          manualActivityNo,
          selectedActivityNo,
        });
      }
      setBanner({ type: 'error', text: 'Course and activity number are required.' });
      return;
    }

    if (!manualStudentEmail.trim() || !manualReason.trim() || scoreValue === null || scoreValue === 0) {
      setBanner({ type: 'error', text: 'Student email, reason and non-zero score are required.' });
      return;
    }

    setBusyAction('manual-grade');
    if (UI_DEBUG) {
      console.log('[DEBUG][UI][InstructorDashboard] manualGrade request', {
        courseId: selectedCourseId,
        activityNo,
        studentEmail: manualStudentEmail.trim(),
        scoreValue,
      });
    }
    const result = await manualGrade(
      credentials.email,
      credentials.password,
      selectedCourseId,
      activityNo,
      manualStudentEmail.trim(),
      scoreValue,
      manualReason.trim(),
      safeJsonObject(manualMeta),
    );
    if (UI_DEBUG) {
      console.log('[DEBUG][UI][InstructorDashboard] manualGrade response', result);
    }

    if (!result.ok) {
      setErrorBanner(result);
      setBusyAction('');
      return;
    }

    const finalScore = result.data && typeof result.data.current_score === 'number' ? result.data.current_score : null;
    setBanner({
      type: 'success',
      text: finalScore === null
        ? 'Manual grade submitted.'
        : `Manual grade submitted. Student final score is now ${finalScore}.`,
    });
    setManualMeta('');
    await refreshExportPreview(selectedCourseId, activityNo);
    await refreshActivities(selectedCourseId);
    setBusyAction('');
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
          <h3>Course & Activity Control</h3>
          <Button variant="secondary" onClick={() => void refreshCourses()} loading={busyAction === 'courses'}>
            Refresh Courses
          </Button>
        </div>

        <div className="row row-gap">
          <label className="field grow">
            <span>Course</span>
            <select
              value={selectedCourseId}
              onChange={(event) => setSelectedCourseId(event.target.value)}
            >
              <option value="">Select course</option>
              {courses.map((course) => (
                <option key={String(course.id)} value={String(course.id)}>
                  {getCourseName(course)}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>Selected Activity No</span>
            <input
              value={selectedActivityNo}
              onChange={(event) => setSelectedActivityNo(event.target.value)}
              placeholder="1"
            />
          </label>

          <div className="button-row">
            <Button onClick={() => void runActivityAction('start')} loading={busyAction === 'start'}>
              Start
            </Button>
            <Button variant="secondary" onClick={() => void runActivityAction('end')} loading={busyAction === 'end'}>
              End
            </Button>
            <Button variant="danger" onClick={() => void runActivityAction('reset')} loading={busyAction === 'reset'}>
              Reset
            </Button>
            <Button variant="ghost" onClick={() => void runActivityAction('export')} loading={busyAction === 'export'}>
              Export Scores
            </Button>
          </div>
        </div>
      </section>

      <section className="panel panel-span-2">
        <div className="panel-header">
          <h3>Activities</h3>
          <Button variant="secondary" onClick={() => void refreshActivities(selectedCourseId)} loading={busyAction === 'activities'}>
            Refresh Activities
          </Button>
        </div>

        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>No</th>
                <th>Status</th>
                <th>Text</th>
                <th>Objectives</th>
              </tr>
            </thead>
            <tbody>
              {activities.length === 0 ? (
                <tr>
                  <td colSpan="4">No activities yet for this course.</td>
                </tr>
              ) : (
                activities.map((activity) => (
                  <tr key={`${activity.course_id}-${activity.activity_no}`} onClick={() => onSelectActivity(activity)}>
                    <td>{activity.activity_no}</td>
                    <td><StatusBadge status={activity.status} /></td>
                    <td className="clip-text">{activity.text}</td>
                    <td>{Array.isArray(activity.learning_objectives) ? activity.learning_objectives.length : 0}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h3>Create Activity</h3>
        </div>

        <form className="form-grid" onSubmit={onCreateActivity}>
          <label className="field">
            <span>Activity Text</span>
            <textarea
              rows="5"
              value={createText}
              onChange={(event) => setCreateText(event.target.value)}
              placeholder="Write activity text"
              required
            />
          </label>

          <label className="field">
            <span>Learning Objectives (one per line)</span>
            <textarea
              rows="4"
              value={createObjectives}
              onChange={(event) => setCreateObjectives(event.target.value)}
              placeholder="Objective 1&#10;Objective 2"
              required
            />
          </label>

          <label className="field">
            <span>Activity No (optional)</span>
            <input
              value={createActivityNo}
              onChange={(event) => setCreateActivityNo(event.target.value)}
              placeholder="Leave empty for auto"
            />
          </label>

          <Button type="submit" loading={busyAction === 'create'}>
            Create Activity
          </Button>
        </form>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h3>Update Activity</h3>
        </div>

        <form className="form-grid" onSubmit={onUpdateActivity}>
          <label className="field">
            <span>Activity No</span>
            <input
              value={updateActivityNo}
              onChange={(event) => setUpdateActivityNo(event.target.value)}
              placeholder="1"
              required
            />
          </label>

          <label className="field">
            <span>Patch Text</span>
            <textarea
              rows="3"
              value={updateText}
              onChange={(event) => setUpdateText(event.target.value)}
              placeholder="Optional"
            />
          </label>

          <label className="field">
            <span>Patch Objectives (optional)</span>
            <textarea
              rows="3"
              value={updateObjectives}
              onChange={(event) => setUpdateObjectives(event.target.value)}
              placeholder="Objective A&#10;Objective B"
            />
          </label>

          <label className="field">
            <span>Patch Status (optional)</span>
            <select value={updateStatus} onChange={(event) => setUpdateStatus(event.target.value)}>
              <option value="">No status update</option>
              <option value="NOT_STARTED">NOT_STARTED</option>
              <option value="ACTIVE">ACTIVE</option>
              <option value="ENDED">ENDED</option>
            </select>
          </label>

          <Button type="submit" variant="secondary" loading={busyAction === 'update'}>
            Update Activity
          </Button>
        </form>
      </section>

      <section className="panel panel-span-2">
        <div className="panel-header">
          <h3>Manual Grade (US-L)</h3>
        </div>

        <form className="form-grid form-grid-2" onSubmit={onManualGrade}>
          <label className="field">
            <span>Activity No</span>
            <input
              value={manualActivityNo}
              onChange={(event) => setManualActivityNo(event.target.value)}
              placeholder="1"
              required
            />
          </label>

          <label className="field">
            <span>Student Email</span>
            <input
              type="email"
              value={manualStudentEmail}
              onChange={(event) => setManualStudentEmail(event.target.value)}
              placeholder="student@example.com"
              required
            />
          </label>

          <label className="field">
            <span>Manual Score (target/final integer)</span>
            <input
              value={manualScore}
              onChange={(event) => setManualScore(event.target.value)}
              placeholder="4"
              required
            />
          </label>

          <label className="field">
            <span>Reason</span>
            <input
              value={manualReason}
              onChange={(event) => setManualReason(event.target.value)}
              placeholder="Exceptional classroom case"
              required
            />
          </label>

          <label className="field panel-span-2">
            <span>Meta (optional JSON or free text)</span>
            <textarea
              rows="2"
              value={manualMeta}
              onChange={(event) => setManualMeta(event.target.value)}
              placeholder='{"note":"late join"}'
            />
          </label>

          <Button type="submit" loading={busyAction === 'manual-grade'}>
            Submit Manual Grade
          </Button>
        </form>
      </section>

      <section className="panel panel-span-2">
        <div className="panel-header">
          <h3>Export Preview</h3>
          <p className="muted">Latest exported rows from backend response.</p>
        </div>

        <div className="table-wrap compact-table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Student Email</th>
                <th>Score</th>
                <th>Meta</th>
              </tr>
            </thead>
            <tbody>
              {exportRows.length === 0 ? (
                <tr>
                  <td colSpan="3">No exported rows yet.</td>
                </tr>
              ) : (
                exportRows.map((row, idx) => (
                  <tr key={`exp-${idx}`}>
                    <td>{row.student_email}</td>
                    <td>{row.score}</td>
                    <td>{row.meta}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
