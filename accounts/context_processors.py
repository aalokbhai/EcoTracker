from .roles import COLLECTOR, OFFICER, CITIZEN, get_role


def roles(request):
    role = get_role(request.user)
    return {
        'user_role': role,
        'is_officer': role == OFFICER,
        'is_collector': role == COLLECTOR,
        'is_citizen': role == CITIZEN,
    }
