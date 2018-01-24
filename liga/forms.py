from django import forms


# action: post request to create_player
class JoinTournamentForm(forms.Form):
    tournament_name = ''
    hidden_tournament_id_field = forms.IntegerField(
        label="Pretend you've never seen this ;)",
        widget=forms.HiddenInput
    )

    def set_data(self, tournament):
        self.tournament_name = tournament.game_name
        self.fields['hidden_tournament_id_field'].initial = tournament.id
        return self


# action: post request to create_team/:tournament_id
class CreateTeamForm(forms.Form):
    team_name = forms.CharField(label='Team name')
    is_public = forms.BooleanField(label='Publicly visible')
    hidden_tournament_id_field = forms.IntegerField(
        label="Pretend you've never seen this ;)",
        widget=forms.HiddenInput
    )

    def set_data(self, tournament):
        self.fields['hidden_tournament_id_field'].initial = tournament.id
        return self


# action: post request to invite_player_to_team
class CreatePlayerInviteForm(forms.Form):
    player_name = ''

    hidden_team_id_field = forms.IntegerField(
        label="Pretend you've never seen this ;)",
        widget=forms.HiddenInput,
    )
    hidden_player_id_field = forms.IntegerField(
        label="Pretend you've never seen this ;)",
        widget=forms.HiddenInput,
    )

    def set_data(self, team, player):
        self.player_name = player.user.name
        self.fields['hidden_player_id_field'].initial = player.id
        self.fields['hidden_team_id_field'].initial = team.id
        return self


# action: post request to request_team
class CreateTeamRequestForm(forms.Form):
    team_name = ''

    hidden_team_id_field = forms.IntegerField(
        label="Pretend you've never seen this ;)",
        widget=forms.HiddenInput,
    )
    hidden_player_id_field = forms.IntegerField(
        label="Pretend you've never seen this ;)",
        widget=forms.HiddenInput,
    )

    def set_data(self, team, player):
        self.team_name = team.name
        self.fields['hidden_player_id_field'].initial = player.id
        self.fields['hidden_team_id_field'].initial = team.id
        return self

# # https://docs.djangoproject.com/en/2.0/ref/forms/api/#dynamic-initial-values
# class ManagePlayerInviteForm(forms.Form):
#     accept_invite_field = forms.TypedChoiceField(
#         empty_value=False,
#         label='DATA NOT SET !!!',
#         coerce=lambda x: x == 'True',
#         choices=((False, 'No'), (True, 'Yes')),
#         widget=forms.RadioSelect
#     )
#
#     def set_data(self, team_name):
#         self.accept_invite_field.label = "Do You want to join {}?".format(team_name)
#
#
# class ManageTeamRequestForm(forms.Form):
#     accept_request_field = forms.TypedChoiceField(
#         empty_value=False,
#         label='DATA NOT SET !!!',
#         coerce=lambda x: x == 'True',
#         choices=((False, 'No'), (True, 'Yes')),
#         widget=forms.RadioSelect
#     )
#
#     def set_data(self, player_name):
#         self.accept_invite_field.label = "Do You want to add {} to Your team?".format(player_name)
#
# class CreateMatchForm(forms.Form):
#     # TODO
#
# class CreateScorePropositionForm(forms.Form):
#     # TODO
