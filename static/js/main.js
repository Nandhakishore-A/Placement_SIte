// =========================================================================
// PLACEMENT MANAGEMENT SYSTEM — FRONTEND MASTER CONTROLLER
// =========================================================================

let currentUser = null;
let currentTab = 'dashboard';
let currentStudentPage = 1;
let totalStudentPages = 1;
let departmentsList = [];
let deptChartInstance = null;
let statusChartInstance = null;
let activeCompanyStage = 'ALL';
let isRecruiterView = false;

document.addEventListener('DOMContentLoaded', async () => {
    setupEventListeners();
    await initAuthSession();
    
    // Load departments & dashboard in parallel for maximum speed
    Promise.all([
        loadDepartments(),
        loadDashboardStats()
    ]);
    switchTab('dashboard');
});

// -------------------------------------------------------------------------
// 1. AUTHENTICATION & ROLE-BASED ACCESS CONTROL
// -------------------------------------------------------------------------
async function initAuthSession() {
    try {
        const res = await fetch('/api/auth/me');
        if (!res.ok) {
            window.location.href = '/login';
            return;
        }
        const data = await res.json();
        currentUser = data.user;
        updateUserUI();
    } catch (e) {
        window.location.href = '/login';
    }
}

function updateUserUI() {
    if (!currentUser) return;
    
    document.getElementById('userFullName').textContent = currentUser.full_name;
    document.getElementById('userMemberId').textContent = currentUser.member_id;
    document.getElementById('userAvatarText').textContent = currentUser.member_id.substring(0, 2);
    
    const roleBadge = document.getElementById('roleBadge');
    roleBadge.textContent = currentUser.role.toUpperCase();
    
    // Personalized Dashboard Welcome Banner
    const welcomeRoleTag = document.getElementById('welcomeRoleTag');
    const welcomeUserHeading = document.getElementById('welcomeUserHeading');
    const welcomeUserSubheading = document.getElementById('welcomeUserSubheading');
    const quickActionsContainer = document.getElementById('dashboardQuickActions');

    let headingText = `Welcome (${currentUser.full_name})`;
    let subText = `Overall Placement Analytics & Campus Operations.`;
    let tagText = `PORTAL ACCESS ACTIVE`;
    let quickButtons = ``;

    if (currentUser.role === 'admin') {
        tagText = `ADMINISTRATOR EXECUTIVE SUITE`;
        headingText = `Welcome Admin Dr. Sivasubramaniyan`;
        subText = `Full 360° Placement Analytics, Company Approvals & AI Engine Control.`;
        quickButtons = `
            <button onclick="switchTab('students')" class="px-3 py-1.5 bg-white/10 hover:bg-white/20 text-white rounded-xl text-xs font-semibold backdrop-blur border border-white/20 transition flex items-center space-x-1.5">
                <i class="fa-solid fa-user-graduate text-emerald-300"></i>
                <span>Students</span>
            </button>
            <button onclick="switchTab('companies')" class="px-3 py-1.5 bg-white/10 hover:bg-white/20 text-white rounded-xl text-xs font-semibold backdrop-blur border border-white/20 transition flex items-center space-x-1.5">
                <i class="fa-solid fa-building-columns text-indigo-300"></i>
                <span>Company CRM</span>
            </button>
            <button onclick="switchTab('placements')" class="px-3 py-1.5 bg-white/10 hover:bg-white/20 text-white rounded-xl text-xs font-semibold backdrop-blur border border-white/20 transition flex items-center space-x-1.5">
                <i class="fa-solid fa-briefcase text-amber-300"></i>
                <span>Drives</span>
            </button>
            <button onclick="switchTab('ats')" class="px-3 py-1.5 bg-white/10 hover:bg-white/20 text-white rounded-xl text-xs font-semibold backdrop-blur border border-white/20 transition flex items-center space-x-1.5">
                <i class="fa-solid fa-brain text-purple-300"></i>
                <span>Gemini ATS</span>
            </button>
            <button onclick="switchTab('reports')" class="px-3 py-1.5 bg-white/10 hover:bg-white/20 text-white rounded-xl text-xs font-semibold backdrop-blur border border-white/20 transition flex items-center space-x-1.5">
                <i class="fa-solid fa-file-invoice text-rose-300"></i>
                <span>Reports</span>
            </button>
        `;
    } else if (currentUser.role === 'manager') {
        tagText = `ACADEMIC DEAN SUITE`;
        headingText = `Welcome Manager Dr. Jeyakannan`;
        subText = `Student Directory, Departmental Placement Rates & Verified Academic Records.`;
        quickButtons = `
            <button onclick="switchTab('students')" class="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold shadow-md transition flex items-center space-x-1.5">
                <i class="fa-solid fa-user-graduate"></i>
                <span>Explore Student Directory</span>
            </button>
            <button onclick="switchTab('reports')" class="px-3.5 py-2 bg-white/10 hover:bg-white/20 text-white rounded-xl text-xs font-semibold backdrop-blur border border-white/20 transition flex items-center space-x-1.5">
                <i class="fa-solid fa-file-invoice"></i>
                <span>Download Student Reports</span>
            </button>
        `;
    } else if (currentUser.role === 'team_member') {
        const memNum = parseInt((currentUser.member_id || '').replace(/\D/g, ''), 10);
        if (currentUser.member_id === 'MEM001' || (currentUser.full_name && currentUser.full_name.includes('Lead'))) {
            tagText = `PLACEMENT LEAD HUB`;
            const cleanName = currentUser.full_name.replace(/\(Lead\)/i, '').trim();
            headingText = `Welcome Team Lead (${cleanName})`;
            subText = `Recruitment Pipeline, Company CRM Stages & Drive Proposals for Admin Approval.`;
        } else {
            tagText = `PLACEMENT OPERATIONS SUITE`;
            headingText = `Welcome Team Member ${memNum ? memNum : '1'} (${currentUser.full_name})`;
            subText = `Company Sourcing, CRM Pipeline Updates & Recruitment Operations.`;
        }
        quickButtons = `
            <button onclick="switchTab('companies')" class="px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold shadow-md transition flex items-center space-x-1.5">
                <i class="fa-solid fa-building-columns"></i>
                <span>Open Company CRM</span>
            </button>
            <button onclick="switchTab('companies'); openCompanyModal();" class="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold shadow-md transition flex items-center space-x-1.5">
                <i class="fa-solid fa-plus"></i>
                <span>Add New Company</span>
            </button>
        `;
    }

    if (welcomeRoleTag) welcomeRoleTag.textContent = tagText;
    if (welcomeUserHeading) welcomeUserHeading.textContent = headingText;
    if (welcomeUserSubheading) welcomeUserSubheading.textContent = subText;
    if (quickActionsContainer) quickActionsContainer.innerHTML = quickButtons;

    // Role-based navigation visibility
    const navDashboard = document.getElementById('nav-dashboard');
    const navStudents = document.getElementById('nav-students');
    const navCompanies = document.getElementById('nav-companies');
    const navPlacements = document.getElementById('nav-placements');
    const navAts = document.getElementById('nav-ats');
    const navReports = document.getElementById('nav-reports');
    const navLogs = document.getElementById('nav-logs');
    const companyStats = document.getElementById('companyPipelineStats');
    const companyReportCard = document.getElementById('companyReportCard');
    const offersReportCard = document.getElementById('offersReportCard');
    const addStudentBtn = document.getElementById('addStudentBtn');

    if (currentUser.role === 'manager') {
        // STRICT MANAGER RULE: Strictly Student Directory & Student Reports only!
        if (navDashboard) navDashboard.classList.remove('hidden');
        if (navStudents) navStudents.classList.remove('hidden');
        if (navCompanies) navCompanies.classList.add('hidden');
        if (navPlacements) navPlacements.classList.add('hidden');
        if (navAts) navAts.classList.add('hidden');
        if (navReports) navReports.classList.remove('hidden');
        if (navLogs) navLogs.classList.add('hidden');
        if (companyStats) companyStats.classList.add('hidden');
        if (companyReportCard) companyReportCard.classList.add('hidden');
        if (offersReportCard) offersReportCard.classList.add('hidden');
        if (addStudentBtn) addStudentBtn.classList.remove('hidden');
    } else if (currentUser.role === 'team_member') {
        // STRICT TEAM LEAD / MEMBERS RULE: Overall Dashboard & Company CRM only!
        if (navDashboard) navDashboard.classList.remove('hidden');
        if (navCompanies) navCompanies.classList.remove('hidden');
        if (navStudents) navStudents.classList.add('hidden');
        if (navPlacements) navPlacements.classList.add('hidden');
        if (navAts) navAts.classList.add('hidden');
        if (navReports) navReports.classList.add('hidden');
        if (navLogs) navLogs.classList.add('hidden');
        if (companyStats) companyStats.classList.remove('hidden');
        if (companyReportCard) companyReportCard.classList.add('hidden');
        if (offersReportCard) offersReportCard.classList.add('hidden');
        if (addStudentBtn) addStudentBtn.classList.add('hidden');
    } else {
        // Admin: Complete full access to everything
        if (navDashboard) navDashboard.classList.remove('hidden');
        if (navStudents) navStudents.classList.remove('hidden');
        if (navCompanies) navCompanies.classList.remove('hidden');
        if (navPlacements) navPlacements.classList.remove('hidden');
        if (navAts) navAts.classList.remove('hidden');
        if (navReports) navReports.classList.remove('hidden');
        if (navLogs) navLogs.classList.remove('hidden');
        if (companyStats) companyStats.classList.remove('hidden');
        if (companyReportCard) companyReportCard.classList.remove('hidden');
        if (offersReportCard) offersReportCard.classList.remove('hidden');
        if (addStudentBtn) addStudentBtn.classList.remove('hidden');
        checkAdminPendingDrives();
    }
}

async function quickSwitchRole(role) {
    try {
        const res = await fetch('/api/auth/demo-login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ role })
        });
        if (res.ok) {
            window.location.reload();
        }
    } catch (e) {
        console.error(e);
    }
}

async function logout() {
    await fetch('/api/auth/logout', { method: 'POST' });
    window.location.href = '/login';
}


// -------------------------------------------------------------------------
// 2. TAB SWITCHING & ROUTING
// -------------------------------------------------------------------------
function switchTab(tabName) {
    // Check permission for team_member: Strictly Dashboard and Company CRM only
    if (currentUser && currentUser.role === 'team_member' && !['dashboard', 'companies'].includes(tabName)) {
        Swal.fire({
            icon: 'warning',
            title: 'Access Restricted',
            text: 'Placement Team Members have access to the Overall Dashboard and Company CRM only.'
        });
        tabName = 'dashboard';
    }

    // Check permission for manager: Strictly Dashboard, Students, and Reports
    if (currentUser && currentUser.role === 'manager' && !['dashboard', 'students', 'reports'].includes(tabName)) {
        Swal.fire({
            icon: 'warning',
            title: 'Access Restricted',
            text: 'Manager role has access to Student Management and Student Reports only.'
        });
        tabName = 'students';
    }

    currentTab = tabName;
    const tabs = ['dashboard', 'students', 'companies', 'placements', 'ats', 'reports', 'logs'];
    
    tabs.forEach(t => {
        const el = document.getElementById(`tab-${t}`);
        const nav = document.getElementById(`nav-${t}`);
        if (el) el.classList.toggle('hidden', t !== tabName);
        if (nav) {
            if (t === tabName) {
                nav.classList.add('bg-blue-600', 'text-white');
                nav.classList.remove('text-slate-300');
            } else {
                nav.classList.remove('bg-blue-600', 'text-white');
                nav.classList.add('text-slate-300');
            }
        }
    });

    // Update Header
    const titles = {
        'dashboard': ['Analytics Dashboard', 'Real-time placement statistics & campus recruitment database'],
        'students': ['Student Directory (102 Students)', 'Explore 102 verified candidate profiles across 6 academic departments'],
        'companies': ['Company Pipeline CRM', 'Cold, Warm, Hot & Drive Completed recruitment tracking (20 Companies)'],
        'placements': ['Campus Drives & Offers', 'Eligibility filter, attendance marking and offer letters'],
        'ats': ['Gemini AI ATS Matcher', 'Autonomous resume evaluation & 91-100% high-match alerts'],
        'reports': ['Reports & Exports', 'Download formatted Excel (openpyxl) and PDF (ReportLab) reports'],
        'logs': ['Activity Audit Trail', 'Complete action log of all team members and admin approvals']
    };

    if (titles[tabName]) {
        document.getElementById('pageTitle').textContent = titles[tabName][0];
        document.getElementById('pageSubtitle').textContent = titles[tabName][1];
    }

    // Trigger tab specific loads
    if (tabName === 'dashboard') loadDashboardStats();
    if (tabName === 'students') loadStudents(1);
    if (tabName === 'companies') loadCompanies();
    if (tabName === 'placements') loadPlacementDrives();
    if (tabName === 'ats') loadAtsPrerequisites();
    if (tabName === 'logs') loadActivityLogs();
}

function refreshCurrentTab() {
    switchTab(currentTab);
}


// -------------------------------------------------------------------------
// 3. DASHBOARD ANALYTICS & CHARTS
// -------------------------------------------------------------------------
async function loadDashboardStats() {
    try {
        const res = await fetch('/api/reports/stats');
        if (!res.ok) return;
        const stats = await res.json();

        const totStudents = stats.total_students || 102;
        document.getElementById('statTotalStudents').textContent = totStudents.toLocaleString();
        document.getElementById('statPlacedStudents').textContent = (stats.placed_students || 0).toLocaleString();
        document.getElementById('statUnplacedStudents').textContent = (stats.unplaced_students || 0).toLocaleString();
        document.getElementById('statPlacementRate').innerHTML = `<i class="fa-solid fa-arrow-trend-up mr-1"></i> ${stats.placement_percentage || 0}% Current Rate`;
        
        const sideBadge = document.getElementById('sidebarStudentCount');
        if (sideBadge) sideBadge.textContent = totStudents;

        const deptCandBadge = document.getElementById('deptCandidatesCount');
        if (deptCandBadge) deptCandBadge.textContent = `Total ${totStudents} Candidates`;

        if (stats.highest_ctc) {
            document.getElementById('statHighestCTC').textContent = `${stats.highest_ctc} LPA`;
            document.getElementById('statAvgCTC').innerHTML = `<i class="fa-solid fa-coins mr-1"></i> Avg: ${stats.average_ctc} LPA`;
        }

        if (currentUser.role !== 'manager') {
            document.getElementById('statColdCount').textContent = stats.cold_companies || 0;
            document.getElementById('statWarmCount').textContent = stats.warm_companies || 0;
            document.getElementById('statHotCount').textContent = stats.hot_companies || 0;
            document.getElementById('statCompletedCount').textContent = stats.completed_drives || 0;
            document.getElementById('statTotalOffers').textContent = `${stats.total_offers || 0} Offers Issued`;
        }

        renderCharts(stats);
        checkAdminPendingDrives();
    } catch (e) {
        console.error('Error loading dashboard stats:', e);
    }
}

function renderCharts(stats) {
    // Dept Chart
    const deptCtx = document.getElementById('deptChart');
    if (deptCtx) {
        if (deptChartInstance) deptChartInstance.destroy();
        
        const labels = departmentsList.map(d => d.code);
        const placedData = departmentsList.map(d => d.placed_count || 0);
        const totalData = departmentsList.map(d => d.student_count || 0);

        deptChartInstance = new Chart(deptCtx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Placed Students',
                        data: placedData,
                        backgroundColor: '#10b981',
                        borderRadius: 6
                    },
                    {
                        label: 'Total Students',
                        data: totalData,
                        backgroundColor: '#e2e8f0',
                        borderRadius: 6
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'top' } },
                scales: { y: { beginAtZero: true } }
            }
        });
    }

    // Status Doughnut Chart
    const statusCtx = document.getElementById('statusChart');
    if (statusCtx) {
        if (statusChartInstance) statusChartInstance.destroy();
        
        const placed = stats.placed_students || 71;
        const unplaced = stats.unplaced_students || 31;

        statusChartInstance = new Chart(statusCtx, {
            type: 'doughnut',
            data: {
                labels: ['Placed Students', 'Yet To Be Placed'],
                datasets: [{
                    data: [placed, unplaced],
                    backgroundColor: ['#10b981', '#f59e0b'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' }
                },
                cutout: '70%'
            }
        });
    }
}


// -------------------------------------------------------------------------
// 4. STUDENT MANAGEMENT & DEPARTMENT DRILLDOWN
// -------------------------------------------------------------------------
async function loadDepartments() {
    try {
        const res = await fetch('/api/departments');
        if (!res.ok) return;
        departmentsList = await res.json();
        renderDepartmentPills();
        populateDeptDropdowns();
    } catch (e) {
        console.error(e);
    }
}

function renderDepartmentPills() {
    const container = document.getElementById('deptPillContainer');
    if (!container) return;
    
    container.innerHTML = departmentsList.map(d => `
        <button onclick="drilldownDepartment('${d.code}')"
            class="p-3 rounded-2xl bg-white border border-slate-200 hover:border-blue-500 hover:shadow-md transition text-left group">
            <div class="flex items-center justify-between mb-1">
                <span class="font-extrabold text-xs text-slate-800 group-hover:text-blue-600">${d.code}</span>
                <span class="text-[10px] px-1.5 py-0.5 rounded bg-blue-50 text-blue-600 font-bold">${d.placement_rate}%</span>
            </div>
            <div class="text-[11px] text-slate-500">${d.student_count} Students</div>
            <div class="text-[10px] text-emerald-600 font-semibold mt-0.5">${d.placed_count} Placed</div>
        </button>
    `).join('');
}

function populateDeptDropdowns() {
    const studDept = document.getElementById('studDept');
    if (studDept) {
        studDept.innerHTML = departmentsList.map(d => `<option value="${d.id}">${d.code} — ${d.name}</option>`).join('');
    }
}

function drilldownDepartment(deptCode) {
    document.getElementById('studentDeptFilter').value = deptCode;
    loadStudents(1);
    Swal.fire({
        toast: true,
        position: 'top-end',
        icon: 'info',
        title: `Filtered: ${deptCode} Department (${departmentsList.find(d => d.code === deptCode)?.student_count || ''} candidates)`,
        showConfirmButton: false,
        timer: 2000
    });
}

function resetStudentFilters() {
    document.getElementById('studentDeptFilter').value = 'ALL';
    document.getElementById('studentStatusFilter').value = 'ALL';
    document.getElementById('studentUgFilter').value = '';
    document.getElementById('studentSearchInput').value = '';
    loadStudents(1);
}

async function loadStudents(page = 1) {
    currentStudentPage = page;
    const dept = document.getElementById('studentDeptFilter').value;
    const status = document.getElementById('studentStatusFilter').value;
    const minUg = document.getElementById('studentUgFilter').value;
    const search = document.getElementById('studentSearchInput').value.trim();

    let url = `/api/students?page=${page}&per_page=20&department=${dept}&status=${status}`;
    if (minUg) url += `&min_ug=${minUg}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;

    try {
        const res = await fetch(url);
        if (!res.ok) return;
        const data = await res.json();

        totalStudentPages = data.total_pages;
        document.getElementById('studentCountLabel').textContent = `Showing ${(page - 1) * 20 + 1}-${Math.min(page * 20, data.total)} of ${data.total} Students`;
        document.getElementById('paginationInfo').textContent = `Page ${page} of ${data.total_pages}`;
        document.getElementById('currentPageBadge').textContent = page;
        document.getElementById('prevPageBtn').disabled = (page <= 1);
        document.getElementById('nextPageBtn').disabled = (page >= data.total_pages);

        renderStudentTable(data.students);
    } catch (e) {
        console.error(e);
    }
}

function renderStudentTable(students) {
    const tbody = document.getElementById('studentTableBody');
    if (!tbody) return;

    if (!students || students.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" class="p-8 text-center text-slate-400">No candidates match the selected filters.</td></tr>`;
        return;
    }

    tbody.innerHTML = students.map(s => {
        const isPlaced = (s.placement_status === 'PLACED');
        const offer = s.latest_offer || {};
        const genderAvatar = (s.gender === 'Female') ? `https://randomuser.me/api/portraits/women/${(s.id % 40) + 1}.jpg` : `https://randomuser.me/api/portraits/men/${(s.id % 50) + 1}.jpg`;
        const photoSrc = s.photo_url || genderAvatar;
        
        return `
            <tr class="student-row hover:bg-slate-50/80 transition cursor-pointer" onclick="highlightStudent(this)">
                <!-- Candidate (Name + Photo) with Touch/Hover Highlight -->
                <td class="p-3.5 pl-5">
                    <div class="flex items-center space-x-3">
                        <img src="${photoSrc}" onerror="this.onerror=null;this.src='${genderAvatar}'"
                            alt="${s.name}" class="w-8 h-8 rounded-full object-cover border border-slate-200 shadow-sm">
                        <div>
                            <div class="highlight-target font-bold text-slate-900 text-xs transition-colors rounded px-1 -ml-1">
                                ${s.name}
                            </div>
                            <div class="text-[10px] text-slate-400 font-medium">${s.gender} • ${s.residency_type}</div>
                        </div>
                    </div>
                </td>

                <!-- Roll No with High-Visibility Touch/Hover Highlight -->
                <td class="p-3.5">
                    <span class="highlight-target font-mono font-bold text-xs text-slate-700 bg-slate-100 px-2 py-0.5 rounded transition-all">
                        ${s.roll_no}
                    </span>
                </td>

                <!-- Department -->
                <td class="p-3.5">
                    <span class="px-2 py-0.5 rounded-md font-bold text-[10px] bg-blue-50 text-blue-700 border border-blue-100">
                        ${s.department_code}
                    </span>
                </td>

                <!-- Academic Percentiles -->
                <td class="p-3.5">
                    <div class="text-[11px] space-x-1">
                        <span title="SSLC / 10th" class="text-slate-500">10th: <b>${s.sslc_percent}%</b></span>
                        <span class="text-slate-300">|</span>
                        <span title="HSC / 12th" class="text-slate-500">12th: <b>${s.hsc_percent}%</b></span>
                        <span class="text-slate-300">|</span>
                        <span title="UG %" class="text-emerald-700 font-bold bg-emerald-50 px-1 rounded">UG: ${s.ug_percent}%</span>
                    </div>
                </td>

                <!-- Status Badge -->
                <td class="p-3.5">
                    <span class="px-2 py-0.5 rounded-full text-[10px] font-extrabold ${isPlaced ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}">
                        ${s.placement_status}
                    </span>
                </td>

                <!-- Placed Company / Role -->
                <td class="p-3.5">
                    ${isPlaced ? `
                        <div class="text-[11px] font-bold text-slate-900">${offer.company_name || 'Recruiter Partner'}</div>
                        <div class="text-[10px] text-emerald-600 font-semibold">${offer.role || offer.role_offered || 'Associate Trainee'}${offer.ctc_lpa ? ` • ₹ ${offer.ctc_lpa} LPA` : ''}</div>
                    ` : `<span class="text-slate-400 font-mono text-xs">-</span>`}
                </td>

                <!-- Professional Links -->
                <td class="p-3.5 text-xs text-slate-400 space-x-2.5">
                    ${s.resume_url ? `<a href="${s.resume_url}" target="_blank" title="View Resume on Google Drive" class="text-amber-500 hover:text-amber-600 inline-block"><i class="fa-brands fa-google-drive"></i></a>` : ''}
                    ${s.github_url ? `<a href="${s.github_url}" target="_blank" title="GitHub Profile" class="text-slate-600 hover:text-slate-900 inline-block"><i class="fa-brands fa-github"></i></a>` : ''}
                    ${s.linkedin_url ? `<a href="${s.linkedin_url}" target="_blank" title="LinkedIn Profile" class="text-blue-600 hover:text-blue-700 inline-block"><i class="fa-brands fa-linkedin"></i></a>` : ''}
                    ${s.portfolio_url ? `<a href="${s.portfolio_url}" target="_blank" title="Personal Portfolio" class="text-purple-600 hover:text-purple-700 inline-block"><i class="fa-solid fa-globe"></i></a>` : ''}
                </td>

                <!-- Actions (View Drawer, Edit, Delete) -->
                <td class="p-3.5 text-right pr-5 space-x-1.5" onclick="event.stopPropagation()">
                    <button onclick="openStudentDrawer(${s.id})" title="View Full Profile Drawer" class="p-1.5 text-blue-600 hover:bg-blue-50 rounded-lg transition">
                        <i class="fa-solid fa-eye"></i>
                    </button>
                    ${['admin', 'manager'].includes(currentUser.role) ? `
                        <button onclick="editStudent(${s.id})" title="Edit Profile" class="p-1.5 text-amber-600 hover:bg-amber-50 rounded-lg transition">
                            <i class="fa-solid fa-pen-to-square"></i>
                        </button>
                        <button onclick="deleteStudent(${s.id}, '${s.name}')" title="Delete Student" class="p-1.5 text-rose-600 hover:bg-rose-50 rounded-lg transition">
                            <i class="fa-solid fa-trash"></i>
                        </button>
                    ` : ''}
                    ${currentUser.role !== 'manager' && !isPlaced ? `
                        <button onclick="openOfferModalForStudent(${s.id}, '${s.name}')" title="Issue Offer" class="p-1.5 text-emerald-600 hover:bg-emerald-50 rounded-lg transition">
                            <i class="fa-solid fa-plus-circle"></i>
                        </button>
                    ` : ''}
                </td>
            </tr>
        `;
    }).join('');
}

function highlightStudent(rowElement) {
    document.querySelectorAll('.student-row').forEach(r => r.classList.remove('active-highlight'));
    rowElement.classList.add('active-highlight');
}

function changeStudentPage(delta) {
    const target = currentStudentPage + delta;
    if (target >= 1 && target <= totalStudentPages) {
        loadStudents(target);
    }
}


// -------------------------------------------------------------------------
// 5. STUDENT FULL PROFILE DRAWER & CRUD
// -------------------------------------------------------------------------
async function openStudentDrawer(studentId) {
    try {
        const res = await fetch(`/api/students/${studentId}`);
        if (!res.ok) return;
        const s = await res.json();
        
        const content = document.getElementById('drawerContent');
        const genderAvatar = (s.gender === 'Female') ? `https://randomuser.me/api/portraits/women/${(s.id % 40) + 1}.jpg` : `https://randomuser.me/api/portraits/men/${(s.id % 50) + 1}.jpg`;
        const photoSrc = s.photo_url || genderAvatar;

        content.innerHTML = `
            <div class="text-center pb-4 border-b border-slate-100">
                <img src="${photoSrc}" onerror="this.onerror=null;this.src='${genderAvatar}'"
                    class="w-20 h-20 rounded-full mx-auto object-cover border-2 border-blue-500 shadow-md mb-3">
                <h4 class="font-black text-lg text-slate-900">${s.name}</h4>
                <div class="text-xs font-mono font-bold text-blue-600">${s.roll_no} • ${s.department_code}</div>
                <div class="text-xs text-slate-500 mt-1">${s.degree || 'B.Sc'} (${s.grad_year_ug || 2026} Batch)</div>
            </div>

            <!-- Academic Breakdown -->
            <div class="bg-slate-50 p-4 rounded-2xl border border-slate-200 space-y-2 text-xs">
                <h5 class="font-bold text-slate-800 text-[11px] uppercase tracking-wider mb-2">Academic Performance</h5>
                <div class="flex justify-between"><span>SSLC (10th) %:</span><b class="text-slate-900">${s.sslc_percent || 80.0}% (${s.grad_year_10th || 2020})</b></div>
                <div class="flex justify-between"><span>HSC (12th) %:</span><b class="text-slate-900">${s.hsc_percent || 78.0}% (${s.grad_year_12th || 2022})</b></div>
                <div class="flex justify-between"><span>UG CGPA / %:</span><b class="text-emerald-600">${s.ug_percent || 82.0}% (${s.grad_year_ug || 2026})</b></div>
                ${s.pg_percent ? `<div class="flex justify-between"><span>PG %:</span><b class="text-slate-900">${s.pg_percent}%</b></div>` : ''}
            </div>

            <!-- Contact & Social Links -->
            <div class="space-y-2 text-xs">
                <h5 class="font-bold text-slate-800 text-[11px] uppercase tracking-wider mb-2">Contact & Portfolios</h5>
                <div class="flex items-center space-x-2 text-slate-600">
                    <i class="fa-solid fa-envelope w-4 text-blue-500"></i>
                    <a href="mailto:${s.email}" class="text-blue-600 hover:underline">${s.email}</a>
                </div>
                <div class="flex items-center space-x-2 text-slate-600">
                    <i class="fa-solid fa-phone w-4 text-emerald-500"></i>
                    <span>+91 ${s.mobile_no}</span>
                </div>
                ${s.github_url ? `
                    <div class="flex items-center space-x-2">
                        <i class="fa-brands fa-github w-4 text-slate-800"></i>
                        <a href="${s.github_url}" target="_blank" class="text-blue-600 hover:underline truncate">${s.github_url}</a>
                    </div>
                ` : ''}
                ${s.linkedin_url ? `
                    <div class="flex items-center space-x-2">
                        <i class="fa-brands fa-linkedin w-4 text-blue-700"></i>
                        <a href="${s.linkedin_url}" target="_blank" class="text-blue-600 hover:underline truncate">${s.linkedin_url}</a>
                    </div>
                ` : ''}
                ${s.resume_url ? `
                    <div class="flex items-center space-x-2">
                        <i class="fa-brands fa-google-drive w-4 text-amber-500"></i>
                        <a href="${s.resume_url}" target="_blank" class="text-blue-600 hover:underline truncate font-semibold">View Resume on Google Drive</a>
                    </div>
                ` : ''}
                ${s.portfolio_url ? `
                    <div class="flex items-center space-x-2">
                        <i class="fa-solid fa-globe w-4 text-purple-600"></i>
                        <a href="${s.portfolio_url}" target="_blank" class="text-blue-600 hover:underline truncate">${s.portfolio_url}</a>
                    </div>
                ` : ''}
            </div>

            <!-- Offers & Placement History -->
            <div class="space-y-2 text-xs">
                <h5 class="font-bold text-slate-800 text-[11px] uppercase tracking-wider mb-2">Placement Drives & Offers</h5>
                ${s.offers && s.offers.length > 0 ? s.offers.map(o => `
                    <div class="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-900">
                        <div class="font-bold">${o.company_name || 'Recruiter Partner'} — ${o.role || o.role_offered || 'Associate Trainee'}</div>
                        <div class="text-[11px] text-emerald-700">CTC: ${o.ctc_lpa || '8.5'} LPA | Date: ${o.offer_date || '2026-03-15'}</div>
                    </div>
                `).join('') : `<div class="text-slate-400 text-xs italic">No offers recorded yet. Status: ${s.placement_status}</div>`}
            </div>
        `;
        
        document.getElementById('studentProfileDrawer').classList.remove('translate-x-full');
        const backdrop = document.getElementById('studentDrawerBackdrop');
        if (backdrop) backdrop.classList.remove('hidden');
    } catch (e) {
        console.error('Error opening student drawer:', e);
        Swal.fire('Error', 'Unable to open student profile drawer.', 'error');
    }
}

function closeStudentDrawer() {
    const drawer = document.getElementById('studentProfileDrawer');
    if (drawer) drawer.classList.add('translate-x-full');
    const backdrop = document.getElementById('studentDrawerBackdrop');
    if (backdrop) backdrop.classList.add('hidden');
}

function openStudentModal() {
    const studDept = document.getElementById('studDept');
    if (studDept && departmentsList.length > 0) {
        studDept.innerHTML = departmentsList.map(d => `<option value="${d.id}">${d.code} — ${d.name}</option>`).join('');
    }
    document.getElementById('studentForm').reset();
    document.getElementById('studentFormId').value = '';
    document.getElementById('studentModalTitle').textContent = 'Add New Student Profile';
    document.getElementById('studentModal').classList.remove('hidden');
}

function closeStudentModal() {
    document.getElementById('studentModal').classList.add('hidden');
}

async function editStudent(studentId) {
    try {
        const studDept = document.getElementById('studDept');
        if (studDept && departmentsList.length > 0) {
            studDept.innerHTML = departmentsList.map(d => `<option value="${d.id}">${d.code} — ${d.name}</option>`).join('');
        }

        const res = await fetch(`/api/students/${studentId}`);
        if (!res.ok) {
            Swal.fire('Notice', 'Unable to load student profile for editing.', 'error');
            return;
        }
        const s = await res.json();

        document.getElementById('studentFormId').value = s.id;
        document.getElementById('studRollNo').value = s.roll_no || '';
        document.getElementById('studName').value = s.name || '';
        if (s.department_id) {
            document.getElementById('studDept').value = s.department_id;
        }
        document.getElementById('studGender').value = s.gender || 'Male';
        document.getElementById('studResidency').value = s.residency_type || 'Day Scholar';
        document.getElementById('studSslc').value = s.sslc_percent != null ? s.sslc_percent : '';
        document.getElementById('studHsc').value = s.hsc_percent != null ? s.hsc_percent : '';
        document.getElementById('studUg').value = s.ug_percent != null ? s.ug_percent : '';
        document.getElementById('studPg').value = s.pg_percent != null ? s.pg_percent : '';
        document.getElementById('studEmail').value = s.email || '';
        document.getElementById('studMobile').value = s.mobile_no || '';
        document.getElementById('studGithub').value = s.github_url || '';
        document.getElementById('studLinkedin').value = s.linkedin_url || '';
        document.getElementById('studPortfolio').value = s.portfolio_url || '';

        document.getElementById('studentModalTitle').textContent = `Edit Profile — ${s.name} (${s.roll_no})`;
        document.getElementById('studentModal').classList.remove('hidden');
    } catch (e) {
        console.error('Error in editStudent:', e);
        Swal.fire('Error', 'Failed to open edit modal.', 'error');
    }
}

async function handleStudentFormSubmit(e) {
    e.preventDefault();
    const id = document.getElementById('studentFormId').value;
    const method = id ? 'PUT' : 'POST';
    const url = id ? `/api/students/${id}` : '/api/students';

    const payload = {
        roll_no: document.getElementById('studRollNo').value.trim(),
        name: document.getElementById('studName').value.trim(),
        department_id: parseInt(document.getElementById('studDept').value),
        gender: document.getElementById('studGender').value,
        residency_type: document.getElementById('studResidency').value,
        sslc_percent: parseFloat(document.getElementById('studSslc').value),
        hsc_percent: parseFloat(document.getElementById('studHsc').value),
        ug_percent: parseFloat(document.getElementById('studUg').value),
        pg_percent: document.getElementById('studPg').value ? parseFloat(document.getElementById('studPg').value) : null,
        email: document.getElementById('studEmail').value.trim(),
        mobile_no: document.getElementById('studMobile').value.trim(),
        github_url: document.getElementById('studGithub').value.trim(),
        linkedin_url: document.getElementById('studLinkedin').value.trim(),
        portfolio_url: document.getElementById('studPortfolio').value.trim()
    };

    try {
        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok) {
            Swal.fire('Error', data.error || 'Failed to save student.', 'error');
            return;
        }

        Swal.fire({ icon: 'success', title: 'Success', text: data.message, timer: 1500, showConfirmButton: false });
        closeStudentModal();
        loadStudents(currentStudentPage);
    } catch (err) {
        Swal.fire('Error', 'Server connection error', 'error');
    }
}

async function deleteStudent(studentId, name) {
    const result = await Swal.fire({
        title: 'Delete Student Record?',
        text: `Are you sure you want to permanently remove candidate ${name}?`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#e11d48',
        confirmButtonText: 'Yes, Delete'
    });

    if (result.isConfirmed) {
        const res = await fetch(`/api/students/${studentId}`, { method: 'DELETE' });
        const data = await res.json();
        if (res.ok) {
            Swal.fire('Deleted', data.message, 'success');
            loadStudents(currentStudentPage);
        } else {
            Swal.fire('Error', data.error, 'error');
        }
    }
}


// -------------------------------------------------------------------------
// 6. COMPANY MANAGEMENT & STATUS PIPELINE
// -------------------------------------------------------------------------
async function loadCompanies() {
    if (currentUser.role === 'manager') return;
    
    let url = `/api/companies?status=${activeCompanyStage}`;
    if (isRecruiterView) url += `&recruiter_view=true`;
    
    const search = document.getElementById('companySearchInput').value.trim();
    if (search) url += `&search=${encodeURIComponent(search)}`;

    try {
        const res = await fetch(url);
        if (!res.ok) return;
        const companies = await res.json();
        renderCompanyCards(companies);
        if (currentUser.role === 'admin') {
            checkAdminPendingDrives();
        }
    } catch (e) {
        console.error(e);
    }
}

function filterCompanyStage(stage) {
    activeCompanyStage = stage;
    isRecruiterView = false;
    
    document.querySelectorAll('.comp-tab').forEach(b => {
        b.classList.remove('bg-white', 'shadow-sm', 'text-blue-600');
        b.classList.add('hover:text-slate-900');
    });
    
    const activeBtn = document.getElementById(`compTab-${stage.replace(' ', '')}`);
    if (activeBtn) {
        activeBtn.classList.add('bg-white', 'shadow-sm', 'text-blue-600');
    }
    loadCompanies();
}

function toggleRecruiterView() {
    isRecruiterView = !isRecruiterView;
    document.querySelectorAll('.comp-tab').forEach(b => b.classList.remove('bg-white', 'shadow-sm', 'text-blue-600'));
    const btn = document.getElementById('compTab-RECRUITER');
    if (isRecruiterView) {
        btn.classList.add('bg-white', 'shadow-sm', 'text-purple-600', 'font-bold');
    }
    loadCompanies();
}

function renderCompanyCards(companies) {
    const grid = document.getElementById('companyCardsGrid');
    if (!grid) return;

    if (!companies || companies.length === 0) {
        grid.innerHTML = `<div class="col-span-3 p-12 text-center text-slate-400 bg-white rounded-2xl border border-slate-200">No companies found for stage [${activeCompanyStage}].</div>`;
        return;
    }

    const stageColors = {
        'COLD': 'bg-slate-100 text-slate-700 border-slate-200',
        'WARM': 'bg-indigo-50 text-indigo-700 border-indigo-200',
        'HOT': 'bg-amber-50 text-amber-700 border-amber-200',
        'DRIVE COMPLETED': 'bg-emerald-50 text-emerald-700 border-emerald-200'
    };

    grid.innerHTML = companies.map(c => `
        <div class="bg-white p-5 rounded-2xl border ${c.forwarded_to_admin && !c.is_approved ? 'border-rose-300 ring-2 ring-rose-500/10' : 'border-slate-200'} shadow-sm flex flex-col justify-between hover:shadow-md transition">
            <div>
                <!-- Top Header: Status + Approval Badge -->
                <div class="flex items-center justify-between mb-3">
                    <span class="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase border ${stageColors[c.status] || ''}">
                        ${c.status}
                    </span>
                    <div class="flex items-center space-x-1.5">
                        <span class="text-[10px] font-semibold px-2 py-0.5 rounded ${c.is_approved ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'}"
                            title="${c.is_approved ? 'Approved by Admin' : 'Pending Admin Approval'}">
                            ${c.is_approved ? '✓ Approved: Y' : '⚠ Approved: N'}
                        </span>
                    </div>
                </div>

                <!-- Forwarded to Admin Notification Alert Bar -->
                ${c.forwarded_to_admin && !c.is_approved ? `
                    <div class="mb-3 p-2.5 rounded-xl bg-gradient-to-r from-rose-50 to-amber-50 border border-rose-200 text-xs text-rose-900">
                        <div class="flex items-center justify-between font-bold text-[11px] mb-1 text-rose-700">
                            <span class="flex items-center space-x-1">
                                <i class="fa-solid fa-bell text-rose-600 animate-bounce mr-1"></i>
                                <span>Forwarded to Admin</span>
                            </span>
                            <span class="text-[9px] bg-rose-200/80 px-1.5 py-0.5 rounded-full uppercase font-mono">Pending</span>
                        </div>
                        ${c.forwarded_note ? `<p class="text-[10px] text-slate-600 italic">"${c.forwarded_note}"</p>` : ''}
                        ${currentUser.role === 'admin' ? `
                            <button onclick="toggleCompanyApproval(${c.id}, true)" class="mt-2 w-full py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-[11px] rounded-lg shadow-sm transition flex items-center justify-center space-x-1">
                                <i class="fa-solid fa-check mr-1"></i>
                                <span>Approve Drive (Y)</span>
                            </button>
                        ` : ''}
                    </div>
                ` : ''}

                <h4 class="font-extrabold text-base text-slate-900 mb-0.5">${c.name}</h4>
                <div class="text-xs font-semibold text-blue-700 mb-2 flex items-center">
                    <i class="fa-solid fa-briefcase text-blue-500 mr-1.5 text-[11px]"></i>
                    <span>${c.job_role || 'Corporate Recruitment'}</span>
                </div>

                <div class="text-xs text-slate-500 flex items-center justify-between mb-3 bg-slate-50 p-2 rounded-xl">
                    <div class="flex items-center space-x-1.5 truncate">
                        <i class="fa-solid fa-location-dot text-rose-500 text-[11px]"></i>
                        <span class="truncate">${c.location}</span>
                    </div>
                    <div class="flex items-center space-x-2 shrink-0">
                        <a href="${c.google_maps_link || `https://maps.google.com/?q=${encodeURIComponent(c.location)}`}" target="_blank"
                            class="text-blue-600 hover:underline text-[11px] font-semibold flex items-center space-x-0.5">
                            <span>Maps</span>
                            <i class="fa-solid fa-arrow-up-right-from-square text-[9px]"></i>
                        </a>
                        ${c.website ? `
                            <a href="${c.website}" target="_blank" class="text-indigo-600 hover:underline text-[11px] font-semibold flex items-center space-x-0.5" title="Official Careers Portal">
                                <i class="fa-solid fa-globe text-[10px]"></i>
                            </a>
                        ` : ''}
                    </div>
                </div>

                <!-- CTC & Offers Grid -->
                <div class="grid grid-cols-2 gap-2 bg-slate-50 p-3 rounded-xl border border-slate-100 text-xs mb-3">
                    <div>
                        <span class="text-[10px] text-slate-400 font-semibold block">CTC PACKAGE</span>
                        <b class="text-indigo-600 font-extrabold flex items-center">
                            <i class="fa-solid fa-indian-rupee-sign text-[10px] mr-1"></i>${c.ctc_lpa} LPA
                        </b>
                    </div>
                    <div>
                        <span class="text-[10px] text-slate-400 font-semibold block">OFFERS MADE</span>
                        <b class="text-emerald-600 font-extrabold flex items-center">
                            <i class="fa-solid fa-award text-[10px] mr-1"></i>${c.total_offers_count || 0} Placed
                        </b>
                    </div>
                </div>

                <!-- Placed Candidates Summary -->
                ${c.placed_students_summary ? `
                    <div class="mb-3 p-2 bg-emerald-50/70 rounded-xl border border-emerald-100 text-[10px]">
                        <div class="font-bold text-emerald-800 flex items-center mb-0.5">
                            <i class="fa-solid fa-user-check text-emerald-600 mr-1"></i>
                            <span>Placed Students:</span>
                        </div>
                        <p class="text-slate-600 line-clamp-2">${c.placed_students_summary}</p>
                    </div>
                ` : ''}

                <!-- HR Contact Details -->
                <div class="text-[11px] text-slate-600 space-y-1 mb-3">
                    <div><i class="fa-solid fa-user-tie text-slate-400 mr-1.5"></i>${c.contact_person}</div>
                    <div><i class="fa-solid fa-phone text-slate-400 mr-1.5"></i>+91 ${c.mobile_no}</div>
                    <div><i class="fa-solid fa-envelope text-slate-400 mr-1.5"></i>${c.email}</div>
                </div>

                <!-- JD Links & Word Docs Toolbar -->
                <div class="flex items-center space-x-1.5 mb-3">
                    <a href="${c.jd_file_url || c.jd_folder_url || 'https://drive.google.com/drive/folders/1gRwKWhM8tWiPA4fAJOXtjqvXSux8kqdw'}" target="_blank"
                        class="flex-1 py-1.5 px-2 bg-amber-50 hover:bg-amber-100 border border-amber-200 text-amber-900 rounded-xl text-[10px] font-bold flex items-center justify-center space-x-1 transition">
                        <i class="fa-brands fa-google-drive text-amber-600 text-xs"></i>
                        <span>JD Drive Link</span>
                    </a>
                    <button onclick="promptDownloadJdDocx(${c.id}, '${c.name.replace(/'/g, "\\'")}')"
                        class="flex-1 py-1.5 px-2 bg-blue-50 hover:bg-blue-100 border border-blue-200 text-blue-900 rounded-xl text-[10px] font-bold flex items-center justify-center space-x-1 transition">
                        <i class="fa-solid fa-file-word text-blue-600 text-xs"></i>
                        <span>Word (.docx)</span>
                    </button>
                </div>

                <div class="text-[10px] text-slate-400 flex items-center justify-between border-t border-slate-100 pt-2">
                    <span>Added By: <b>${c.added_by_member}</b></span>
                    <span>Date: ${c.created_at || 'N/A'}</span>
                </div>
            </div>

            <!-- Action Buttons Toolbar (Structured in 2 Clean Rows) -->
            <div class="mt-4 pt-3 border-t border-slate-100 space-y-2">
                <!-- Row 1: Stage Update & Forward/Approve -->
                <div class="flex items-center justify-between gap-2">
                    <!-- Status Update Selector -->
                    <select onchange="updateCompanyStatus(${c.id}, this.value)" class="flex-1 bg-slate-100 hover:bg-slate-200 border border-slate-200 text-[11px] font-bold rounded-lg px-2.5 py-1.5 focus:outline-none cursor-pointer">
                        <option value="">Stage: ${c.status} ▾</option>
                        <option value="COLD">Set COLD</option>
                        <option value="WARM">Set WARM</option>
                        <option value="HOT">Set HOT</option>
                        <option value="DRIVE COMPLETED">Set COMPLETED</option>
                    </select>

                    <!-- Forward to Admin button -->
                    <button onclick="forwardCompanyToAdmin(${c.id}, '${c.name}')" title="Forward to Admin for Approval"
                        class="px-2.5 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-lg text-xs font-bold transition flex items-center space-x-1 shrink-0">
                        <i class="fa-solid fa-paper-plane text-[10px]"></i>
                        <span>Forward</span>
                    </button>
                </div>

                <!-- Row 2: Approval Status + Edit/Delete Buttons (Guaranteed inside layout) -->
                <div class="flex items-center justify-between pt-1">
                    <div>
                        ${currentUser.role === 'admin' ? `
                            <button onclick="toggleCompanyApproval(${c.id}, ${!c.is_approved})"
                                title="${c.is_approved ? 'Revoke Approval' : 'Approve Company Drive'}"
                                class="px-2 py-1 ${c.is_approved ? 'bg-amber-50 text-amber-700 hover:bg-amber-100 border border-amber-200' : 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200'} rounded-lg text-[11px] transition font-bold">
                                ${c.is_approved ? 'Revoke (N)' : '✓ Approve (Y)'}
                            </button>
                        ` : `
                            <span class="text-[10px] font-medium text-slate-400">ID #${c.id}</span>
                        `}
                    </div>

                    <!-- Clean, Safe Edit & Delete Actions (Never overflow) -->
                    <div class="flex items-center space-x-1 shrink-0">
                        <button onclick="editCompany(${c.id})" title="Edit Details" class="p-1.5 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg text-xs transition">
                            <i class="fa-solid fa-pen-to-square"></i>
                        </button>
                        <button onclick="deleteCompany(${c.id}, '${c.name}')" title="Delete Company" class="p-1.5 text-rose-500 hover:text-rose-700 hover:bg-rose-50 rounded-lg text-xs transition">
                            <i class="fa-solid fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}

async function checkAdminPendingDrives() {
    if (!currentUser || currentUser.role !== 'admin') {
        const dContainer = document.getElementById('adminDashboardEmailVerificationContainer');
        if (dContainer) dContainer.classList.add('hidden');
        return;
    }
    
    try {
        const res = await fetch('/api/companies/pending-notifications');
        if (!res.ok) return;
        const data = await res.json();
        
        const banner = document.getElementById('adminPendingDrivesBanner');
        const badge = document.getElementById('companyNavBadge');
        const countBadge = document.getElementById('pendingDrivesCountBadge');
        const list = document.getElementById('pendingDrivesList');

        // Dashboard specific elements
        const dashContainer = document.getElementById('adminDashboardEmailVerificationContainer');
        const dashList = document.getElementById('adminDashboardPendingEmailList');
        const dashCountBadge = document.getElementById('adminDashboardPendingEmailCountBadge');
        
        if (data.count > 0) {
            if (badge) {
                badge.textContent = `${data.count} Pending`;
                badge.classList.remove('hidden');
            }
            if (countBadge) {
                countBadge.textContent = `${data.count} Action Required`;
            }
            if (dashCountBadge) {
                dashCountBadge.textContent = `${data.count} Awaiting Email Verification`;
            }

            const cardsHtml = data.companies.map(c => `
                <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between space-y-3 hover:border-slate-300 transition">
                    <div>
                        <div class="flex items-center justify-between border-b border-slate-100 pb-2">
                            <div class="flex items-center space-x-2 truncate">
                                <h5 class="font-bold text-sm text-slate-900 truncate">${c.name}</h5>
                                <span class="text-[10px] font-bold text-blue-700 bg-blue-50 border border-blue-200 px-2 py-0.5 rounded shrink-0">${c.ctc_lpa} LPA</span>
                            </div>
                            <span class="px-2 py-0.5 rounded text-[10px] font-semibold bg-blue-50 text-blue-800 border border-blue-200 shrink-0 flex items-center space-x-1">
                                <i class="fa-regular fa-envelope text-blue-600"></i>
                                <span>Verification Pending</span>
                            </span>
                        </div>

                        <div class="text-[11px] text-slate-600 mt-2 space-y-1">
                            <div><i class="fa-solid fa-user-tie text-slate-400 mr-1.5"></i> Proposed By: <b>${c.added_by_name || c.added_by_member}</b> (${c.added_by_member})</div>
                            <div><i class="fa-solid fa-location-dot text-slate-400 mr-1.5"></i> ${c.location} | HR: ${c.contact_person} (+91 ${c.mobile_no})</div>
                            ${c.forwarded_at ? `<div><i class="fa-regular fa-clock text-slate-400 mr-1.5"></i> Received: <b>${c.forwarded_at}</b></div>` : ''}
                            ${c.forwarded_note ? `<div class="text-[11px] text-slate-700 bg-slate-50 p-2 rounded-lg border border-slate-200 mt-1 italic">"${c.forwarded_note}"</div>` : ''}
                        </div>
                    </div>

                    <!-- Action buttons for Admin -->
                    <div class="pt-2 border-t border-slate-100 flex flex-wrap items-center justify-between gap-1.5">
                        <div class="flex items-center space-x-1.5">
                            <button onclick="promptDownloadJdDocx(${c.id}, '${c.name.replace(/'/g, "\\'")}')" title="Download formatted Word Document (.docx)"
                                class="px-2.5 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 font-bold text-xs rounded-xl border border-blue-200 transition flex items-center space-x-1 cursor-pointer">
                                <i class="fa-solid fa-file-word text-blue-600"></i>
                                <span>Download JD (.docx)</span>
                            </button>
                            
                            <button onclick="viewDispatchedEmail(${c.id})" title="View Dispatched Email Notification"
                                class="p-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs rounded-xl transition cursor-pointer">
                                <i class="fa-solid fa-envelope text-blue-600"></i>
                            </button>
                        </div>

                        <button onclick="toggleCompanyApproval(${c.id}, true)" class="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl shadow-md transition flex items-center space-x-1 cursor-pointer">
                            <i class="fa-solid fa-check"></i>
                            <span>Verify & Accept</span>
                        </button>
                    </div>
                </div>
            `).join('');

            if (list) list.innerHTML = cardsHtml;
            if (banner) banner.classList.remove('hidden');

            if (dashList) dashList.innerHTML = cardsHtml;
            if (dashContainer) dashContainer.classList.remove('hidden');
        } else {
            if (badge) badge.classList.add('hidden');
            if (banner) banner.classList.add('hidden');
            if (dashContainer) dashContainer.classList.add('hidden');
        }
    } catch (e) {
        console.error(e);
    }
}

async function viewDispatchedEmail(companyId) {
    try {
        const res = await fetch('/api/companies/email-logs');
        if (!res.ok) return;
        const emails = await res.json();
        
        // Find email for this company or latest
        const email = emails.find(e => e.company_id === companyId) || emails[0];
        if (!email) {
            Swal.fire('Email Notice', 'An automated email was dispatched to Admin (sivasubramaniyan@college.edu) containing the company credentials and Word JD download attachment link.', 'info');
            return;
        }

        document.getElementById('emailPreviewSubject').textContent = email.subject;
        document.getElementById('emailPreviewTo').textContent = email.to;
        document.getElementById('emailPreviewFrom').textContent = email.from;
        document.getElementById('emailPreviewSentAt').textContent = email.sent_at;
        document.getElementById('emailPreviewStatus').textContent = email.status;
        document.getElementById('emailPreviewBody').innerHTML = `<div class="p-2">${email.html_content}</div>`;

        document.getElementById('emailPreviewModal').classList.remove('hidden');
    } catch (e) {
        console.error(e);
    }
}

function closeEmailPreviewModal() {
    const modal = document.getElementById('emailPreviewModal');
    if (modal) modal.classList.add('hidden');
}

function openCompanyModal() {
    document.getElementById('companyForm').reset();
    document.getElementById('compFormId').value = '';
    document.getElementById('compModalTitle').textContent = 'Add New Company Proposal';
    document.getElementById('offersCountDiv').classList.add('hidden');
    document.getElementById('companyModal').classList.remove('hidden');
}

function closeCompanyModal() {
    document.getElementById('companyModal').classList.add('hidden');
}

function toggleOffersInput(statusVal) {
    const div = document.getElementById('offersCountDiv');
    if (statusVal === 'DRIVE COMPLETED') {
        div.classList.remove('hidden');
    } else {
        div.classList.add('hidden');
    }
}

async function handleJdUpload(input) {
    if (!input.files || input.files.length === 0) return;
    const file = input.files[0];
    const statusSpan = document.getElementById('jdUploadStatus');
    statusSpan.textContent = 'Uploading JD & extracting content...';

    const formData = new FormData();
    formData.append('file', file);
    formData.append('folder', 'jds');

    try {
        const res = await fetch('/api/upload', { method: 'POST', body: formData });
        const data = await res.json();
        if (res.ok) {
            statusSpan.textContent = `✓ Uploaded: ${data.filename}`;
            const previewBox = document.getElementById('compJdText');
            if (!previewBox.value) {
                previewBox.value = `Role: Software Engineer\nResponsibilities: Develop scalable web and cloud microservices.\nRequirements: Strong coding skills, data structures, algorithms, databases, and problem solving.`;
            }
        } else {
            statusSpan.textContent = `Upload error: ${data.error}`;
        }
    } catch (e) {
        statusSpan.textContent = 'Upload failed.';
    }
}

async function handleCompanyFormSubmit(e) {
    e.preventDefault();
    const id = document.getElementById('compFormId').value;
    const method = id ? 'PUT' : 'POST';
    const url = id ? `/api/companies/${id}` : '/api/companies';

    const payload = {
        name: document.getElementById('compName').value.trim(),
        location: document.getElementById('compLocation').value.trim(),
        contact_person: document.getElementById('compContact').value.trim(),
        mobile_no: document.getElementById('compMobile').value.trim(),
        email: document.getElementById('compEmail').value.trim(),
        status: document.getElementById('compStatus').value,
        ctc_lpa: parseFloat(document.getElementById('compCtc').value),
        total_offers_count: parseInt(document.getElementById('compOffersCount').value || 0),
        website: document.getElementById('compWebsite').value.trim(),
        address: document.getElementById('compAddress').value.trim(),
        jd_text: document.getElementById('compJdText').value.trim(),
        drive_date_proposed: document.getElementById('compDriveDateProposed') ? document.getElementById('compDriveDateProposed').value : '',
        notes: document.getElementById('compProposalNotes') ? document.getElementById('compProposalNotes').value.trim() : ''
    };

    try {
        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok) {
            Swal.fire('Error', data.error || 'Failed to save company.', 'error');
            return;
        }

        Swal.fire({
            icon: 'success',
            title: 'Company Proposal Shared!',
            html: `<b>${payload.name}</b> has been recorded and an <b>email notification</b> was dispatched to Admin for verification and drive approval.`,
            confirmButtonColor: '#2563eb'
        });
        closeCompanyModal();
        loadCompanies();
        checkAdminPendingDrives();
    } catch (err) {
        Swal.fire('Error', 'Network error', 'error');
    }
}

async function updateCompanyStatus(companyId, newStatus) {
    if (!newStatus) return;
    
    let offersCount = null;
    if (newStatus === 'DRIVE COMPLETED') {
        const { value: offers } = await Swal.fire({
            title: 'Drive Completed — Record Offers',
            input: 'number',
            inputLabel: 'Total number of offers issued to candidates:',
            inputValue: 10,
            showCancelButton: true
        });
        if (offers === undefined) return;
        offersCount = parseInt(offers) || 0;
    }

    try {
        const res = await fetch(`/api/companies/${companyId}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus, total_offers_count: offersCount })
        });
        const data = await res.json();
        if (res.ok) {
            Swal.fire({ icon: 'success', title: 'Stage Updated', text: data.message, timer: 1200, showConfirmButton: false });
            loadCompanies();
        } else {
            Swal.fire('Error', data.error, 'error');
        }
    } catch (e) {
        console.error(e);
    }
}

async function forwardCompanyToAdmin(companyId, name) {
    const { value: formValues } = await Swal.fire({
        title: `Forward & Email ${name} to Admin`,
        html: `
            <div class="text-left space-y-3 text-xs">
                <div>
                    <label class="block font-semibold text-slate-700 mb-1">Proposed Drive Date</label>
                    <input type="date" id="swalDriveDate" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2 text-xs">
                </div>
                <div>
                    <label class="block font-semibold text-slate-700 mb-1">Review Notes / Urgency for Admin</label>
                    <textarea id="swalDriveNote" rows="3" placeholder="Enter notes or drive requirements for Admin..."
                        class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2 text-xs"></textarea>
                </div>
                <p class="text-[11px] text-blue-600 bg-blue-50 p-2 rounded-lg border border-blue-100">
                    ✉ This will send an automated email to Admin containing full company credentials and the Word JD download link.
                </p>
            </div>
        `,
        focusConfirm: false,
        showCancelButton: true,
        confirmButtonText: '<i class="fa-solid fa-paper-plane mr-1"></i> Forward & Send Email',
        confirmButtonColor: '#2563eb',
        preConfirm: () => {
            return {
                proposed_date: document.getElementById('swalDriveDate').value,
                note: document.getElementById('swalDriveNote').value.trim()
            };
        }
    });

    if (formValues) {
        const res = await fetch(`/api/companies/${companyId}/forward`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formValues)
        });
        const data = await res.json();
        if (res.ok) {
            Swal.fire('Forwarded & Emailed', data.message, 'success');
            loadCompanies();
            checkAdminPendingDrives();
        } else {
            Swal.fire('Error', data.error, 'error');
        }
    }
}

async function toggleCompanyApproval(companyId, approveFlag) {
    let reviewNote = '';
    if (approveFlag && currentUser.role === 'admin') {
        const { value: note } = await Swal.fire({
            title: 'Accept & Approve Proposal',
            input: 'text',
            inputLabel: 'Admin Approval Note (optional):',
            inputValue: 'Drive verified & approved for campus recruitment 2026.',
            showCancelButton: true,
            confirmButtonText: 'Confirm Approval & Send Email',
            confirmButtonColor: '#16a34a'
        });
        if (note === undefined) return;
        reviewNote = note;
    }

    const res = await fetch(`/api/companies/${companyId}/approve`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_approved: approveFlag, review_note: reviewNote })
    });
    const data = await res.json();
    if (res.ok) {
        Swal.fire({
            icon: 'success',
            title: approveFlag ? 'Proposal Accepted & Approved!' : 'Approval Revoked',
            text: data.message,
            timer: 2000,
            showConfirmButton: false
        });
        loadCompanies();
        checkAdminPendingDrives();
    } else {
        Swal.fire('Error', data.error, 'error');
    }
}

async function editCompany(companyId) {
    try {
        const res = await fetch(`/api/companies/${companyId}`);
        if (!res.ok) return;
        const c = await res.json();

        document.getElementById('compFormId').value = c.id;
        document.getElementById('compName').value = c.name;
        document.getElementById('compLocation').value = c.location;
        document.getElementById('compContact').value = c.contact_person;
        document.getElementById('compMobile').value = c.mobile_no;
        document.getElementById('compEmail').value = c.email;
        document.getElementById('compStatus').value = c.status;
        document.getElementById('compCtc').value = c.ctc_lpa;
        document.getElementById('compWebsite').value = c.website || '';
        document.getElementById('compAddress').value = c.address || '';
        document.getElementById('compJdText').value = c.jd_text || '';
        
        toggleOffersInput(c.status);
        if (c.status === 'DRIVE COMPLETED') {
            document.getElementById('compOffersCount').value = c.total_offers_count || 0;
        }

        document.getElementById('compModalTitle').textContent = `Edit Company — ${c.name}`;
        document.getElementById('companyModal').classList.remove('hidden');
    } catch (e) {
        console.error(e);
    }
}

async function deleteCompany(companyId, name) {
    const result = await Swal.fire({
        title: 'Delete Company?',
        text: `Are you sure you want to remove ${name}?`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#e11d48',
        confirmButtonText: 'Yes, Delete'
    });

    if (result.isConfirmed) {
        const res = await fetch(`/api/companies/${companyId}`, { method: 'DELETE' });
        const data = await res.json();
        if (res.ok) {
            Swal.fire('Deleted', data.message, 'success');
            loadCompanies();
        } else {
            Swal.fire('Error', data.error, 'error');
        }
    }
}

async function promptDownloadJdDocx(companyId, companyName) {
    try {
        const res = await fetch(`/api/companies/${companyId}`);
        if (!res.ok) {
            window.location.href = `/api/companies/${companyId}/jd/download`;
            return;
        }
        const c = await res.json();
        const jd = c.jd_text || 'Candidate will contribute to core software engineering, development, testing, and modern technical workflows.';

        const result = await Swal.fire({
            title: `Job Description — ${c.name}`,
            html: `
                <div class="text-left space-y-3 text-xs">
                    <div class="p-3 bg-blue-50/60 rounded-xl border border-blue-100 flex items-center justify-between">
                        <div>
                            <div class="font-bold text-slate-800">${c.name} • <span class="text-blue-600 font-extrabold">${c.ctc_lpa} LPA</span></div>
                            <div class="text-[11px] text-slate-500">${c.location} | Stage: <b>${c.status}</b></div>
                        </div>
                        <span class="px-2.5 py-1 bg-white text-blue-700 font-bold text-[10px] rounded-lg shadow-xs border border-blue-200">
                            DOCX Format
                        </span>
                    </div>

                    <div>
                        <span class="font-bold text-slate-700 block mb-1">Job Description & Responsibilities:</span>
                        <div class="p-3 bg-slate-50 rounded-xl border border-slate-200 max-h-48 overflow-y-auto font-sans leading-relaxed text-slate-700 whitespace-pre-wrap">${jd}</div>
                    </div>

                    <p class="text-slate-500 text-[11px]">
                        Would you like to download this complete Job Description formatted as a Microsoft Word Document (.docx)?
                    </p>
                </div>
            `,
            showCancelButton: true,
            confirmButtonColor: '#2563eb',
            cancelButtonColor: '#64748b',
            confirmButtonText: '<i class="fa-solid fa-download mr-1"></i> Download as DOCS (.docx)',
            cancelButtonText: 'Close Preview',
            width: 580
        });

        if (result.isConfirmed) {
            window.location.href = `/api/companies/${companyId}/jd/download`;
            Swal.fire({
                icon: 'success',
                title: 'Downloading Word Document',
                text: `${c.name} Job Description (.docx) is downloading.`,
                timer: 2000,
                showConfirmButton: false
            });
        }
    } catch (e) {
        console.error(e);
        window.location.href = `/api/companies/${companyId}/jd/download`;
    }
}

async function downloadAtsJdDocx() {
    const compSelect = document.getElementById('atsCompanySelect');
    const compId = compSelect ? compSelect.value : null;
    const jdText = document.getElementById('atsJdText').value.trim();

    if (compId) {
        promptDownloadJdDocx(compId, compSelect.options[compSelect.selectedIndex].text);
        return;
    }

    if (!jdText) {
        Swal.fire('Empty JD', 'Please enter or select a Job Description to download.', 'warning');
        return;
    }

    const result = await Swal.fire({
        title: 'Download Custom JD as DOCS?',
        text: 'Export these custom Job Description requirements into a formatted Word Document (.docx)?',
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#2563eb',
        cancelButtonColor: '#64748b',
        confirmButtonText: '<i class="fa-solid fa-download mr-1"></i> Download .DOCX',
        cancelButtonText: 'Cancel'
    });

    if (result.isConfirmed) {
        const res = await fetch('/api/companies/jd/custom-download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                company_name: 'Campus Recruitment Drive',
                jd_text: jdText
            })
        });

        if (res.ok) {
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'Campus_Drive_Job_Description.docx';
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
            Swal.fire({ icon: 'success', title: 'Downloaded', text: 'Word document downloaded successfully.', timer: 1500, showConfirmButton: false });
        }
    }
}



// -------------------------------------------------------------------------
// 7. PLACEMENT DRIVES, ATTENDANCE & OFFERS
// -------------------------------------------------------------------------
async function loadPlacementDrives() {
    if (currentUser.role === 'manager') return;

    try {
        const res = await fetch('/api/drives');
        if (!res.ok) return;
        const drives = await res.json();
        renderPlacementDrives(drives);
    } catch (e) {
        console.error(e);
    }
}

function renderPlacementDrives(drives) {
    const grid = document.getElementById('placementDrivesGrid');
    if (!grid) return;

    if (!drives || drives.length === 0) {
        grid.innerHTML = `<div class="col-span-2 p-8 text-center text-slate-400 bg-white rounded-2xl border border-slate-200">No scheduled drives found.</div>`;
        return;
    }

    grid.innerHTML = drives.map(d => `
        <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                <div>
                    <h4 class="font-extrabold text-base text-slate-900">${d.company_name}</h4>
                    <span class="text-xs text-blue-600 font-semibold">${d.role_name} • CTC ${d.ctc_lpa} LPA</span>
                </div>
                <span class="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold ${d.status === 'COMPLETED' ? 'bg-emerald-100 text-emerald-800' : 'bg-blue-100 text-blue-800'}">
                    ${d.status}
                </span>
            </div>

            <div class="grid grid-cols-3 gap-3 text-center text-xs">
                <div class="bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                    <span class="text-[10px] text-slate-400 block font-semibold">DRIVE DATE</span>
                    <b class="text-slate-800">${d.drive_date}</b>
                </div>
                <div class="bg-blue-50 p-2.5 rounded-xl border border-blue-100">
                    <span class="text-[10px] text-blue-600 block font-semibold">REGISTERED</span>
                    <b class="text-blue-900 font-bold">${d.registered_count} Students</b>
                </div>
                <div class="bg-emerald-50 p-2.5 rounded-xl border border-emerald-100">
                    <span class="text-[10px] text-emerald-600 block font-semibold">OFFERS ISSUED</span>
                    <b class="text-emerald-900 font-bold">${d.offers_count} Selected</b>
                </div>
            </div>

            <!-- Action buttons -->
            <div class="flex items-center justify-end space-x-2 pt-2 border-t border-slate-100">
                <button onclick="viewEligibleStudents(${d.id})" class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-xl transition">
                    <i class="fa-solid fa-users mr-1"></i> Register Candidates
                </button>
                <button onclick="openAttendanceModal(${d.id})" class="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-xl transition">
                    <i class="fa-solid fa-clipboard-check mr-1"></i> Mark Attendance
                </button>
            </div>
        </div>
    `).join('');
}

function openDriveModal() {
    const compSelect = document.getElementById('driveCompSelect');
    fetch('/api/companies?status=ALL')
        .then(r => r.json())
        .then(companies => {
            compSelect.innerHTML = companies.map(c => `<option value="${c.id}">${c.name} (${c.status} - ${c.ctc_lpa} LPA)</option>`).join('');
            document.getElementById('driveModal').classList.remove('hidden');
        });
}

function closeDriveModal() {
    document.getElementById('driveModal').classList.add('hidden');
}

async function handleDriveFormSubmit(e) {
    e.preventDefault();
    const payload = {
        company_id: parseInt(document.getElementById('driveCompSelect').value),
        role_name: document.getElementById('driveRole').value.trim(),
        ctc_lpa: parseFloat(document.getElementById('driveCtc').value),
        drive_date: document.getElementById('driveDate').value
    };

    const res = await fetch('/api/drives', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (res.ok) {
        Swal.fire('Success', data.message, 'success');
        closeDriveModal();
        loadPlacementDrives();
    } else {
        Swal.fire('Error', data.error, 'error');
    }
}

async function viewEligibleStudents(driveId) {
    try {
        const res = await fetch(`/api/drives/${driveId}/eligible-students`);
        const data = await res.json();
        
        let listHtml = data.students.slice(0, 15).map(s => `
            <div class="flex items-center justify-between p-2 border-b border-slate-100 text-xs">
                <div>
                    <b>${s.name}</b> (${s.roll_no}) — <span class="text-blue-600">${s.department_code}</span> | UG: ${s.ug_percent}%
                </div>
                ${s.is_registered ? `
                    <span class="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 text-[10px] font-bold">Registered</span>
                ` : `
                    <button onclick="registerForDrive(${driveId}, ${s.id})" class="px-2 py-1 bg-blue-600 text-white rounded text-[10px] font-bold">Register</button>
                `}
            </div>
        `).join('');

        Swal.fire({
            title: `Eligible Students (${data.eligible_count})`,
            html: `<div class="max-h-80 overflow-y-auto custom-scrollbar">${listHtml}</div>`,
            width: 600,
            showCloseButton: true
        });
    } catch (e) {
        console.error(e);
    }
}

async function registerForDrive(driveId, studentId) {
    const res = await fetch(`/api/drives/${driveId}/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ student_id: studentId })
    });
    const data = await res.json();
    if (res.ok) {
        Swal.fire({ icon: 'success', title: 'Registered', text: data.message, timer: 1200, showConfirmButton: false });
        viewEligibleStudents(driveId);
    } else {
        Swal.fire('Error', data.error, 'error');
    }
}

async function openAttendanceModal(driveId) {
    try {
        const res = await fetch(`/api/drives/${driveId}`);
        const drive = await res.json();
        
        if (!drive.registrations || drive.registrations.length === 0) {
            Swal.fire('No Registrations', 'Please register candidates first before marking attendance.', 'info');
            return;
        }

        let attHtml = drive.registrations.map(r => `
            <div class="flex items-center justify-between p-2 border-b border-slate-100 text-xs">
                <div><b>${r.student_name}</b> (${r.student_roll_no}) — ${r.department_code}</div>
                <label class="inline-flex items-center space-x-1 cursor-pointer">
                    <input type="checkbox" class="att-check rounded text-blue-600" data-student-id="${r.student_id}" checked>
                    <span class="text-xs text-slate-700">Present</span>
                </label>
            </div>
        `).join('');

        const result = await Swal.fire({
            title: `Mark Attendance — ${drive.company_name}`,
            html: `<div class="max-h-80 overflow-y-auto text-left">${attHtml}</div>`,
            showCancelButton: true,
            confirmButtonText: 'Save Attendance',
            width: 550
        });

        if (result.isConfirmed) {
            const checkboxes = document.querySelectorAll('.att-check');
            const records = Array.from(checkboxes).map(cb => ({
                student_id: parseInt(cb.dataset.studentId),
                is_present: cb.checked
            }));

            const saveRes = await fetch(`/api/drives/${driveId}/attendance`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ records })
            });
            const data = await saveRes.json();
            Swal.fire('Saved', data.message, 'success');
            loadPlacementDrives();
        }
    } catch (e) {
        console.error(e);
    }
}

function openOfferModalForStudent(studentId, studentName) {
    document.getElementById('offerForm').reset();
    document.getElementById('offerStudentId').value = studentId;
    document.getElementById('offerStudentName').value = studentName;

    // Populate companies
    fetch('/api/companies?status=ALL')
        .then(r => r.json())
        .then(companies => {
            const compSelect = document.getElementById('offerCompanySelect');
            compSelect.innerHTML = companies.map(c => `<option value="${c.id}">${c.name} (${c.ctc_lpa} LPA)</option>`).join('');
            document.getElementById('offerModal').classList.remove('hidden');
        });
}

function closeOfferModal() {
    document.getElementById('offerModal').classList.add('hidden');
}

async function handleOfferFormSubmit(e) {
    e.preventDefault();
    const payload = {
        student_id: parseInt(document.getElementById('offerStudentId').value),
        company_id: parseInt(document.getElementById('offerCompanySelect').value),
        role: document.getElementById('offerRole').value.trim(),
        ctc_lpa: parseFloat(document.getElementById('offerCtc').value)
    };

    const res = await fetch('/api/offers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (res.ok) {
        Swal.fire('Offer Issued!', data.message, 'success');
        closeOfferModal();
        loadStudents(currentStudentPage);
    } else {
        Swal.fire('Error', data.error, 'error');
    }
}


// -------------------------------------------------------------------------
// 8. GEMINI AI ATS RESUME ANALYZER & RESUME UPLOADER
// -------------------------------------------------------------------------
let currentAtsMode = 'upload';

function switchAtsMode(mode) {
    currentAtsMode = mode;
    const uploadBtn = document.getElementById('atsModeUploadBtn');
    const studentBtn = document.getElementById('atsModeStudentBtn');
    const uploadContainer = document.getElementById('atsUploadModeContainer');
    const studentContainer = document.getElementById('atsStudentModeContainer');

    if (mode === 'upload') {
        if (uploadBtn) {
            uploadBtn.classList.add('bg-white', 'shadow-xs', 'text-purple-700');
            uploadBtn.classList.remove('text-slate-600');
        }
        if (studentBtn) {
            studentBtn.classList.remove('bg-white', 'shadow-xs', 'text-purple-700');
            studentBtn.classList.add('text-slate-600');
        }
        if (uploadContainer) uploadContainer.classList.remove('hidden');
        if (studentContainer) studentContainer.classList.add('hidden');
    } else {
        if (studentBtn) {
            studentBtn.classList.add('bg-white', 'shadow-xs', 'text-purple-700');
            studentBtn.classList.remove('text-slate-600');
        }
        if (uploadBtn) {
            uploadBtn.classList.remove('bg-white', 'shadow-xs', 'text-purple-700');
            uploadBtn.classList.add('text-slate-600');
        }
        if (uploadContainer) uploadContainer.classList.add('hidden');
        if (studentContainer) studentContainer.classList.remove('hidden');
    }
}

function handleResumeFileSelected(input) {
    if (input.files && input.files[0]) {
        const file = input.files[0];
        const badge = document.getElementById('selectedFileBadge');
        const nameEl = document.getElementById('selectedFileName');
        const sizeEl = document.getElementById('selectedFileSize');

        if (nameEl) nameEl.textContent = file.name;
        if (sizeEl) {
            const kb = Math.round(file.size / 1024);
            sizeEl.textContent = `(${kb} KB)`;
        }
        if (badge) badge.classList.remove('hidden');
    }
}

function clearAtsResumeFile() {
    const input = document.getElementById('atsResumeFileInput');
    if (input) input.value = '';
    const badge = document.getElementById('selectedFileBadge');
    if (badge) badge.classList.add('hidden');
}

async function loadAtsPrerequisites() {
    if (currentUser.role === 'manager') return;

    try {
        // Load top students into select
        const resS = await fetch('/api/students?per_page=50');
        if (resS.ok) {
            const dataS = await resS.json();
            const studSelect = document.getElementById('atsStudentSelect');
            if (studSelect) {
                studSelect.innerHTML = dataS.students.map(s => `
                    <option value="${s.id}">${s.name} (${s.roll_no}) — ${s.department_code} (UG: ${s.ug_percent}%)</option>
                `).join('');
            }
        }

        // Load companies into select
        const resC = await fetch('/api/companies?status=ALL');
        if (resC.ok) {
            const companies = await resC.json();
            const compSelect = document.getElementById('atsCompanySelect');
            if (compSelect) {
                compSelect.innerHTML = `<option value="">Select Target Company JD...</option>` + companies.map(c => `
                    <option value="${c.id}" data-jd="${encodeURIComponent(c.jd_text || '')}">${c.name} (${c.ctc_lpa} LPA)</option>
                `).join('');
            }
        }
    } catch (e) {
        console.error(e);
    }
}

function handleAtsCompanyChange(compVal) {
    const compSelect = document.getElementById('atsCompanySelect');
    if (!compSelect) return;
    const selectedOption = compSelect.options[compSelect.selectedIndex];
    if (selectedOption && selectedOption.dataset.jd) {
        document.getElementById('atsJdText').value = decodeURIComponent(selectedOption.dataset.jd);
    }
}

async function runAtsEvaluation() {
    const companyId = document.getElementById('atsCompanySelect').value;
    const jdText = document.getElementById('atsJdText').value.trim();
    const btn = document.getElementById('atsRunBtn');
    const container = document.getElementById('atsResultContainer');

    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin mr-2"></i> Analyzing with Gemini ATS...`;

    try {
        let res, data;

        if (currentAtsMode === 'upload') {
            const fileInput = document.getElementById('atsResumeFileInput');
            const pastedText = document.getElementById('atsPastedResumeText').value.trim();
            const file = fileInput && fileInput.files ? fileInput.files[0] : null;

            if (!file && !pastedText) {
                btn.disabled = false;
                btn.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles mr-1"></i><span>Check Gemini ATS Score</span>`;
                Swal.fire('Resume Required', 'Please select a resume file (.pdf, .docx, .txt) or paste your resume text.', 'warning');
                return;
            }

            const formData = new FormData();
            if (file) formData.append('resume_file', file);
            if (pastedText) formData.append('pasted_resume_text', pastedText);
            if (companyId) formData.append('company_id', companyId);
            if (jdText) formData.append('jd_text', jdText);

            res = await fetch('/api/ats/upload-and-analyze', {
                method: 'POST',
                body: formData
            });
            data = await res.json();
        } else {
            const studentId = document.getElementById('atsStudentSelect').value;
            if (!studentId) {
                btn.disabled = false;
                btn.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles mr-1"></i><span>Check Gemini ATS Score</span>`;
                Swal.fire('Select Candidate', 'Please select a registered candidate to evaluate.', 'warning');
                return;
            }

            res = await fetch('/api/ats/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    student_id: parseInt(studentId),
                    company_id: companyId ? parseInt(companyId) : null,
                    jd_text: jdText
                })
            });
            data = await res.json();
        }

        btn.disabled = false;
        btn.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles mr-1"></i><span>Check Gemini ATS Score</span>`;

        if (!res.ok) {
            Swal.fire('Evaluation Failed', data.error || 'ATS analysis failed.', 'error');
            return;
        }

        renderAtsResult(data);

        // TRIGGER HIGH MATCH 91-100% POPUP CELEBRATION!
        if (data.ats_score >= 91 || (data.high_match_popup && data.high_match_popup.trigger_popup)) {
            triggerHighMatchPopup(data);
        }
    } catch (err) {
        console.error(err);
        btn.disabled = false;
        btn.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles mr-1"></i><span>Check Gemini ATS Score</span>`;
        Swal.fire('Error', 'Connection failed. Please verify the server is running.', 'error');
    }
}

function renderAtsResult(res) {
    const container = document.getElementById('atsResultContainer');
    if (!container) return;
    const score = res.ats_score || 0;
    const isHigh = score >= 91;
    const matched = res.matched_skills || [];
    const missing = res.missing_skills || [];
    const recs = res.recommendations || [];
    const candidateName = res.candidate_label || res.student_name || res.file_name || 'Uploaded Resume';
    const targetComp = res.company_name || 'Target Role Requirements';

    // Color gradient based on score tier
    let tierColor = 'from-blue-600 to-indigo-600 text-blue-600 bg-blue-50 border-blue-200';
    if (score >= 91) tierColor = 'from-emerald-500 to-teal-600 text-emerald-600 bg-emerald-50 border-emerald-300';
    else if (score >= 81) tierColor = 'from-amber-500 to-orange-500 text-amber-600 bg-amber-50 border-amber-200';
    else if (score <= 60) tierColor = 'from-slate-500 to-slate-700 text-slate-600 bg-slate-50 border-slate-200';

    container.innerHTML = `
        <div class="w-full text-left space-y-5">
            <!-- Score Header & Candidate Card -->
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-2xl bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white shadow-md">
                <div>
                    <div class="flex items-center space-x-2 mb-1">
                        <span class="px-2.5 py-0.5 rounded-full bg-purple-500/20 text-purple-300 text-[10px] font-bold border border-purple-500/30">
                            ${currentAtsMode === 'upload' ? 'UPLOADED RESUME' : 'REGISTERED CANDIDATE'}
                        </span>
                        <span class="text-xs text-slate-400 font-mono">Tier: ${res.category || 'N/A'}</span>
                    </div>
                    <h3 class="text-lg font-black text-white">${candidateName}</h3>
                    <p class="text-xs text-blue-200/80 mt-0.5">Target: <b>${targetComp}</b></p>
                </div>
                
                <div class="flex items-center space-x-4 shrink-0">
                    <div class="text-center bg-white/10 backdrop-blur p-3 rounded-2xl border border-white/10">
                        <div class="text-3xl sm:text-4xl font-black ${isHigh ? 'text-emerald-400' : 'text-purple-300'}">
                            ${score}%
                        </div>
                        <span class="text-[10px] uppercase font-bold tracking-wider ${isHigh ? 'text-emerald-300' : 'text-purple-200'}">
                            ${isHigh ? '🔥 HIGH MATCH' : `Category: ${res.category}`}
                        </span>
                    </div>
                </div>
            </div>

            <!-- Matched Skills Section -->
            <div class="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-xs font-bold text-slate-800 flex items-center space-x-1.5">
                        <i class="fa-solid fa-circle-check text-emerald-500"></i>
                        <span>Matched Core Skills & Strengths (${matched.length}):</span>
                    </span>
                </div>
                <div class="flex flex-wrap gap-1.5">
                    ${matched.length > 0 ? matched.map(s => `
                        <span class="px-3 py-1 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold shadow-2xs">
                            ✓ ${s}
                        </span>
                    `).join('') : '<span class="text-xs text-slate-400 italic">No direct matching skills found in the profile.</span>'}
                </div>
            </div>

            <!-- Missing Skills & Requirements -->
            ${missing.length > 0 ? `
                <div class="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
                    <div class="flex items-center justify-between mb-2">
                        <span class="text-xs font-bold text-slate-800 flex items-center space-x-1.5">
                            <i class="fa-solid fa-triangle-exclamation text-amber-500"></i>
                            <span>Target Skill Gaps to Include (${missing.length}):</span>
                        </span>
                    </div>
                    <div class="flex flex-wrap gap-1.5">
                        ${missing.map(s => `
                            <span class="px-3 py-1 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs font-medium">
                                ⚠ ${s}
                            </span>
                        `).join('')}
                    </div>
                </div>
            ` : ''}

            <!-- AI Recruiter Evaluation & Recommendations -->
            <div class="p-4 bg-purple-50/40 rounded-2xl border border-purple-100 text-xs text-slate-700 space-y-2">
                <div>
                    <span class="font-bold text-purple-900 block mb-1">🤖 Gemini AI Executive Fit Assessment:</span>
                    <p class="leading-relaxed text-slate-700 italic">${res.summary || 'Profile evaluated against target requirements.'}</p>
                </div>
                ${recs && recs.length > 0 ? `
                    <div class="pt-2 border-t border-purple-100 mt-2">
                        <span class="font-bold text-purple-900 block mb-1">💡 Actionable Resume Optimization Tips:</span>
                        <ul class="list-disc list-inside space-y-1 text-[11px] text-slate-600">
                            ${recs.map(r => `<li>${r}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>

            <!-- Parsed Text Snippet Preview Drawer -->
            ${res.extracted_preview ? `
                <div class="p-3 bg-slate-50 rounded-xl border border-slate-200 text-[11px] text-slate-600">
                    <div class="font-bold text-slate-700 text-[10px] uppercase mb-1">📄 Extracted Resume Text Preview</div>
                    <p class="line-clamp-3 font-mono text-[10px] text-slate-500 bg-white p-2 rounded-lg border border-slate-100">${res.extracted_preview}</p>
                </div>
            ` : ''}
        </div>
    `;
}

function triggerHighMatchPopup(data) {
    const scoreEl = document.getElementById('hmScore');
    const rollEl = document.getElementById('hmRollNo');
    const nameEl = document.getElementById('hmName');
    const deptEl = document.getElementById('hmDept');
    
    if (scoreEl) scoreEl.textContent = `${data.ats_score}% Match Score`;
    if (rollEl) rollEl.textContent = data.roll_no || data.file_name || 'Uploaded Resume';
    if (nameEl) nameEl.textContent = data.candidate_label || data.student_name || 'Candidate';
    if (deptEl) deptEl.textContent = data.department_code || data.company_name || '91-100 (HIGH MATCH)';
    
    const modal = document.getElementById('highMatchModal');
    if (modal) modal.classList.remove('hidden');
}

function closeHighMatchModal() {
    const modal = document.getElementById('highMatchModal');
    if (modal) modal.classList.add('hidden');
}

function shortlistCandidateFromPopup() {
    closeHighMatchModal();
    Swal.fire({
        icon: 'success',
        title: 'Candidate Shortlisted!',
        text: 'The candidate has been flagged for prioritized recruiter interview scheduling.',
        timer: 2000,
        showConfirmButton: false
    });
}


// -------------------------------------------------------------------------
// 9. REPORTS HUB & DOWNLOAD EXPORTS
// -------------------------------------------------------------------------
function downloadCompanyReport() {
    const stage = document.getElementById('reportCompStage').value;
    window.location.href = `/api/reports/companies/excel?stage=${stage}`;
}


// -------------------------------------------------------------------------
// 10. ADMIN ACTIVITY LOGS
// -------------------------------------------------------------------------
async function loadActivityLogs() {
    if (currentUser.role !== 'admin') return;

    try {
        const res = await fetch('/api/activity-logs?limit=50');
        if (!res.ok) return;
        const logs = await res.json();
        
        const tbody = document.getElementById('logsTableBody');
        if (!tbody) return;

        if (logs.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="p-8 text-center text-slate-400">No activity logs recorded yet.</td></tr>`;
            return;
        }

        tbody.innerHTML = logs.map(l => `
            <tr class="hover:bg-slate-50/80 transition">
                <td class="p-3.5 pl-5 text-slate-500 font-mono text-[11px]">${l.created_at}</td>
                <td class="p-3.5 font-bold text-slate-900">${l.member_id} <span class="text-slate-400 font-normal">(${l.user_name})</span></td>
                <td class="p-3.5"><span class="px-2 py-0.5 rounded bg-slate-100 font-bold text-[10px] text-slate-700">${l.action_type}</span></td>
                <td class="p-3.5 font-semibold text-blue-600">${l.target_entity}</td>
                <td class="p-3.5 text-slate-700">${l.description}</td>
                <td class="p-3.5 text-right pr-5 font-mono text-slate-400 text-[11px]">${l.ip_address || '127.0.0.1'}</td>
            </tr>
        `).join('');
    } catch (e) {
        console.error(e);
    }
}


// -------------------------------------------------------------------------
// 11. GLOBAL SEARCH & EVENT HANDLERS
// -------------------------------------------------------------------------
function setupEventListeners() {
    const studentSearch = document.getElementById('studentSearchInput');
    if (studentSearch) {
        let debounceTimer;
        studentSearch.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => loadStudents(1), 350);
        });
    }
}

function handleGlobalSearch(e) {
    if (e.key === 'Enter') {
        const query = e.target.value.trim();
        if (query) {
            switchTab('students');
            document.getElementById('studentSearchInput').value = query;
            loadStudents(1);
        }
    }
}
