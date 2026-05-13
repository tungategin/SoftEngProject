import { postJson } from './client';

export function studentLogin(email, password) {
  return postJson('/student/login', { email, password });
}

export function instructorLogin(email, password) {
  return postJson('/instructor/login', { email, password });
}

export function changeStudentPassword(email, password, oldPassword, newPassword) {
  return postJson('/student/change-password', {
    email,
    password,
    old_password: oldPassword,
    new_password: newPassword,
  });
}
