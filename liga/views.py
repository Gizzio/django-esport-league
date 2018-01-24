from datetime import datetime, date, timezone

from django.http import HttpResponseNotFound
from django.shortcuts import render, get_object_or_404, redirect

from liga.forms import JoinTournamentForm, CreateTeamForm, CreatePlayerInviteForm, CreateTeamRequestForm
from liga.models import Tournament, Team, TeamRequest, PlayerInvite, Match, Player, User


# Create your views here.


# noinspection SpellCheckingInspection
def index(request):
    user_id = 1  # TODO: require sign in user
    user = User.objects.get(id=user_id)

    playable_tournaments = user.playable_tournaments.all()
    joinable_tournaments = user.joinable_tournaments.all()
    joinable_tournament_forms = [JoinTournamentForm().set_data(t) for t in joinable_tournaments]

    context = {
        'playable_tournaments': playable_tournaments,
        'joinable_tournament_forms': joinable_tournament_forms,
    }
    return render(request, 'liga/index.html', context)


def tournament(request, tournament_id):
    user_id = 1  # TODO: require sign in user
    user = User.objects.get(id=user_id)

    current_tournament = get_object_or_404(Tournament, id=tournament_id)
    print(current_tournament)
    player = get_object_or_404(Player, tournament_id=tournament_id, user_id=user_id)
    has_team = player.team is not None

    before_season = datetime.now(timezone.utc) < current_tournament.season_start

    if before_season:
        start_date = current_tournament.season_start
        if has_team:
            team_requests = TeamRequest.objects.filter(team=player.team).all()
            free_players = current_tournament.players.filter(team=None).all()
            free_player_forms = [CreatePlayerInviteForm().set_data(player.team, fp) for fp in free_players]
            context = {
                'tournament': current_tournament,
                'has_team': has_team,
                'team': player.team,
                'team_players': player.team.players.all(),
                'team_players_count': player.team.players.count(),
                'team_requests': team_requests,
                'free_players_invite_forms': free_player_forms,
                'start_date': start_date,
            }
        else:
            public_teams = current_tournament.teams.filter(is_public=True).all()
            public_team_forms = [CreateTeamRequestForm().set_data(pt, player) for pt in public_teams]
            player_invites = PlayerInvite.objects.filter(player=player).all()
            create_team_form = CreateTeamForm().set_data(current_tournament)
            context = {
                'tournament': current_tournament,
                'has_team': has_team,
                'create_team_form': create_team_form,
                'public_teams_request_forms': public_team_forms,
                'player_invites': player_invites,
            }
        return render(request, 'liga/tournament_before_season.html', context)

    else:
        # during season
        teams = current_tournament.teams.all()  # TODO: .order_by(score)
        context = {
            'tournament': current_tournament,
            'has_team': has_team,
            'player_team': player.team,
            'teams': teams,
        }
        return render(request, 'liga/tournament_during_season.html', context)


def team(request, tournament_id, team_id):
    user_id = 1  # TODO: require sign in user
    user = User.objects.get(id=user_id)

    current_tournament = get_object_or_404(Tournament, id=tournament_id)
    current_team = get_object_or_404(Team, id=team_id, tournament_id=tournament_id)
    player = get_object_or_404(Player, user_id=user_id, team_id=team_id)

    season_ended = current_tournament.season_end < datetime.now(timezone.utc)
    if season_ended:
        return redirect('tournaments', tournament_id=current_tournament.id)

    else:
        possible_opponents = current_team.possible_oponenets()
        played_matches = current_team.matches.order_by()

        pending_matches = None
        played_matches = None
        possible_opponents = None

        context = {
            'team_members': current_team.players,
            'pending_matches': pending_matches,
            'match_history': played_matches,
            'possible_opponents': possible_opponents
        }
        return render(request, 'liga/team.html', context)


def match(request, tournament_id, match_id):
    user_id = 1  # TODO: get from session

    current_tournament = get_object_or_404(Tournament, id=tournament_id)
    current_match = get_object_or_404(Match, id=match_id)
    player = get_object_or_404(Player, tournament_id=tournament_id, user_id=user_id)
    current_team = player.team
    if current_team is None:
        return HttpResponseNotFound()
    player = match.inviting_team.player_set.filter(user=user) | match.guest_team.player_set.filter(user=user)
    if player.count() == 0:
        return HttpResponseNotFound()  # TODO: Not sure if get_or_404 works with quryse unions so I left this
    context = {
        'match': match
    }
    return render(request, 'liga/match.html', context)


def create_player(request):
    user_id = 1  # TODO: get from session
    if request.method != 'POST':
        return HttpResponseNotFound()

    form = JoinTournamentForm(request.POST)
    if form.is_valid():
        player, created = Player.objects.get_or_create(
            tournament_id=form.cleaned_data['hidden_tournament_id_field'],
            user_id=user_id,
        )
        if created:
            print('CREATED:', player)
        else:
            print('WARNING:', 'new player already in tournament')
        return redirect('tournament', tournament_id=player.tournament_id)

    else:
        # invalid form
        print('ERROR: form error')
        print(form.errors)
        return HttpResponseNotFound()


def create_team(request, tournament_id):
    user_id = 1  # TODO: get from session
    if request.method != 'POST':
        return HttpResponseNotFound()

    player = get_object_or_404(Player, user_id=user_id, tournament_id=tournament_id)

    form = CreateTeamForm(request.POST)
    if form.is_valid():
        new_team, created = Team.objects.get_or_create(
            tournament_id=tournament_id,
            name=form.cleaned_data['team_name'],
            is_public=form.cleaned_data['is_public']
        )
        if created:
            print('CREATED:', new_team)
            player.team_id = new_team.id
            player.save()

            return redirect('tournament', tournament_id=player.tournament_id)
        else:
            print('WARNING:', 'unable to create new team')
            # TODO: Notify user about failure (probably team name was already used)
            return redirect('tournament', tournament_id=player.tournament_id)
    else:
        # invalid form
        print('ERROR: form error')
        print(form.errors)
        return redirect('tournament', tournament_id=tournament_id)


def create_player_invite(request, tournament_id):
    user_id = 1  # TODO: get from session
    if request.method != 'POST':
        return HttpResponseNotFound()

    sending_player = get_object_or_404(Player, user_id=user_id, tournament_id=tournament_id)

    form = CreatePlayerInviteForm(request.POST)
    if form.is_valid():
        form_team_id = form.cleaned_data['hidden_team_id_field']

        if form_team_id != sending_player.team_id:
            return HttpResponseNotFound()

        current_team = get_object_or_404(Team, id=form_team_id)
        if current_team is None or current_team.tournament.season_start < datetime.now(timezone.utc):
            # no team or tournament already started
            return HttpResponseNotFound()

        invited_player = get_object_or_404(Player,
                                           id=form.cleaned_data['hidden_player_id_field'],
                                           tournament_id=current_team.tournament_id)
        if invited_player.team is not None:
            return HttpResponseNotFound()

        # assuming invites expire at the time of tournament start
        invite, created = PlayerInvite.objects.get_or_create(player=invited_player,
                                                             team=current_team,
                                                             expire_date=current_team.tournament.season_start.date())
        if created:
            print('CREATED:', invite)
            return redirect('tournament', tournament_id=tournament_id)
        else:
            print('WARNING:', 'unable to create new team')
            # TODO: Notify user about failure (invite already existed) -- or tournament started? check
            return redirect('tournament', tournament_id=tournament_id)

    else:
        # invalid form
        print('ERROR: form error')
        print(form.errors)
        return redirect('tournament', tournament_id=tournament_id)


def create_team_requst(request, tournament_id):
    user_id = 1  # TODO: get from session
    if request.method != 'POST':
        return HttpResponseNotFound()

    sending_player = get_object_or_404(Player, user_id=user_id, tournament_id=tournament_id)

    form = CreateTeamRequestForm(request.POST)
    if form.is_valid():
        form_team_id = form.cleaned_data['hidden_team_id_field']
        form_team = get_object_or_404(Team, id=form_team_id, tournament_id=tournament_id, is_public=True)

        if form_team is None or form_team.tournament.season_start < datetime.now(timezone.utc):
            # no team or tournament already started
            return HttpResponseNotFound()

        # assuming team requests expire at the time of tournament start
        team_request, created = TeamRequest.objects.get_or_create(player=sending_player,
                                                                  team=form_team,
                                                                  expire_date=form_team.tournament.season_start.date())
        if created:
            print('CREATED:', team_request)
            return redirect('tournament', tournament_id=tournament_id)
        else:
            print('WARNING:', 'unable to create new team')
            # TODO: Notify user about failure (invite already existed) -- or tournament started? check
            return redirect('tournament', tournament_id=tournament_id)

    else:
        # invalid form
        print('ERROR: form error')
        print(form.errors)
        return redirect('tournament', tournament_id=tournament_id)


# TODO actions (handling POST request):
# log in
# log out (user)
# request team (tournament, team, player, user)
# accept player invitation (tournament, team, player, user, playerinvite)
# accept team request (tournament, team, player, user, teamrequest)
# reject team request (tournament, team, player, user, teamrequest)
# create match (tournament, team, opponent team, user)
# create score proposition (tournament, match, user)
