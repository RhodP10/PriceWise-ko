<script lang="ts">
	import { authState } from '$lib/state/auth.svelte';
	import { type EmployeeDTO, fetchEmployees, createEmployee, deleteEmployee } from '$lib/api/adminClient';
	import TypeToConfirmDeleteModal from '$lib/components/TypeToConfirmDeleteModal.svelte';

	let employees = $state<EmployeeDTO[]>([]);
	let loading = $state(true);
	let error = $state('');

	// Create Employee Modal State
	let addModalOpen = $state(false);
	let newUsername = $state('');
	let newPassword = $state('');
	let showPassword = $state(false);
	let creating = $state(false);
	let createError = $state('');

	// Delete Modal State
	let deleteModalOpen = $state(false);
	let employeeToDelete = $state<EmployeeDTO | null>(null);
	let deleting = $state(false);

	let hasLoaded = $state(false);

	async function loadEmployees(): Promise<void> {
		try {
			loading = true;
			error = '';
			const token = authState.token;
			if (!token) return;
			employees = await fetchEmployees(token);
			hasLoaded = true;
		} catch (e: any) {
			error = e.message;
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		if (authState.token && !hasLoaded) {
			void loadEmployees();
		}
	});

	function openAddModal(): void {
		newUsername = '';
		newPassword = '';
		showPassword = false;
		createError = '';
		addModalOpen = true;
	}

	function closeAddModal(): void {
		addModalOpen = false;
		createError = '';
	}

	async function handleCreateEmployee(e: Event): Promise<void> {
		e.preventDefault();
		createError = '';

		const cleanUsername = newUsername.trim().toLowerCase();
		if (!cleanUsername) {
			createError = 'Username is required.';
			return;
		}
		if (cleanUsername.length < 3) {
			createError = 'Username must be at least 3 characters.';
			return;
		}
		if (!/^[a-zA-Z0-9_\.\-]+$/.test(cleanUsername)) {
			createError = 'Username can only contain letters, numbers, dashes, dots, and underscores.';
			return;
		}
		if (!newPassword || newPassword.length < 6) {
			createError = 'Password must be at least 6 characters.';
			return;
		}

		const token = authState.token;
		if (!token) {
			createError = 'You must be logged in.';
			return;
		}

		try {
			creating = true;
			await createEmployee(token, {
				username: cleanUsername,
				password: newPassword
			});
			closeAddModal();
			await loadEmployees();
		} catch (err: any) {
			createError = err.message || 'Failed to create employee account.';
		} finally {
			creating = false;
		}
	}

	function askDelete(emp: EmployeeDTO): void {
		employeeToDelete = emp;
		deleteModalOpen = true;
	}

	async function confirmDelete(): Promise<void> {
		if (!employeeToDelete) return;
		const token = authState.token;
		if (!token) {
			alert('Not authenticated. Please log in again.');
			return;
		}
		try {
			deleting = true;
			await deleteEmployee(token, employeeToDelete.id);
			deleteModalOpen = false;
			employeeToDelete = null;
			await loadEmployees();
		} catch (e: any) {
			alert('Failed to delete employee: ' + e.message);
		} finally {
			deleting = false;
		}
	}
</script>

<svelte:head>
	<title>Admin Panel - Employee Management</title>
</svelte:head>

<section class="animate-in relative space-y-8 pb-12">
	<!-- Hero Banner -->
	<div class="relative overflow-hidden rounded-3xl bg-zinc-900 p-8 text-white shadow-2xl lg:p-12">
		<div class="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-emerald-500/20 blur-3xl"></div>
		<div class="absolute -bottom-20 -left-20 h-64 w-64 rounded-full bg-teal-500/10 blur-3xl"></div>

		<div class="relative z-10 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
			<div>
				<div class="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-400">
					<span class="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
					Store Admin Panel
				</div>
				<h1 class="mt-2 text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">
					Staff & <span class="text-emerald-400">Employee Management</span>
				</h1>
				<p class="mt-2 max-w-2xl text-base text-zinc-400 sm:text-lg">
					Create employee accounts using only a username and password. All employees automatically share and collaborate on your store's recipes, ingredients, and cost settings.
				</p>
			</div>

			<div class="shrink-0 pt-2 sm:pt-0">
				<button
					type="button"
					onclick={openAddModal}
					class="inline-flex items-center gap-2 rounded-2xl bg-emerald-600 px-5 py-3 text-sm font-bold text-white shadow-lg shadow-emerald-900/30 transition hover:bg-emerald-500 hover:shadow-emerald-900/50 active:scale-95"
				>
					<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
						<path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
					</svg>
					Add Employee
				</button>
			</div>
		</div>
	</div>

	<!-- Stats & Info Cards -->
	<div class="grid gap-4 sm:grid-cols-3">
		<div class="rounded-2xl border border-zinc-200/80 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/60">
			<div class="text-xs font-semibold uppercase tracking-wider text-zinc-500">Total Employees</div>
			<div class="mt-2 text-3xl font-extrabold text-zinc-900 dark:text-white">
				{employees.length}
			</div>
			<p class="mt-1 text-xs text-zinc-500">Accounts created under your store</p>
		</div>

		<div class="rounded-2xl border border-zinc-200/80 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/60">
			<div class="text-xs font-semibold uppercase tracking-wider text-zinc-500">Workspace Data</div>
			<div class="mt-2 flex items-center gap-2 text-xl font-bold text-emerald-600 dark:text-emerald-400">
				<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d="M7.5 21 3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" />
				</svg>
				Shared & Synced
			</div>
			<p class="mt-1 text-xs text-zinc-500">Staff view and edit your exact recipes & costs</p>
		</div>

		<div class="rounded-2xl border border-zinc-200/80 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/60">
			<div class="text-xs font-semibold uppercase tracking-wider text-zinc-500">Employee Login</div>
			<div class="mt-2 text-lg font-bold text-zinc-800 dark:text-zinc-200">
				Username & Password
			</div>
			<p class="mt-1 text-xs text-zinc-500">No email required for employee logins</p>
		</div>
	</div>

	<!-- Error state -->
	{#if error}
		<div class="rounded-2xl border border-red-200 bg-red-50 p-6 text-red-700 dark:border-red-900/50 dark:bg-red-950/20 dark:text-red-400">
			{error}
		</div>
	{:else if loading}
		<div class="flex flex-col items-center justify-center py-16 text-zinc-500">
			<div class="h-10 w-10 animate-spin rounded-full border-4 border-emerald-600 border-t-transparent"></div>
			<p class="mt-4 text-sm font-medium">Loading employee accounts...</p>
		</div>
	{:else}
		<!-- Employee List Table -->
		<div class="overflow-hidden rounded-2xl border border-zinc-200 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-900/60">
			<div class="border-b border-zinc-200 bg-zinc-50/50 px-6 py-4 dark:border-zinc-800 dark:bg-zinc-800/30 flex items-center justify-between">
				<h2 class="text-base font-bold text-zinc-900 dark:text-zinc-100">
					Active Staff Accounts ({employees.length})
				</h2>
			</div>

			<table class="w-full text-left text-sm text-zinc-600 dark:text-zinc-400">
				<thead class="border-b border-zinc-200 bg-zinc-50/80 text-xs uppercase text-zinc-500 dark:border-zinc-800 dark:bg-zinc-900/80">
					<tr>
						<th class="px-6 py-4 font-medium">Employee</th>
						<th class="px-6 py-4 font-medium">Role</th>
						<th class="px-6 py-4 font-medium">Date Created</th>
						<th class="px-6 py-4 font-medium text-right">Actions</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-zinc-200/70 dark:divide-zinc-800/50">
					{#each employees as emp}
						<tr class="transition-colors hover:bg-zinc-50/80 dark:hover:bg-zinc-800/30">
							<td class="px-6 py-4">
								<div class="flex items-center gap-3">
									<div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-emerald-100 font-bold text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-400">
										{emp.username.slice(0, 2).toUpperCase()}
									</div>
									<div>
										<div class="font-semibold text-zinc-900 dark:text-zinc-100">
											@{emp.username}
										</div>
										<div class="text-xs text-zinc-500">ID: #{emp.id}</div>
									</div>
								</div>
							</td>
							<td class="px-6 py-4">
								<span class="inline-flex items-center rounded-full bg-sky-100 px-2.5 py-0.5 text-xs font-semibold text-sky-800 dark:bg-sky-950/50 dark:text-sky-300">
									Employee
								</span>
							</td>
							<td class="px-6 py-4 whitespace-nowrap text-zinc-500 dark:text-zinc-400">
								{new Date(emp.created_at).toLocaleDateString(undefined, {
									year: 'numeric',
									month: 'short',
									day: 'numeric'
								})}
							</td>
							<td class="px-6 py-4 text-right">
								<button
									type="button"
									class="inline-flex items-center gap-1.5 rounded-xl border border-red-200 px-3 py-1.5 text-xs font-semibold text-red-600 transition hover:bg-red-50 hover:text-red-700 active:scale-95 dark:border-red-900/40 dark:text-red-400 dark:hover:bg-red-950/30"
									aria-label={`Delete ${emp.username}`}
									onclick={() => askDelete(emp)}
								>
									<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
										<path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" x2="10" y1="11" y2="17"/><line x1="14" x2="14" y1="11" y2="17"/>
									</svg>
									Delete
								</button>
							</td>
						</tr>
					{/each}

					{#if employees.length === 0}
						<tr>
							<td colspan="4" class="px-6 py-14 text-center">
								<div class="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-zinc-100 text-zinc-400 dark:bg-zinc-800">
									<svg xmlns="http://www.w3.org/2000/svg" class="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.75">
										<path stroke-linecap="round" stroke-linejoin="round" d="M18 18.72a9.094 9.094 0 0 0 3.741-.479 3 3 0 0 0-4.682-2.72m.94 3.198.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0 1 12 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 0 1 6 18.719m12 0a5.971 5.971 0 0 0-.941-3.197m0 0A5.995 5.995 0 0 0 12 12.75a5.995 5.995 0 0 0-5.058 2.772m0 0a3 3 0 0 0-4.681 2.72 8.986 8.986 0 0 0 3.74.477m.94-3.197a5.971 5.971 0 0 0-.94 3.197M15 6.75a3 3 0 1 1-6 0 3 3 0 0 1 6 0Zm6 3a2.25 2.25 0 1 1-4.5 0 2.25 2.25 0 0 1 4.5 0Zm-13.5 0a2.25 2.25 0 1 1-4.5 0 2.25 2.25 0 0 1 4.5 0Z" />
									</svg>
								</div>
								<h3 class="mt-4 text-base font-bold text-zinc-900 dark:text-zinc-100">No employees added yet</h3>
								<p class="mt-1 text-sm text-zinc-500 max-w-sm mx-auto">
									Add your staff or barista accounts using username and password so they can log in and view your recipes.
								</p>
								<button
									type="button"
									onclick={openAddModal}
									class="mt-5 inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow transition hover:bg-emerald-500 active:scale-95"
								>
									<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
										<path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
									</svg>
									Add First Employee
								</button>
							</td>
						</tr>
					{/if}
				</tbody>
			</table>
		</div>
	{/if}
</section>

<!-- Add Employee Modal -->
{#if addModalOpen}
	<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
	<div
		class="fixed inset-0 z-[80] flex items-center justify-center bg-zinc-950/50 p-4 backdrop-blur-sm"
		role="dialog"
		aria-modal="true"
		aria-labelledby="add-emp-title"
	>
		<form
			class="w-full max-w-md rounded-3xl border border-zinc-200 bg-white p-6 shadow-2xl transition-all dark:border-zinc-800 dark:bg-zinc-900"
			onsubmit={handleCreateEmployee}
		>
			<div class="flex items-center justify-between">
				<div class="flex items-center gap-3">
					<div class="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-600 ring-1 ring-emerald-100 dark:bg-emerald-950/50 dark:text-emerald-400 dark:ring-emerald-900/50">
						<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M18 7.5v3m0 0v3m0-3h3m-3 0h-3m-2.25-4.125a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0ZM3 19.235v-.11a6.375 6.375 0 0 1 12.75 0v.109A12.318 12.318 0 0 1 9.374 21c-2.331 0-4.512-.645-6.374-1.766Z" />
						</svg>
					</div>
					<div>
						<h2 id="add-emp-title" class="text-lg font-bold text-zinc-900 dark:text-white">Create Employee Account</h2>
						<p class="text-xs text-zinc-500">Username and password only (no email needed)</p>
					</div>
				</div>

				<button
					type="button"
					aria-label="Close modal"
					class="rounded-xl p-1.5 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600 dark:hover:bg-zinc-800 dark:hover:text-zinc-200"
					onclick={closeAddModal}
				>
					<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
					</svg>
				</button>
			</div>

			{#if createError}
				<div class="mt-4 rounded-xl bg-red-50 p-3 text-xs font-semibold text-red-600 dark:bg-red-950/30 dark:text-red-400">
					{createError}
				</div>
			{/if}

			<div class="mt-5 space-y-4">
				<div>
					<label for="emp-username" class="block text-xs font-bold uppercase tracking-wider text-zinc-600 dark:text-zinc-300">
						Username
					</label>
					<div class="relative mt-1">
						<span class="absolute inset-y-0 left-0 flex items-center pl-3.5 text-sm font-semibold text-zinc-400">@</span>
						<input
							id="emp-username"
							type="text"
							bind:value={newUsername}
							required
							placeholder="barista_sam"
							class="w-full rounded-xl border border-zinc-200 bg-zinc-50 py-2.5 pl-8 pr-3 text-sm text-zinc-900 outline-none transition focus:border-emerald-500 focus:bg-white focus:ring-4 focus:ring-emerald-500/10 dark:border-zinc-700 dark:bg-zinc-800 dark:text-white"
						/>
					</div>
					<p class="mt-1 text-[11px] text-zinc-400">Use letters, numbers, or underscores (min 3 chars).</p>
				</div>

				<div>
					<label for="emp-password" class="block text-xs font-bold uppercase tracking-wider text-zinc-600 dark:text-zinc-300">
						Password
					</label>
					<div class="relative mt-1">
						<input
							id="emp-password"
							type={showPassword ? 'text' : 'password'}
							bind:value={newPassword}
							required
							placeholder="••••••••"
							class="w-full rounded-xl border border-zinc-200 bg-zinc-50 py-2.5 pl-3.5 pr-10 text-sm text-zinc-900 outline-none transition focus:border-emerald-500 focus:bg-white focus:ring-4 focus:ring-emerald-500/10 dark:border-zinc-700 dark:bg-zinc-800 dark:text-white"
						/>
						<button
							type="button"
							class="absolute inset-y-0 right-0 flex items-center pr-3 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200"
							onclick={() => (showPassword = !showPassword)}
						>
							{#if showPassword}
								<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l18 18" />
								</svg>
							{:else}
								<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
								</svg>
							{/if}
						</button>
					</div>
					<p class="mt-1 text-[11px] text-zinc-400">At least 6 characters.</p>
				</div>
			</div>

			<div class="mt-6 flex justify-end gap-2">
				<button
					type="button"
					class="rounded-xl px-4 py-2.5 text-sm font-semibold text-zinc-600 transition hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800"
					onclick={closeAddModal}
				>
					Cancel
				</button>
				<button
					type="submit"
					disabled={creating}
					class="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-5 py-2.5 text-sm font-bold text-white shadow-sm transition hover:bg-emerald-500 active:scale-95 disabled:opacity-50"
				>
					{#if creating}
						<div class="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
						<span>Creating...</span>
					{:else}
						<span>Create Account</span>
					{/if}
				</button>
			</div>
		</form>
	</div>
{/if}

<!-- Confirm Delete Modal -->
<TypeToConfirmDeleteModal
	open={deleteModalOpen}
	title={`Delete Employee Account`}
	description={`Are you sure you want to delete @${employeeToDelete?.username ?? ''}? They will no longer be able to log in to this store.`}
	confirmText={deleting ? 'Deleting...' : 'Delete Employee'}
	requireTyped={false}
	onClose={() => (deleteModalOpen = false)}
	onConfirm={confirmDelete}
/>
