from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('', views.home, name="home"),
    path('register/', views.register, name="register"),
    path('login/', views.login, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.log_out, name='logout'),

    # Project URLs (Admin)
    path('create-project/', views.create_project, name='create_project'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('update_project/<int:id>/', views.update_project, name='update_project'),
    path('delete_project/<int:id>/', views.delete_project, name='delete_project'),

    # Team URLs (Manager)
    path('create_team/', views.create_team, name='create_team'),
    path('manager_dashboard/', views.manager_dashboard, name='manager_dashboard'),
    path('update_team/<int:team_id>/', views.update_team, name='update_team'),
    path('delete_team/<int:id>/', views.delete_team, name='delete_team'),


    
     # Developer URLs
    path('developer_dashboard/', views.developer_dashboard, name='developer_dashboard'),
   
    # Tester URLs
    path('tester_dashboard/', views.tester_dashboard, name='tester_dashboard'),

    path('create-bug/', views.create_bug, name='create_bug'),

    path('manager-bug-list/', views.manager_bug_list, name='manager_bug_list'),

    path('assign_developer', views.assign_developer, name='assign_developer'),

    path("developer-bug-details/<int:bug_id>/", views.developer_bug_details, name="developer_bug_details"),

    path('update-assign/<int:bug_id>/', views.update_assign_developer, name='update_assign_developer'),

    path('delete-assign/<int:bug_id>/', views.delete_assign_developer, name='delete_assign_developer'),

    path("start-bug/<int:bug_id>/", views.start_bug, name="start_bug"),

    path("resolve-bug/<int:bug_id>/", views.resolve_bug, name="resolve_bug"),

    path("tester-verify/<int:bug_id>/",views.tester_verify_bug,name="tester_verify"),

    path("close-bug/<int:bug_id>/",views.close_bug,name="close_bug"),

    path('bug-history/<int:bug_id>/', views.show_bughistory, name='bug_history'),

    path("bug/<int:bug_id>/", views.bug_details, name="bug_details"),

    path("bug/<int:bug_id>/add-comment/", views.add_comment, name="add_comment"),

    path('History - Disscussion/', views.all_view_histories, name='history-discussion')

    

]

   
