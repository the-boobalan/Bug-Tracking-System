
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from .models import RegisterModel, Project, Team, TeamMember, Bug, BugHistory, BugComment
from django.db.models import Q


def _role(request, expected_role):
    return bool(request.user.is_authenticated) and request.user.role.lower() == expected_role


def _user_id(request):
    return request.user.id if request.user.is_authenticated else None


def _manager_project_queryset(request):
    return Project.objects.filter(manager_id=_user_id(request))


def _manager_bug_queryset(request):
    return Bug.objects.filter(project__manager_id=_user_id(request))


def _visible_bug_queryset(request):
    user_id = _user_id(request)
    role = request.user.role.lower() if request.user.is_authenticated else ""
    if role == "admin":
        return Bug.objects.all()
    if role == "manager":
        return _manager_bug_queryset(request)
    if role == "developer":
        return Bug.objects.filter(assigned_to_id=user_id)
    if role == "tester":
        return Bug.objects.filter(created_by_id=user_id)
    return Bug.objects.none()


# REGISTER


def home(request):
    return render(request, 'home.html')

def register(request):

    if request.method == "POST":

        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        role = request.POST.get("role", "").lower()

        if role not in {"manager", "developer", "tester"}:
            messages.error(request, "Please select a valid role")
            return redirect("register")

        if password != confirm_password:
            messages.error(request, "Password does not match")
            return redirect("register")

        if RegisterModel.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return redirect("register")

        user = RegisterModel(
            username=username,
            email=email,
            role=role
        )

        user.set_password(password)
        user.save()

        messages.success(request, "Account created successfully")
        return redirect("login")

    return render(request, "register.html")



# LOGIN


def login(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:

            auth_login(request, user)

            request.session["user_id"] = user.id
            request.session["username"] = user.username
            request.session["role"] = user.role

            return redirect("dashboard")

        messages.error(request, "Invalid username or password")

    return render(request, "login.html")



# DASHBOARD ROUTER



def dashboard(request):

    # 1. Check login session
    if not request.user.is_authenticated:
        return redirect("login")

    role = request.user.role.lower()
    user_id = _user_id(request)

    # 3. Get all projects
    if role == "admin":
        projects = Project.objects.all()
        teams = Team.objects.all()
    elif role == "manager":
        projects = Project.objects.filter(manager_id=user_id)
        teams = Team.objects.filter(project__manager_id=user_id)
    else:
        projects = Project.objects.filter(team__teammember__user_id=user_id).distinct()
        teams = Team.objects.filter(teammember__user_id=user_id).distinct()
    team_data = []

    for team in teams:

        developers = TeamMember.objects.filter(team=team, role="Developer")
        testers = TeamMember.objects.filter(team=team, role="Tester")

        team_data.append({
            "team": team,
            "developers": developers,
            "testers": testers
        })

    # 5. Get bugs based on role
    if role == "developer":
        bugs = Bug.objects.filter(assigned_to_id=user_id)

    elif role == "tester":
        bugs = Bug.objects.filter(created_by_id=user_id)

    elif role == "manager":
        bugs = Bug.objects.filter(project__manager_id=user_id)

    elif role == "admin":
        bugs = Bug.objects.all()
    else:
        bugs = Bug.objects.none()

    

    # ✅ TO DO → Open + Assigned
    todo_bugs = bugs.filter(
        Q(status="Open") | Q(status="Assigned")
    )

    # ✅ IN PROGRESS → In Progress
    progress_bugs = bugs.filter(status="In Progress")

    # ✅ DONE → Resolved + Verified + Closed
    done_bugs = bugs.filter(
        Q(status="Resolved") |
        Q(status="Verified") |
        Q(status="Closed")
    )

    kanban_board = {
        "todo": todo_bugs,
        "progress": progress_bugs,
        "done": done_bugs
    }

    context = {
        "projects": projects,
        "team_data": team_data,
        "bugs": bugs,
        "kanban_board": kanban_board,
        "role": role
    }

    return render(request, "dashboard.html", context)

# LOGOUT


def log_out(request):

    auth_logout(request)
    request.session.flush()
    return redirect("login")


# ADMIN DASHBOARD


def admin_dashboard(request):

    if not _role(request, "admin"):
        return redirect("login")

    projects = Project.objects.all()

    return render(request, "admin_dashboard.html", {
        "projects": projects
    })



# CREATE PROJECT


def create_project(request):

    if not _role(request, "admin"):
        return redirect("login")

    managers = RegisterModel.objects.filter(role="manager")
    

    if request.method == "POST":

        project_name = request.POST.get("project_name")
        description = request.POST.get("description")
        manager_id = request.POST.get("manager")
        deadline = request.POST.get("deadline")

        manager = get_object_or_404(RegisterModel, id=manager_id, role="manager")
        admin = get_object_or_404(RegisterModel, id=_user_id(request), role="admin")

        Project.objects.create(
            project_name=project_name,
            description=description,
            manager=manager,
            admin=admin,
            repository_link=request.POST.get("repository_link"),
            deadline=deadline
        )

        return redirect("admin_dashboard")

    return render(request, "create_project.html", {
        "managers": managers
    })



# UPDATE PROJECT


def update_project(request, id):

    if not _role(request, "admin"):
        return redirect("login")

    project = get_object_or_404(Project, id=id)
    managers = RegisterModel.objects.filter(role="manager")

    if request.method == "POST":

        project.project_name = request.POST.get("project_name")
        project.description = request.POST.get("description")

        manager_id = request.POST.get("manager")
        project.manager = get_object_or_404(RegisterModel, id=manager_id, role="manager")

        project.deadline = request.POST.get("deadline")

        project.save()

        return redirect("admin_dashboard")

    return render(request, "update_project.html", {
        "project": project,
        "managers": managers
    })



# DELETE PROJECT


def delete_project(request, id):

    if not _role(request, "admin") or request.method != "POST":
        return redirect("login")

    project = get_object_or_404(Project, id=id)
    project.delete()

    return redirect("admin_dashboard")



# MANAGER DASHBOARD


def manager_dashboard(request):

    if not _role(request, "manager"):
        return redirect("login")

    manager_id = _user_id(request)

    # Existing code (keep it)
    teams = Team.objects.filter(project__manager_id=manager_id)

    # Add assigned bugs for manager projects
    bugs = Bug.objects.filter(project__manager_id=manager_id)

    active_bugs = bugs.exclude(status="Closed").count()

    closed_bugs = bugs.filter(status="Closed").count()

    return render(request, "manager_dashboard.html", {
        "teams": teams,
        "bugs": bugs,
        'active_bugs':active_bugs,
        'closed_bugs':closed_bugs
    })



# CREATE TEAM



def create_team(request):

    if not _role(request, "manager"):
        return redirect("login")

    manager_id = _user_id(request)

    # Projects created by this manager
    projects = Project.objects.filter(manager_id=manager_id)

    # Get developers and testers for selection
    developers = RegisterModel.objects.filter(role__iexact="developer")
    testers = RegisterModel.objects.filter(role__iexact="tester")

    if request.method == "POST":

        team_name = request.POST.get("team_name")
        project_id = request.POST.get("project")

        developer_ids = request.POST.getlist("developers")
        tester_ids = request.POST.getlist("testers")

        project = get_object_or_404(
            Project,
            id=project_id,
            manager_id=manager_id,
        )

        # Create Team
        team = Team.objects.create(
            team_name=team_name,
            project=project
        )

        # Add Developers to Team
        valid_developers = RegisterModel.objects.filter(
            id__in=developer_ids,
            role__iexact="developer",
        )
        for developer in valid_developers:
            TeamMember.objects.create(
                user=developer,
                team=team,
                role="Developer"
            )

        # Add Testers to Team
        valid_testers = RegisterModel.objects.filter(
            id__in=tester_ids,
            role__iexact="tester",
        )
        for tester in valid_testers:
            TeamMember.objects.create(
                user=tester,
                team=team,
                role="Tester"
            )

        return redirect("manager_dashboard")

    return render(request, "create_team.html", {
        "projects": projects,
        "developers": developers,
        "testers": testers
    })

# UPDATE TEAM



def update_team(request, team_id):
    if not _role(request, "manager"):
        return redirect("login")

    manager_id = _user_id(request)
    team = get_object_or_404(Team, id=team_id, project__manager_id=manager_id)

    projects = Project.objects.filter(manager_id=manager_id)
    developers = RegisterModel.objects.filter(role__iexact="Developer")
    testers = RegisterModel.objects.filter(role__iexact="Tester")

    # Preselected IDs for template
    selected_devs = list(team.teammember_set.filter(role="Developer").values_list("user_id", flat=True))
    selected_testers = list(team.teammember_set.filter(role="Tester").values_list("user_id", flat=True))

    if request.method == "POST":
        team_name = request.POST.get("team_name")
        project_id = request.POST.get("project")
        developer_ids = request.POST.getlist("developers")
        tester_ids = request.POST.getlist("testers")

        team.team_name = team_name
        team.project = get_object_or_404(
            Project,
            id=project_id,
            manager_id=manager_id,
        )
        team.save()

        TeamMember.objects.filter(team=team).delete()

        for dev_id in developer_ids:
            developer = get_object_or_404(
                RegisterModel, id=dev_id, role__iexact="developer"
            )
            TeamMember.objects.create(
                user=developer, team=team, role="Developer"
            )

        for tester_id in tester_ids:
            tester = get_object_or_404(
                RegisterModel, id=tester_id, role__iexact="tester"
            )
            TeamMember.objects.create(user=tester, team=team, role="Tester")

        return redirect("manager_dashboard")

    return render(request, "update_team.html", {
        "team": team,
        "projects": projects,
        "developers": developers,
        "testers": testers,
        "selected_devs": selected_devs,
        "selected_testers": selected_testers
    })


# DELETE TEAM


def delete_team(request, id):

    if not _role(request, "manager") or request.method != "POST":
        return redirect("login")

    team = get_object_or_404(
        Team, id=id, project__manager_id=_user_id(request)
    )
    team.delete()

    return redirect("manager_dashboard")






# TESTER DASHBOARD


def tester_dashboard(request):

    if not _role(request, "tester"):
        return redirect("login")

    user_id = _user_id(request)

    bugs = Bug.objects.filter(created_by_id=user_id)

    return render(request, "tester_dashboard.html", {
        "bugs": bugs
    })


# CREATE BUG TICKET

def create_bug(request):

    user_id = _user_id(request)
    if not user_id or not _role(request, "tester"):
        return redirect('login')

    projects = Project.objects.filter(team__teammember__user_id=user_id).distinct()

    if request.method == "POST":
        project_id = request.POST.get('project_id')
        project_url = request.POST.get('project_url')
        title = request.POST.get('title')
        description = request.POST.get('description')
        priority = request.POST.get('priority')
        expected_result = request.POST.get('expected_result')
        actual_result = request.POST.get('actual_result')
        screenshot =  request.FILES.get('screenshot')

        project = get_object_or_404(
            projects.select_related("manager"),
            id=project_id,
        )
        tester = get_object_or_404(RegisterModel, id=user_id, role="tester")
        manager = project.manager

        team_member = TeamMember.objects.filter(user=tester, team__project=project).first()
        team = team_member.team if team_member else None


        bug = Bug.objects.create(
            project = project,
            project_url = project_url,
            title=title,
            description=description,
            status="Open",
            team=team,
            priority = priority,
            created_by=tester,
            manager = manager,
            expected_result = expected_result,
            actual_result = actual_result,
            screenshot = screenshot,
        )

        create_bug_history(bug, "Open", user_id, "Bug reported")

        messages.success(request,'Bug Ticket Created Successfully..!')
        return redirect('tester_dashboard')
    
    return render(request, 'create_bug.html', {'projects':projects})





# MANAGER BUG VIEW LIST

def manager_bug_list(request):

    if not _role(request, "manager"):
        return redirect('login')

    bug_details = _manager_bug_queryset(request)
    return render(request, 'bug_list.html', {'bug_details':bug_details})



# MANAGER ASSIGN BUG TO DEVELOPER

def assign_developer(request):

    if not _role(request, "manager"):
        return redirect('login')

    bugs = _manager_bug_queryset(request).filter(status__in=["Open", "Assigned"])
    developers = RegisterModel.objects.filter(
        role='developer',
        teammember__team__project__manager_id=_user_id(request),
    ).distinct()

    if request.method == 'POST':
        developer_id = request.POST.get("developer_name")
        bug_id = request.POST.get("bug_name")
        priority = request.POST.get("priority")

        bug = get_object_or_404(bugs, id=bug_id)
        developer = get_object_or_404(
            developers,
            id=developer_id,
            teammember__team=bug.team,
        )

        # Assign developer and update bug
        bug.assigned_to = developer
        bug.status = "Assigned"
        if priority in dict(Bug.PRIORITY_CHOICES):
            bug.priority = priority
        bug.save()
        create_bug_history(bug, "Assigned", _user_id(request), "Developer assigned")

        return redirect("manager_dashboard")

    return render(request, 'assign_developer.html', {
        'developers': developers,
        'bugs': bugs
    })

# UPDATE ASSIGN DEVELOPER

def update_assign_developer(request, bug_id):

    if not _role(request, "manager"):
        return redirect('login')

    bug = get_object_or_404(_manager_bug_queryset(request), id=bug_id)
    developers = RegisterModel.objects.filter(
        role='developer',
        teammember__team__project=bug.project,
    ).distinct()

    if request.method == 'POST':

        developer_id = request.POST.get("developer_name")
        title = request.POST.get("title")
        priority = request.POST.get("priority")

        developer = get_object_or_404(
            developers,
            id=developer_id,
            teammember__team=bug.team,
        )

        bug.assigned_to = developer
        bug.title = title
        if priority in dict(Bug.PRIORITY_CHOICES):
            bug.priority = priority
        bug.save()

        return redirect('manager_dashboard')

    return render(request, 'update_assign_developer.html',
                  {'bug': bug, 'developers': developers})



#  DELETE ASSIGN DEVELOPER

def delete_assign_developer(request, bug_id):

    if not _role(request, "manager") or request.method != "POST":
        return redirect("login")

    bug = get_object_or_404(_manager_bug_queryset(request), id=bug_id)

    bug.delete()

    return redirect('manager_dashboard')



# DEVELOPER DASHBOARD


def developer_dashboard(request):

    if not _role(request, "developer"):
        return redirect("login")

    user_id = _user_id(request)

    bugs = Bug.objects.filter(assigned_to_id=user_id)

    return render(request, "developer_dashboard.html", {
        "bugs": bugs
    })



# DEVELOPER BUG DETAILS 
def developer_bug_details(request, bug_id):

    if not _role(request, "developer"):
        return redirect('login')

    bug = get_object_or_404(
        Bug, id=bug_id, assigned_to_id=_user_id(request)
    )

    return render(request, 'developer_bug_details.html', {'bug': bug})


#  Helper Function
def create_bug_history(bug, status, user_id, comment=None):
    BugHistory.objects.create(
        bug=bug,
        status=status,
        changed_by_id=user_id,
        comment=comment
    )



def start_bug(request, bug_id):

    if not _role(request, "developer") or request.method != "POST":
        return redirect("login")

    bug = get_object_or_404(
        Bug,
        id=bug_id,
        assigned_to_id=_user_id(request),
        status="Assigned",
    )

    bug.status = "In Progress"
    bug.save()

    create_bug_history(
        bug,
        "In Progress",
        _user_id(request),
        "Developer started working"
    )


    return redirect("developer_dashboard")


def resolve_bug(request, bug_id):

    if not _role(request, "developer") or request.method != "POST":
        return redirect("login")

    bug = get_object_or_404(
        Bug,
        id=bug_id,
        assigned_to_id=_user_id(request),
        status="In Progress",
    )

    bug.status = "Resolved"
    bug.save()

    create_bug_history(
        bug,
        "Resolved",
        _user_id(request),
        "Bug resolved by developer"
    )


    return redirect("developer_dashboard")





def tester_verify_bug(request, bug_id):

    if not _role(request, "tester") or request.method != "POST":
        return redirect("login")

    bug = get_object_or_404(
        Bug,
        id=bug_id,
        created_by_id=_user_id(request),
        status="Resolved",
    )

    bug.status = "Verified"
    bug.save()

    create_bug_history(
        bug,
        "Verified",
        _user_id(request),
        "tester Verified the Fix"
    )


    return redirect("tester_dashboard")


def close_bug(request, bug_id):

    if not _role(request, "manager") or request.method != "POST":
        return redirect("login")

    bug = get_object_or_404(
        _manager_bug_queryset(request), id=bug_id, status="Verified"
    )

    bug.status = "Closed"
    bug.save()

    create_bug_history(
        bug,
        "Closed",
        _user_id(request),
        "Manager closed the Bug"
    )


    return redirect("manager_dashboard")


def show_bughistory(request, bug_id):

    if not request.user.is_authenticated:
        return redirect('login')

    bug = get_object_or_404(_visible_bug_queryset(request), id=bug_id)
    histories = BugHistory.objects.filter(bug=bug).order_by("created_at")

    return render(request, "show_bughistory.html", {
        'histories': histories
    })


def bug_details(request, bug_id):

    if not request.user.is_authenticated:
        return redirect("login")

    bug = get_object_or_404(_visible_bug_queryset(request), id=bug_id)

    comments = BugComment.objects.filter(bug=bug).order_by("-created_at")

    return render(request, "bug_details.html", {
        "bug": bug,
        "comments": comments
    })


def add_comment(request, bug_id):

    if not request.user.is_authenticated:
        return redirect("login")

    bug = get_object_or_404(_visible_bug_queryset(request), id=bug_id)

    if request.method == "POST":

        message = request.POST.get("message")

        if message:
            BugComment.objects.create(
                bug=bug,
                user_id=_user_id(request),
                message=message
            )

    return redirect("bug_details", bug_id=bug_id)


def all_view_histories(request):

    if not request.user.is_authenticated:
        return redirect('login')

    bugs = _visible_bug_queryset(request)
    
    return render(request,'all_view_histories.html', {'bugs':bugs})