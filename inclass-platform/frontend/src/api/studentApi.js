import { postJson } from './client';

export function getActivity(email, password, courseId, activityNo) {
  return postJson('/student/get-activity', {
    email,
    password,
    course_id: courseId,
    activity_no: activityNo,
  });
}

export function tutorChat(email, password, courseId, activityNo, message, progressContext) {
  return postJson('/student/tutor-chat', {
    email,
    password,
    course_id: courseId,
    activity_no: activityNo,
    message,
    progress_context: progressContext || null,
  });
}

export function logScore(email, password, courseId, activityNo, score, meta) {
  return postJson('/student/log-score', {
    email,
    password,
    course_id: courseId,
    activity_no: activityNo,
    score,
    meta: meta || null,
  });
}
