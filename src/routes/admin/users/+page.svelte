<script lang="ts">
	import { type AdminUserDTO, fetchAdminUsers, deleteAdminUser } from '$lib/api/adminClient';
	import TypeToConfirmDeleteModal from '$lib/components/TypeToConfirmDeleteModal.svelte';
	import { authState } from '$lib/state/auth.svelte';

	let users = $state<AdminUserDTO[]>([]);
	let loading = $state(true);
	let error = $state('');

	let deleteModalOpen = $state(false);
	let userToDelete = $state<AdminUserDTO | null>(null);
	let deleting = $state(false);

	let hasLoaded = $state(false);

	async function loadUsers(): Promise<void> {
		try {
			loading = true;
			error = '';
			const token = authState.token;
			if (!token) return;
			users = await fetchAdminUsers(token);
			hasLoaded = true;
		} catch (e: any) {
			error = e.message;
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		if (authState.token && !hasLoaded) {
			void loadUsers();
		}
	});

	function askDelete(u: AdminUserDTO): void {
		userToDelete = u;
		deleteModalOpen = true;
	}

	async function confirmDelete(): Promise<void> {
		if (!userToDelete) return;
		const token = authState.token;
		if (!token) {
			alert('Not authenticated. Please log in again.');
			return;
		}
		try {
			deleting = true;
			await deleteAdminUser(token, userToDelete.id);
			deleteModalOpen = false;
			userToDelete = null;
			try {
				users = await fetchAdminUsers(token);
			} catch {
				// Silently ignore reload errors
			}
		} catch (e: any) {
			alert('Failed to delete user: ' + e.message);
		} finally {
			deleting = false;
		}
	}
</script>

<svelte:head>
	<title>Super Admin - Platform Accounts</title>
</svelte:head>

<section class="animate-in relative space-y-8 pb-10">
	<div class="relative overflow-hidden rounded-3xl bg-zinc-900 p-8 text-white shadow-2xl lg:p-12">
		<div class="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-orange-500/20 blur-3xl"></div>
		<div class="absolute -bottom-20 -left-20 h-64 w-64 rounded-full bg-purple-500/10 blur-3xl"></div>
		
		<div class="relative z-10 flex flex-col gap-4">
			<div class="inline-flex w-fit items-center gap-2 rounded-full border border-orange-500/30 bg-orange-500/10 px-3 py-1 text-xs font-bold text-orange-400">
				Platform Super Admin
			</div>
			<h1 class="text-4xl font-bold tracking-tight sm:text-5xl">
				Super Admin <span class="text-orange-400">Panel</span>
			</h1>
			<p class="max-w-2xl text-lg text-zinc-400">
				Manage all registered accounts (Admins, Employees, and Super Admins) across the platform.
			</p>
		</div>
	</div>

	{#if error}
		<div class="rounded-xl border border-red-900/50 bg-red-950/20 p-6 text-red-400">
			{error}
		</div>
	{:else if loading}
		<div class="py-10 text-center text-zinc-500">Loading platform accounts...</div>
	{:else}
		<div class="overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900/50">
			<table class="w-full text-left text-sm text-zinc-400">
				<thead class="border-b border-zinc-800 bg-zinc-900/80 text-xs uppercase text-zinc-500">
					<tr>
						<th class="px-6 py-4 font-medium">ID</th>
						<th class="px-6 py-4 font-medium">Account</th>
						<th class="px-6 py-4 font-medium">Role</th>
						<th class="px-6 py-4 font-medium">Created</th>
						<th class="px-6 py-4 font-medium text-center">Recipes</th>
						<th class="px-6 py-4 font-medium text-center">Ingredients</th>
						<th class="px-6 py-4 font-medium text-center">Other Costs</th>
						<th class="px-6 py-4 font-medium text-right">Actions</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-zinc-800/50">
					{#each users as u}
						<tr class="transition-colors hover:bg-zinc-800/30">
							<td class="px-6 py-4 font-mono text-xs text-zinc-500">{u.id}</td>
							<td class="px-6 py-4 text-zinc-300">
								<div class="font-medium text-white">
									{u.email}
								</div>
								{#if u.username && !u.email.includes(u.username)}
									<div class="text-xs text-zinc-500">@{u.username}</div>
								{/if}
							</td>
							<td class="px-6 py-4">
								{#if u.role === 'super_admin' || u.is_admin}
									<span class="rounded-full bg-orange-500/20 px-2.5 py-0.5 text-[11px] font-bold text-orange-400 uppercase tracking-wider">
										Super Admin
									</span>
								{:else if u.role === 'employee'}
									<span class="rounded-full bg-sky-500/20 px-2.5 py-0.5 text-[11px] font-bold text-sky-400 uppercase tracking-wider">
										Employee
									</span>
								{:else}
									<span class="rounded-full bg-emerald-500/20 px-2.5 py-0.5 text-[11px] font-bold text-emerald-400 uppercase tracking-wider">
										Admin
									</span>
								{/if}
							</td>
							<td class="px-6 py-4 text-zinc-500 whitespace-nowrap">
								{new Date(u.created_at).toLocaleDateString()}
							</td>
							<td class="px-6 py-4 text-center font-mono text-zinc-400">{u.recipe_count}</td>
							<td class="px-6 py-4 text-center font-mono text-zinc-400">{u.ingredient_count}</td>
							<td class="px-6 py-4 text-center font-mono text-zinc-400">{u.other_cost_count}</td>
							<td class="px-6 py-4 text-right">
								{#if u.role !== 'super_admin' && !u.is_admin}
									<button 
										class="rounded-lg p-2 text-red-400 hover:bg-red-500/10 hover:text-red-300 transition-colors"
										aria-label="Delete User"
										onclick={() => askDelete(u)}
									>
										<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-trash-2"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" x2="10" y1="11" y2="17"/><line x1="14" x2="14" y1="11" y2="17"/></svg>
									</button>
								{/if}
							</td>
						</tr>
					{/each}
					{#if users.length === 0}
						<tr>
							<td colspan="8" class="px-6 py-8 text-center text-zinc-500">
								No users found.
							</td>
						</tr>
					{/if}
				</tbody>
			</table>
		</div>
	{/if}
</section>

<TypeToConfirmDeleteModal
	open={deleteModalOpen}
	title="Delete Account"
	description={`Are you sure you want to delete ${userToDelete?.email ?? 'this user'}? All associated data and any employee accounts will be permanently removed.`}
	confirmText={deleting ? 'Deleting...' : 'Delete Account'}
	requireTyped={false}
	onClose={() => (deleteModalOpen = false)}
	onConfirm={confirmDelete}
/>
