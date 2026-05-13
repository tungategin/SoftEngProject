import { postJson } from './client';

const COURSE_ID_PLACEHOLDER = '00000000-0000-0000-0000-000000000000';

export function listCourses(email, password, courseId) {
  return postJson('/instructor/list-courses', {
    email,
    password,
    course_id: courseId || COURSE_ID_PLACEHOLDER,
  });
}

export function listActivities(email, password, courseId) {
  return postJson('/instructor/list-activities', {
    email,
    password,
    course_id: courseId,
  });
}

export function createActivity(email, password, courseId, activityText, learningObjectives, activityNoOptional) {
  return postJson('/instructor/create-activity', {
    email,
    password,
    course_id: courseId,
    activity_text: activityText,
    learning_objectives: learningObjectives,
    activity_no_optional: activityNoOptional,
  });
}

export function updateActivity(email, password, courseId, activityNo, patch) {
  return postJson('/instructor/update-activity', {
    email,
    password,
    course_id: courseId,
    activity_no: activityNo,
    patch,
  });
}

export function startActivity(email, password, courseId, activityNo) {
  return postJson('/instructor/start-activity', {
    email,
    password,
    course_id: courseId,
    activity_no: activityNo,
  });
}

export function endActivity(email, password, courseId, activityNo) {
  return postJson('/instructor/end-activity', {
    email,
    password,
    course_id: courseId,
    activity_no: activityNo,
  });
}

export function exportScores(email, password, courseId, activityNo) {
  return postJson('/instructor/export-scores', {
    email,
    password,
    course_id: courseId,
    activity_no: activityNo,
  });
}

export function manualGrade(email, password, courseId, activityNo, studentEmail, manualScore, reason, meta) {
  return postJson('/instructor/manual-grade', {
    email,
    password,
    course_id: courseId,
    activity_no: activityNo,
    student_email: studentEmail,
    manual_score: manualScore,
    reason,
    meta: meta || null,
  });
}

export function resetActivity(email, password, courseId, activityNo) {
  return postJson('/instructor/reset-activity', {
    email,
    password,
    course_id: courseId,
    activity_no: activityNo,
  });
}
