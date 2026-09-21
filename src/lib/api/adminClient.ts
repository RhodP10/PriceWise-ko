import { API_BASE } from './apiBase';

export interface AdminUserDTO {
	id: number;
	email: string;
	username?: string | null;
	role?: string;
	created_at: string;
	is_admin: boolean;
	admin_id?: number | null;
	recipe_count: number;
	ingredient_count: number;
	other_cost_count: number;
}

export interface EmployeeDTO {
	id: number;
	username: string;
	created_at: string;
	role: string;
	admin_id: number;
}

export async function fetchAdminUsers(token: string): Promise<AdminUserDTO[]> {
	const res = await fetch(`${API_BASE}/admin/users`, {
		headers: { Authorization: `Bearer ${token}` }
	});
	if (!res.ok) throw new Error('Failed to fetch users');
	return await res.json();
}

export async function deleteAdminUser(token: string, userId: number): Promise<void> {
	const res = await fetch(`${API_BASE}/admin/users/${userId}`, {
		method: 'DELETE',
		headers: { Authorization: `Bearer ${token}` }
	});
	if (!res.ok) {
		const text = await res.text();
		throw new Error(text || 'Failed to delete user');
	}
}

export async function fetchEmployees(token: string): Promise<EmployeeDTO[]> {
	const res = await fetch(`${API_BASE}/admin/employees`, {
		headers: { Authorization: `Bearer ${token}` }
	});
	if (!res.ok) throw new Error('Failed to fetch employees');
	return await res.json();
}

export async function createEmployee(
	token: string,
	payload: { username: string; password: string }
): Promise<EmployeeDTO> {
	const res = await fetch(`${API_BASE}/admin/employees`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify(payload)
	});
	if (!res.ok) {
		let errMsg = 'Failed to create employee';
		try {
			const err = await res.json();
			if (err.detail) {
				errMsg = typeof err.detail === 'string' ? err.detail : JSON.stringify(err.detail);
			}
		} catch {
			const text = await res.text();
			if (text) errMsg = text;
		}
		throw new Error(errMsg);
	}
	return await res.json();
}

export async function deleteEmployee(token: string, employeeId: number): Promise<void> {
	const res = await fetch(`${API_BASE}/admin/employees/${employeeId}`, {
		method: 'DELETE',
		headers: { Authorization: `Bearer ${token}` }
	});
	if (!res.ok) {
		const text = await res.text();
		throw new Error(text || 'Failed to delete employee');
	}
}
