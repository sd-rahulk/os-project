export const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8765'

export type Metrics = { cpu_percent?: number | null; memory_percent?: number | null; memory_available?: number | null; disk_percent?: number | null; upload_bps?: number | null; download_bps?: number | null; uptime_seconds?: number | null }
export type Device = { device_id:string; name:string; os_name:string; os_version:string; architecture:string; agent_version:string; ip_address:string|null; approved:boolean; status:string; last_seen_at:string|null; last_heartbeat_at:string|null; metrics:Metrics }
export type Process = { pid:number; name:string; executable:string|null; username:string|null; status:string|null; create_time:number; ppid:number|null; thread_count:number|null; memory_bytes:number|null; memory_percent:number|null; priority:string|number|null; cpu_affinity:number[]|null; cpu_percent:number|null }

export async function request<T>(path:string, init:RequestInit = {}, token?:string):Promise<T> {
  const response = await fetch(`${API}${path}`, { ...init, headers: { 'Content-Type':'application/json', ...(token ? { Authorization:`Bearer ${token}` } : {}), ...(init.headers ?? {}) }, cache:'no-store' })
  if (!response.ok) { const body = await response.json().catch(() => ({})); throw new Error(body.detail ?? `Request failed (${response.status})`) }
  return response.json()
}
