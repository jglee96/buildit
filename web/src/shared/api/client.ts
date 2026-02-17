import { ProjectRead, RunRead, UserRead } from '@/entities/run'

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://127.0.0.1:8000/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {})
    }
  })

  if (!res.ok) {
    const body = await res.text()
    throw new Error(body || `Request failed: ${res.status}`)
  }

  return (await res.json()) as T
}

export function createUser(email: string, name: string): Promise<UserRead> {
  return request('/users', { method: 'POST', body: JSON.stringify({ email, name }) })
}

export function createRuleSet(payload: Record<string, unknown>): Promise<{ id: string }> {
  return request('/rules/sets', { method: 'POST', body: JSON.stringify(payload) })
}

export function createRuleDefinition(payload: Record<string, unknown>): Promise<{ id: string }> {
  return request('/rules/definitions', { method: 'POST', body: JSON.stringify(payload) })
}

export function createProject(payload: Record<string, unknown>): Promise<ProjectRead> {
  return request('/projects', { method: 'POST', body: JSON.stringify(payload) })
}

export function setRequirements(projectId: string, payload: Record<string, unknown>[]): Promise<Record<string, unknown>[]> {
  return request(`/projects/${projectId}/requirements`, { method: 'POST', body: JSON.stringify(payload) })
}

export function runEvaluation(projectId: string, payload: Record<string, unknown>): Promise<RunRead> {
  return request(`/runs/projects/${projectId}/evaluate`, { method: 'POST', body: JSON.stringify(payload) })
}

export function getRun(runId: string): Promise<RunRead> {
  return request(`/runs/${runId}`)
}
