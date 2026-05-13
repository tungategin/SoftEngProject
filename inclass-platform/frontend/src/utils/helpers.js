export function parseObjectives(raw) {
  if (!raw || typeof raw !== 'string') {
    return [];
  }

  return raw
    .split(/\n|;/)
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
}

export function safeInt(value, fallbackValue) {
  const num = Number(value);
  if (Number.isFinite(num)) {
    return Math.trunc(num);
  }
  return fallbackValue;
}

export function safeJsonObject(raw) {
  if (!raw || typeof raw !== 'string') {
    return null;
  }
  const trimmed = raw.trim();
  if (trimmed.length === 0) {
    return null;
  }

  try {
    const parsed = JSON.parse(trimmed);
    if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
      return parsed;
    }
    return null;
  } catch (error) {
    return { note: trimmed };
  }
}

export function statusLabel(status) {
  if (!status) {
    return 'Unknown';
  }

  if (status === 'NOT_STARTED') {
    return 'Not Started';
  }

  if (status === 'ACTIVE') {
    return 'Active';
  }

  if (status === 'ENDED') {
    return 'Ended';
  }

  return String(status);
}

export function mapErrorCodeToMessage(errorCode) {
  const map = {
    invalid_credentials: 'Email or password is invalid.',
    forbidden_role: 'Your account role cannot access this page.',
    course_access_denied: 'You are not authorized for this course.',
    activity_not_found: 'Requested activity was not found.',
    activity_not_active: 'This activity is not active right now.',
    activity_completed: 'This activity has already been completed.',
    objective_not_found: 'Could not map this answer to an objective.',
    duplicate_objective: 'This objective was already scored earlier.',
    score_log_insert_failed: 'Score could not be saved right now.',
    manual_grade_event_insert_failed: 'Manual grade event could not be saved.',
    invalid_manual_score: 'Manual score must be a non-zero integer.',
    student_not_found: 'Student account was not found.',
    student_not_in_course: 'Student is not enrolled in this course.',
    update_failed: 'Update failed. Please try again.',
    empty_patch: 'Please provide at least one field to update.',
    activity_already_exists: 'Activity number already exists in this course.',
    activity_already_active: 'Activity is already active.',
    activity_already_ended: 'Activity is already ended.',
    activity_reset_failed: 'Activity reset failed.',
    network_error: 'Network error. Check backend status and try again.',
    validation_error: 'Form validation failed. Check the required fields.',
    invalid_json: 'Tutor response format was invalid. Please retry your last message.',
    operation_failed: 'Operation failed.',
    request_failed: 'Request failed.',
    invalid_response: 'Unexpected response from backend.',
  };

  return map[errorCode] || `Operation failed: ${errorCode || 'unknown_error'}`;
}

export function formatValidationErrors(validation) {
  if (!Array.isArray(validation) || validation.length === 0) {
    return 'Validation failed.';
  }

  return validation
    .map((item) => {
      const loc = Array.isArray(item.loc) ? item.loc.join('.') : 'field';
      const msg = item.msg || 'invalid value';
      return `${loc}: ${msg}`;
    })
    .join(' | ');
}

export function downloadTextFile(filename, content) {
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const href = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = href;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(href);
}

export function normalizeRole(role) {
  const value = String(role || '').toLowerCase();
  if (value === 'student' || value === 'instructor') {
    return value;
  }
  return '';
}
