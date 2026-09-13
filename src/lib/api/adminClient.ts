import { API_BASE } from './apiBase';

export interface AdminUserDTO {
	id: number;
	email: string;
	created_at: string;
	is_admin: boolean;
	recipe_count: number;
	ingredient_count: number;
	other_cost_count: number;
}

export async function fetchAdminUsers(token: string): Promise<AdminUserDTO[]> {
	const res = await fetch(`${API_BASE}/admin/users`, {
		headers: { Authorization: `Bearer ${token}` }
	});
	if (!res.ok) throw new Error('Failed to fetch admin users');
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
